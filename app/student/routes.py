from flask import render_template, url_for, flash, redirect
from app.student import student
from app.models import Student, Subject, Session, Attendance
from flask_login import login_required, current_user

@student.route("/student/dashboard")
@login_required
def dashboard():
    if current_user.role != 'student':
        return redirect(url_for('main.home'))
        
    student_profile = current_user.student_profile
    if not student_profile:
        flash("Student profile not found.", "danger")
        return redirect(url_for('main.home'))
        
    # Get all subjects for student's class
    subjects = Subject.query.filter_by(class_name=student_profile.class_name).all()
    
    attendance_data = []
    total_sessions_all = 0
    total_attended_all = 0
    
    for subject in subjects:
        # Count total ACTIVE or COMPLETED sessions for this subject
        sessions = Session.query.filter_by(subject_id=subject.id).all()
        session_ids = [s.id for s in sessions]
        total_sessions = len(sessions)
        
        # Count attendance records for this student in those sessions
        if total_sessions > 0:
            attended = Attendance.query.filter(
                Attendance.session_id.in_(session_ids),
                Attendance.student_id == student_profile.id,
                Attendance.status == 'Present'
            ).count()
        else:
            attended = 0
            
        percent = round((attended / total_sessions * 100), 1) if total_sessions > 0 else 0
        
        attendance_data.append({
            'subject': subject.name,
            'class_name': subject.class_name,
            'total': total_sessions,
            'attended': attended,
            'percent': percent
        })
        
        total_sessions_all += total_sessions
        total_attended_all += attended
        
    overall_percent = round((total_attended_all / total_sessions_all * 100), 1) if total_sessions_all > 0 else 0
    
    return render_template('student/dashboard.html', 
                          attendance_data=attendance_data,
                          overall_percent=overall_percent)

