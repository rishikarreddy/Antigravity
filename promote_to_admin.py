from app import create_app, db
from app.models import User

app = create_app()

def promote_to_admin():
    with app.app_context():
        email = input("Enter email to promote to Admin: ")
        user = User.query.filter_by(email=email).first()
        
        if user:
            user.role = 'admin'
            db.session.commit()
            print(f"SUCCESS: {user.name} ({user.email}) is now an Admin.")
        else:
            print(f"ERROR: User with email '{email}' not found.")

if __name__ == "__main__":
    promote_to_admin()
