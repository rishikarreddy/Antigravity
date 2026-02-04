import os

class Config:
    # Key for session security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-change-in-production-12345'
    
    # Database
    # Using absolute path for reliability in some envs, but relative is fine for SQLite usually
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'faces')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # AI Performance Tuning
    # Higher = stricter match. 0.40 is standard for VGG-Face + Euclidean L2
    FACE_MATCH_THRESHOLD = 0.50 
