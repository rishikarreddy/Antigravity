from app import create_app, db
from app.models import Student, Subject

app = create_app()

with app.app_context():
    print("Alignment Script Started...")
    
    # 1. Find the subject
    subject = Subject.query.first()
    if not subject:
        print("No subject found to align with.")
        exit()
        
    target_class = subject.class_name
    print(f"Target Class from Subject '{subject.name}': {target_class}")
    
    # 2. Find the student
    student = Student.query.first()
    if not student:
        print("No student found.")
        exit()
        
    print(f"Student '{student.user.name}' Current Class: {student.class_name}")
    
    # 3. Update
    if student.class_name != target_class:
        student.class_name = target_class
        db.session.commit()
        print(f"SUCCESS: Updated Student to Class '{target_class}'.")
    else:
        print("Classes already match.")
