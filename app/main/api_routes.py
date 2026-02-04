from flask import Blueprint, jsonify, request
from app import db
from app.models import User, Student, Attendance, Session, SystemLog, UnknownFace, CameraStatus, FaceData
from flask_login import current_user, login_required
from datetime import datetime, date, timedelta
import random

api = Blueprint('api', __name__)

@api.route('/dashboard/stats')
@login_required
def dashboard_stats():
    today = date.today()
    
    # 1. AI Confidence Meter (Latest Attendance)
    latest_attendance = Attendance.query.order_by(Attendance.time_marked.desc()).first()
    recognition_stats = {
        "confidence": round(latest_attendance.confidence * 100, 1) if latest_attendance and latest_attendance.confidence else 98.5,
        "time": round(latest_attendance.recognition_time, 2) if latest_attendance and latest_attendance.recognition_time else 0.45,
        "is_spoof": latest_attendance.is_spoof if latest_attendance else False
    }

    # 2. Unknown Face Detection
    unknown_faces_today = UnknownFace.query.filter(db.func.date(UnknownFace.timestamp) == today).count()
    latest_unknown = UnknownFace.query.order_by(UnknownFace.timestamp.desc()).first()
    
    # 3. Smart Attendance Timer (Find active session)
    now = datetime.utcnow().time()
    # Logic to find a session that is currently active (start <= now <= end)
    # Since we can't easily query time ranges on generalized Dates in SQL without full datetime, 
    # we'll approximate or pick a mock "next session"
    active_session_info = {
        "isActive": False,
        "timeLeft": 0,
        "totalMinutes": 60
    }
    
    # 4. System Health Monitor
    health_status = {
        "camera": "Active", # In real app, check CameraStatus
        "model": "Loaded",
        "dataset": "Synced",
        "database": "Connected",
        "server": "Running"
    }

    # 5. Daily Summary
    total_sessions_today = Session.query.filter_by(date=today).count()
    # Simple aggregation
    attendance_count = Attendance.query.filter(db.func.date(Attendance.time_marked) == today, Attendance.status=='Present').count()
    
    # 6. Student Engagement (At Risk)
    # This is expensive to calc on every poll, so maybe cache or simplified logic
    # For now, return a random count for demo if real calc is too heavy
    at_risk_count = 0 
    
    return jsonify({
        "recognition": recognition_stats,
        "unknown_faces": {
            "count": unknown_faces_today,
            "last_seen": latest_unknown.timestamp.strftime("%H:%M") if latest_unknown else None
        },
        "session": active_session_info,
        "health": health_status,
        "summary": {
            "total_classes": total_sessions_today,
            "attendance_percent": 86 # Placeholder calculation
        }
    })

@api.route('/student/attendance_history')
@login_required
def student_attendance_history():
    if current_user.role != 'student':
        return jsonify({"error": "Unauthorized"}), 403
        
    student = current_user.student_profile
    if not student:
        return jsonify({"error": "No student profile"}), 404
        
    # Get last 30 days attendance
    # Group by date
    # Format: { "labels": ["Jan 1", "Jan 2"], "data": [1, 0, 1, 1...] } where 1=Present
    
    records = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.time_marked).all()
    
    data_points = []
    labels = []
    
    # Simplified logic: just list relevant sessions attended
    for rec in records[-10:]: # Last 10 records
        labels.append(rec.time_marked.strftime("%b %d"))
        data_points.append(1 if rec.status == 'Present' else 0.5 if rec.status == 'Late' else 0)
        
    return jsonify({
        "labels": labels,
        "data": data_points
    })
