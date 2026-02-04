from app import create_app,db
from app.models import User, Student, Faculty, Subject, FaceData

app = create_app()

with app.app_context():
    print("--- DIAGNOSIS REPORT ---")
    
    print("\n1. CONFIGURATION:")
    print(f"   FACE_MATCH_THRESHOLD: {app.config.get('FACE_MATCH_THRESHOLD', 'Not Set')}")
    
    print("\n2. STUDENTS:")
    students = Student.query.all()
    for s in students:
        face_status = "REGISTERED" if s.face_data else "MISSING"
        print(f"   - {s.user.name} (Roll: {s.roll_no}) | Class: '{s.class_name}' | Face Data: {face_status}")
        
    print("\n3. SUBJECTS:")
    subjects = Subject.query.all()
    for sub in subjects:
        faculty_name = sub.faculty.user.name if sub.faculty else "None"
        print(f"   - {sub.name} ({sub.code}) | Targeted Class: '{sub.class_name}' | Faculty: {faculty_name}")

    print("\n4. POTENTIAL ISSUES:")
    # Check for class mismatches
    classes_with_students = set(s.class_name for s in students)
    classes_with_subjects = set(s.class_name for s in subjects)
    
    if not classes_with_students.intersection(classes_with_subjects):
        print("   CRITICAL WARNING: No overlap between Student Classes and Subject Classes.")
        print(f"   Student Classes: {classes_with_students}")
        print(f"   Subject Classes: {classes_with_subjects}")
        print("   Attendance will NEVER work if classes don't match exactly.")
    else:
        print("   Class overlap detected. Data likely okay.")

    print("\n--- END REPORT ---")
