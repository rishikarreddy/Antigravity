from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'faculty', 'student'
    theme = db.Column(db.String(10), default='light') # 'light' or 'dark'
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    faculty_profile = db.relationship('Faculty', backref='user', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.role}')"

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    class_name = db.Column(db.String(50), nullable=False) # Linked to Subject.class_name
    department = db.Column(db.String(100), nullable=False)
    
    face_data = db.relationship('FaceData', backref='student', uselist=False, cascade="all, delete-orphan")
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    
    subjects = db.relationship('Subject', backref='faculty', lazy=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g. "Data Structures"
    code = db.Column(db.String(20), nullable=False) # e.g. "CS101"
    class_name = db.Column(db.String(50), nullable=False) # e.g. "CSA-2024"
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    
    sessions = db.relationship('Session', backref='subject', lazy=True)

class FaceData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), unique=True, nullable=False)
    embedding = db.Column(db.Text, nullable=False) # JSON serialized list
    image_path = db.Column(db.String(200), nullable=False) # Path to representative image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_embedding(self, embedding_list):
        self.embedding = json.dumps(embedding_list)

    def get_embedding(self):
        return json.loads(self.embedding)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    start_time = db.Column(db.Time, nullable=False, default=lambda: datetime.utcnow().time())
    end_time = db.Column(db.Time, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    attendance_records = db.relationship('Attendance', backref='session', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    status = db.Column(db.String(20), default='Present') # Present, Late, Absent
    time_marked = db.Column(db.DateTime, default=datetime.utcnow)
    confidence = db.Column(db.Float, nullable=True) # Confidence score of recognition
    recognition_time = db.Column(db.Float, nullable=True) # Time taken to recognize in seconds
    is_spoof = db.Column(db.Boolean, default=False) # Anti-spoofing flag

class UnknownFace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    camera_id = db.Column(db.String(50), nullable=True)
    
class CameraStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='Offline') # Active, Idle, Offline
    last_ping = db.Column(db.DateTime, default=datetime.utcnow)

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False) # INFO, WARNING, ERROR
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PasswordResetRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='password_requests')
