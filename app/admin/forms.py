from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('student', 'Student'), ('faculty', 'Faculty')], validators=[DataRequired()])
    
    # Student Specific
    roll_no = StringField('Roll No (Students only)')
    class_name = StringField('Class Code (e.g. CS-A)')
    student_dept = StringField('Department')

    # Faculty Specific
    faculty_dept = StringField('Department (Faculty only)')

    submit = SubmitField('Register User')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')
            
    def validate_roll_no(self, roll_no):
        if self.role.data == 'student' and not roll_no.data:
            raise ValidationError('Roll No is required for students.')
            
    def validate_class_name(self, class_name):
        if self.role.data == 'student' and not class_name.data:
            raise ValidationError('Class Name is required for students.')

class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired(), Length(max=100)])
    code = StringField('Subject Code', validators=[DataRequired(), Length(max=20)])
    class_name = StringField('Class / Section', validators=[DataRequired(), Length(max=50)])
    faculty_id = SelectField('Assign Faculty', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create Subject')


class EditUserForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    # Password is removed for edit (handled separately if needed)
    
    # Student Specific
    roll_no = StringField('Roll No (Students only)')
    class_name = StringField('Class Code (e.g. CS-A)')
    student_dept = StringField('Department')

    # Faculty Specific
    faculty_dept = StringField('Department (Faculty only)')

    submit = SubmitField('Update User')
    
    # Validation for unique Email (exclude current user)
    def __init__(self, original_email, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already taken.')
