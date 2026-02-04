# Force Reload - v2
import numpy as np

# PATCH: Restore deprecated aliases for TensorFlow 2.5 compat with NumPy 1.20+
try:
    if not hasattr(np, 'object'):
        np.object = object
    if not hasattr(np, 'bool'):
        np.bool = bool
    if not hasattr(np, 'int'):
        np.int = int
    if not hasattr(np, 'float'):
        np.float = float
    if not hasattr(np, 'typeDict'):
        np.typeDict = np.sctypeDict
except Exception as e:
    print(f"NumPy Patch Error: {e}")

from app import create_app, db
import os

app = create_app()

if __name__ == '__main__':
    # Ensure instance folder exists for SQLite
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Create Tables & Default Admin on startup if not exists
    with app.app_context():
        db.create_all()
        from app.models import User
        from app import bcrypt
        
        # Check if Admin exists
        if not User.query.filter_by(role='admin').first():
            print("Creating Default Admin Account...")
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            # Assuming User model has these fields - we will define them shortly
            admin = User(
                name='Super Admin',
                email='admin@example.com',
                password_hash=hashed_pw,
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin Created: admin@example.com / admin123")

    # Run App
    app.run(debug=True, host='0.0.0.0', port=5000)
