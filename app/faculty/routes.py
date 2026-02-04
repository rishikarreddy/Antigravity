from flask import render_template, url_for, flash, redirect, request, jsonify
from app import db
from app.faculty import faculty
from app.models import Subject, Session, Student, FaceData, Attendance
from flask_login import login_required, current_user
from datetime import datetime
import base64
import cv2
import numpy as np
import os
# from deepface import DeepFace # Lazy load
from flask import current_app

@faculty.route("/faculty/dashboard")
@login_required
def dashboard():
    if current_user.role != 'faculty':
        return redirect(url_for('main.home'))
    
    # Get subjects assigned to this faculty's ID
    subjects = Subject.query.filter_by(faculty_id=current_user.faculty_profile.id).all()
    return render_template('faculty/dashboard.html', subjects=subjects)

@faculty.route("/faculty/start_session/<int:subject_id>", methods=['POST'])
@login_required
def start_session(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject.faculty_id != current_user.faculty_profile.id:
        return "Unauthorized", 403
        
    session = Session(subject_id=subject.id, date=datetime.utcnow().date())
    db.session.add(session)
    db.session.commit()
    
    return redirect(url_for('faculty.attendance_session', session_id=session.id))

@faculty.route("/faculty/session/<int:session_id>")
@login_required
def attendance_session(session_id):
    session = Session.query.get_or_404(session_id)
    # Security check: ensure session belongs to a subject owned by this faculty
    if session.subject.faculty_id != current_user.faculty_profile.id:
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('faculty.dashboard'))
        
    return render_template('faculty/session.html', session=session)

@faculty.route("/faculty/end_session/<int:session_id>")
@login_required
def end_session(session_id):
    session = Session.query.get_or_404(session_id)
    session.end_time = datetime.utcnow().time()
    session.is_active = False
    db.session.commit()
    flash('Session Ended. Attendance saved.', 'success')
    return redirect(url_for('faculty.dashboard'))

# GLOBAL CACHE for Embeddings
# Structure: { session_id: { 'embeddings': [list], 'map': { index: student_obj } } }
active_sessions_cache = {}

@faculty.route("/faculty/refresh_cache_manual/<int:session_id>", methods=['POST'])
@login_required
def refresh_cache_manual(session_id):
    print(f"DEBUG: Manual Cache Refresh for Session {session_id}")
    try:
        if session_id in active_sessions_cache:
            del active_sessions_cache[session_id]
        
        # Rebuild logic (could be helper function, but simple enough to repeat for now)
        students = Student.query.all()
        known_embeddings = []
        student_map = {}
        for i, student in enumerate(students):
            if student.face_data:
                emb = student.face_data.get_embedding()
                if emb:
                    known_embeddings.append(emb)
                    student_map[len(known_embeddings)-1] = student
        
        active_sessions_cache[session_id] = {
            'embeddings': known_embeddings,
            'map': student_map
        }
        return jsonify({'success': True, 'count': len(known_embeddings)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@faculty.route("/faculty/process_frame", methods=['POST'])
@login_required
def process_frame():
    from deepface import DeepFace
    data = request.get_json()
    image_data = data['image']
    session_id = data['session_id']
    
    session = Session.query.get(session_id)
    if not session or not session.is_active:
        return {'success': False, 'message': 'Session inactive'}, 400

    # 1. Decode Image
    try:
        header, encoded = image_data.split(",", 1)
        nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        return {'success': False, 'message': 'Image Decode Error'}, 400

    # 2. Get/Cache Embeddings
    current_student_count = Student.query.count()
    
    # Refresh cache if session missing OR student count changed (handling new registrations)
    should_refresh = False
    if session_id not in active_sessions_cache:
        should_refresh = True
    else:
        # Check if cache is stale
        cached_count = len(active_sessions_cache[session_id]['map'])
        if cached_count != current_student_count:
            print(f"DEBUG: Cache Stale! (Cached: {cached_count}, DB: {current_student_count}). Refreshing...")
            should_refresh = True

    if should_refresh:
        print(f"DEBUG: Building Cache for Session {session_id}")
        students = Student.query.all() 
        known_embeddings = []
        student_map = {}
        
        for i, student in enumerate(students):
            if student.face_data:
                # Ensure embedding is list
                emb = student.face_data.get_embedding()
                if emb:
                    known_embeddings.append(emb)
                    student_map[len(known_embeddings)-1] = student
        
        active_sessions_cache[session_id] = {
            'embeddings': known_embeddings,
            'map': student_map
        }
    
    # Retrieve from cache
    cache = active_sessions_cache[session_id]
    known_embeddings = cache['embeddings']
    student_map = cache['map']

    if not known_embeddings:
         return {'success': True, 'new_students': []} 

    # 3. Detect & Recognize (Optimized)
    newly_marked = []
    
    try:
        # threshold for Cosine with VGG-Face: 0.40 (Strict) -> 0.60 (Lenient)
        # Reverting to 0.65 (Yesterday's value) to ensure matches are found.
        threshold = 0.65
        
        # Use 'ssd' - Verified WORKING on TF 2.10.
        # This provides robust multi-face detection without the crashes of RetinaFace/MediaPipe.
        target_objs = DeepFace.represent(
            frame, 
            model_name="VGG-Face", 
            detector_backend="ssd", 
            enforce_detection=False,
            align=True
        )

        # Log how many faces found
        if isinstance(target_objs, list):
            print(f"DEBUG: SSD detected {len(target_objs)} face(s).")
        
        # Check if any faces detected
        if target_objs and isinstance(target_objs, list):
            
            detected_faces_list = []
            newly_marked = []
            attendance_buffer = []

            for i, face_obj in enumerate(target_objs):
                try:
                    target_embedding = face_obj.get("embedding")
                    facial_area = face_obj.get("facial_area", {})
                    
                    if not target_embedding:
                        continue

                    # ------------- RECOGNITION -------------
                    best_match_idx = -1
                    min_dist = 100
                    
                    # Cosine calc
                    target_vec = np.array(target_embedding)
                    norm_target = np.linalg.norm(target_vec)
                    
                    for idx, known_emb in enumerate(known_embeddings):
                        known_vec = np.array(known_emb)
                        norm_known = np.linalg.norm(known_vec)
                        
                        cosine_sim = np.dot(known_vec, target_vec) / (norm_known * norm_target)
                        cosine_dist = 1 - cosine_sim
                        
                        if cosine_dist < min_dist:
                            min_dist = cosine_dist
                            best_match_idx = idx
                    
                    # Log Top Matches for Debugging
                    # We can't easily sort without storing them all, so we just log the Best one clearly
                    # or strictly log if it was close.
                    
                    # ------------- MATCH LOGIC -------------
                    face_data = {
                        'box': facial_area,
                        'name': 'Unknown',
                        'match': False
                    }
                    
                    # Log the best match distance even if unknown
                    matched_name = student_map[best_match_idx].user.name if best_match_idx != -1 else "None"
                    print(f"FACE {i}: Best Dist={min_dist:.4f} to {matched_name} (Thresh={threshold})")
                    
                    # Diagnostic: If dist is high, print why
                    if min_dist >= threshold:
                        print("    -> UNKNOWN. Closest match was not good enough.")

                    if min_dist < threshold and best_match_idx != -1:
                        # Match Found
                        student = student_map[best_match_idx]
                        face_data['name'] = student.user.name
                        face_data['match'] = True
                        print(f"  -> Match: {student.user.name}")
                        
                        # Check DB (is already marked?)
                        # Optimization: Check buffer first to avoid double-add in same frame
                        in_buffer = any(a.student_id == student.id for a in attendance_buffer)
                        
                        if not in_buffer:
                            existing = Attendance.query.filter_by(student_id=student.id, session_id=session.id).first()
                            if not existing:
                                confidence_score = (1 - min_dist) * 100
                                new_attendance = Attendance(
                                    student_id=student.id, 
                                    session_id=session.id, 
                                    status='Present',
                                    confidence=confidence_score,
                                    recognition_time=0.5
                                )
                                attendance_buffer.append(new_attendance)
                                
                                newly_marked.append({
                                    'name': student.user.name,
                                    'roll_no': student.roll_no,
                                    'time': datetime.now().strftime("%H:%M:%S")
                                })
                            else:
                                print(f"  -> Already marked within session.")
                    
                    detected_faces_list.append(face_data)
                
                except Exception as loop_e:
                    print(f"Error processing face {i}: {loop_e}")
                    continue

            # ------------- BATCH COMMIT -------------
            if attendance_buffer:
                try:
                    db.session.add_all(attendance_buffer)
                    db.session.commit()
                    print(f"DEBUG: Committed {len(attendance_buffer)} new attendance records.")
                except Exception as db_e:
                    print(f"Database Commit Error: {db_e}")
                    db.session.rollback()

            return {'success': True, 'new_students': newly_marked, 'detected_faces': detected_faces_list}

    except Exception as e:
        print(f"Recognition Error: {e}")

    return {'success': True, 'new_students': newly_marked, 'detected_faces': []}

