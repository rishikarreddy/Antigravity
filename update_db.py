from app import create_app, db
# Ensuring model is imported so SQLAlchemy sees it
from app.models import PasswordResetRequest 

app = create_app()
with app.app_context():
    db.create_all()
    print("Database Schema Updated successfully.")
