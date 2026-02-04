from flask import render_template, url_for, flash, redirect, request, jsonify
from app import db, bcrypt
from app.admin import admin
from app.admin.forms import RegistrationForm, EditUserForm
from app.models import User, Student, Faculty, FaceData
from flask_login import login_required, current_user

@admin.route("/admin/dashboard")
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access Denied', 'danger')
        return redirect(url_for('main.home'))
        
    student_count = Student.query.count()
    faculty_count = Faculty.query.count()
    face_count = FaceData.query.count()
    
    # Chart Data: Last 7 Days Attendance
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app.models import Session, Attendance 

    dates = []
    counts = []
    
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        dates.append(date.strftime('%b %d'))
        
        # Count attendance for this date
        # Join Session to filter by date
        count = Attendance.query.join(Session).filter(Session.date == date).count()
        counts.append(count)
    
    return render_template('admin/dashboard.html', 
                          student_count=student_count, 
                          faculty_count=faculty_count,
                          face_count=face_count,
                          chart_labels=dates,
                          chart_data=counts)

@admin.route("/admin/manage_users")
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin/manage_users.html', users=users)

@admin.route("/admin/edit_user/<int:user_id>", methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
        
    user = User.query.get_or_404(user_id)
    form = EditUserForm(original_email=user.email)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        
        if user.role == 'student' and user.student_profile:
            user.student_profile.roll_no = form.roll_no.data
            user.student_profile.class_name = form.class_name.data
            user.student_profile.department = form.student_dept.data
            
        elif user.role == 'faculty' and user.faculty_profile:
            user.faculty_profile.department = form.faculty_dept.data
            
        db.session.commit()
        flash(f'User {user.name} has been updated!', 'success')
        return redirect(url_for('admin.manage_users'))
        
    elif request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        
        if user.role == 'student' and user.student_profile:
            form.roll_no.data = user.student_profile.roll_no
            form.class_name.data = user.student_profile.class_name
            form.student_dept.data = user.student_profile.department
            
        elif user.role == 'faculty' and user.faculty_profile:
            form.faculty_dept.data = user.faculty_profile.department
            
    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin.route("/admin/register_user", methods=['GET', 'POST'])
@login_required
def register_user():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, email=form.email.data, password_hash=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        
        if form.role.data == 'student':
            student = Student(
                user_id=user.id, 
                roll_no=form.roll_no.data, 
                class_name=form.class_name.data, 
                department=form.student_dept.data
            )
            db.session.add(student)
        elif form.role.data == 'faculty':
            faculty = Faculty(
                user_id=user.id, 
                department=form.faculty_dept.data
            )
            db.session.add(faculty)
            
        db.session.commit()
        flash(f'Account created for {form.name.data}!', 'success')
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/register_user.html', title='Register User', form=form)

@admin.route("/admin/register_face_selection")
@login_required
def register_face_selection():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    students = Student.query.all()
    return render_template('admin/select_student_face.html', students=students)

@admin.route("/admin/register_face_capture/<int:student_id>")
@login_required
def register_face_capture(student_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    student = Student.query.get_or_404(student_id)
    return render_template('admin/register_face.html', student=student)

@admin.route("/admin/upload_face", methods=['POST'])
@login_required
def upload_face():
    if current_user.role != 'admin':
        return {'success': False, 'message': 'Unauthorized'}, 403
    
    try:
        data = request.get_json()
        if not data or 'image' not in data or 'student_id' not in data:
            return {'success': False, 'message': 'Invalid data'}, 400
            
        from app.utils import save_base64_image, generate_embedding
        import traceback
        
        student_id = data['student_id']
        image_data = data['image']
        
        # 1. Save Image
        filepath = save_base64_image(image_data, student_id)
        if not filepath:
            print("ERROR: save_base64_image returned None")
            return {'success': False, 'message': 'Failed to save image file'}, 500
            
        # 2. Generate Embedding
        print(f"DEBUG: Calling generate_embedding for {filepath}")
        embedding = generate_embedding(filepath)
        if not embedding:
            print("ERROR: generate_embedding returned None")
            return {'success': False, 'message': 'No face detected! Please ensure better lighting.'}, 400
            
        # 3. Save to DB
        print(f"DEBUG: Saving to DB for student {student_id}")
        face_data = FaceData.query.filter_by(student_id=student_id).first()
        if not face_data:
            face_data = FaceData(student_id=student_id, image_path=filepath)
            db.session.add(face_data)
            
        face_data.set_embedding(embedding)
        face_data.image_path = filepath
        db.session.commit()
        print("DEBUG: DB Commit Successful")
        
        return {'success': True}
        
    except Exception as e:
        print(f"CRITICAL ERROR in upload_face: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Internal Server Error: {str(e)}'}), 500

@admin.route("/admin/create_subject", methods=['GET', 'POST'])
@login_required
def create_subject():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    
    from app.admin.forms import SubjectForm
    from app.models import Subject
    
    form = SubjectForm()
    # Populate Faculty Choices
    faculty_list = Faculty.query.join(User).all()
    form.faculty_id.choices = [(f.id, f"{f.user.name} ({f.department})") for f in faculty_list]
    
    if form.validate_on_submit():
        subject = Subject(
            name=form.name.data,
            code=form.code.data,
            class_name=form.class_name.data,
            faculty_id=form.faculty_id.data
        )
        db.session.add(subject)
        db.session.commit()
        flash(f'Subject "{form.name.data}" created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/create_subject.html', title='Create Subject', form=form)

    return render_template('admin/create_subject.html', title='Create Subject', form=form)

@admin.route("/admin/delete_user/<int:user_id>", methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
        
    user = User.query.get_or_404(user_id)
    
    # 1. Prevent Self Deletion
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for('admin.manage_users'))

    # 2. Check Faculty Subjects
    if user.role == "faculty" and user.faculty_profile:
        if user.faculty_profile.subjects:
            flash(f"Cannot delete faculty {user.name}. They are assigned to {len(user.faculty_profile.subjects)} subjects. Please reassign the subjects first.", "warning")
            return redirect(url_for('admin.manage_users'))

    # 3. Handle Student Attendance Records (Manual Cleanup)
    if user.role == "student" and user.student_profile:
        from app.models import Attendance
        # Delete related attendance records manually
        Attendance.query.filter_by(student_id=user.student_profile.id).delete()
        
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.name} has been deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "danger")
        
    return redirect(url_for('admin.manage_users'))

@admin.route("/admin/password_requests")
@login_required
def password_requests():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
        
    from app.models import PasswordResetRequest
    # Get all pending requests
    requests = PasswordResetRequest.query.filter_by(status='Pending').order_by(PasswordResetRequest.timestamp.desc()).all()
    return render_template('admin/password_requests.html', requests=requests)

@admin.route("/admin/password_requests/approve/<int:req_id>")
@login_required
def approve_password_request(req_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
        
    from app.models import PasswordResetRequest
    req = PasswordResetRequest.query.get_or_404(req_id)
    req.status = 'Approved'
    db.session.commit()
    flash(f"Password reset request for {req.email} has been APPROVED.", "success")
    return redirect(url_for('admin.password_requests'))

@admin.route("/admin/password_requests/reject/<int:req_id>")
@login_required
def reject_password_request(req_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
        
    from app.models import PasswordResetRequest
    req = PasswordResetRequest.query.get_or_404(req_id)
    db.session.delete(req)
    db.session.commit()
    flash(f"Password reset request for {req.email} has been REJECTED/DELETED.", "info")
    return redirect(url_for('admin.password_requests'))

