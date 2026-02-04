from flask import render_template, url_for, flash, redirect, request
from app import db, bcrypt
from app.auth import auth
from app.auth.forms import LoginForm
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            
            # Role-based redirect
            if not next_page:
                if user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user.role == 'faculty':
                    return redirect(url_for('faculty.dashboard'))
                elif user.role == 'student':
                    return redirect(url_for('student.dashboard'))
            
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
    return render_template('auth/login.html', title='Login', form=form)

@auth.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

    return render_template('auth/change_password.html', title='Change Password', form=form)


@auth.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    from app.auth.forms import ForgotPasswordForm, ResetPasswordVerifiedForm
    from app.models import PasswordResetRequest
    
    # Check if there is an email involved in the request args (if redirecting back)
    # But usually we start simple with an empty form
    form = ForgotPasswordForm()
    
    # If the form is submitted (Email entry)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Check for existing request
            existing_request = PasswordResetRequest.query.filter_by(user_id=user.id, status='Pending').first()
            approved_request = PasswordResetRequest.query.filter_by(user_id=user.id, status='Approved').first()
            
            if approved_request:
                # If approved, show the reset password form
                # We need to pass the email or user_id to the reset form handling, 
                # but for now let's just render a different template or use session? 
                # Better approach: Render the Reset Verified Template directly here
                # We'll need a way to maintain state. 
                # Let's simple render `reset_password_verified.html` passing the user's email hidden or implicit?
                # Actually, standard flow: 
                # 1. User enters Email.
                # 2. Loop detects "Approved".
                # 3. Flashes "Your request is approved".
                # 4. Redirects to a distinct "reset_token" style url OR just handle it here if we trust the email input.
                # Since we don't have email tokens, we trust the person entering the email IF the request is approved.
                # Note: This is weak security (anyone knowing the email can reset if approved), as noted in the plan.
                
                reset_form = ResetPasswordVerifiedForm()
                return render_template('auth/reset_password_verified.html', title='Reset Password', form=reset_form, email=user.email)
            
            elif existing_request:
                flash('You have already requested a password reset. Please wait for Admin approval.', 'info')
            else:
                # Create NEW request
                req = PasswordResetRequest(user_id=user.id, email=user.email)
                db.session.add(req)
                db.session.commit()
                flash('Your password reset request has been sent to the Admin. Please wait for approval.', 'success')
                return redirect(url_for('auth.login'))
        else:
            flash('If an account with that email exists, a password reset request has been initiated.', 'info')
            return redirect(url_for('auth.login'))

    # Handle the submission of the Reset Logic (The actual password change)
    # Since we are reusing the route or need a secondary post?
    # Let's verify if we are posting the ResetForm.
    # The ResetForm needs to be in a separate route OR distinct logic.
    # To keep it clean, let's make a separate route `reset_password_verified` 
    # OR handle it in the same route with a hidden field.
    # Let's try to handle it in a separate route to avoid form collisions if possible, 
    # BUT since we are doing a flow based on email, maybe separate is better.
    
    return render_template('auth/forgot_password.html', title='Forgot Password', form=form)

@auth.route("/reset_password_verified/<email>", methods=['GET', 'POST'])
def reset_password_verified(email):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
        
    from app.auth.forms import ResetPasswordVerifiedForm
    from app.models import PasswordResetRequest

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid request.', 'danger')
        return redirect(url_for('auth.login'))

    # Double check it is approved
    approved_request = PasswordResetRequest.query.filter_by(user_id=user.id, status='Approved').first()
    if not approved_request:
        flash('No approved reset request found for this email.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordVerifiedForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password_hash = hashed_password
        
        # Cleanup requests
        db.session.delete(approved_request)
        db.session.commit()
        
        flash('Your password has been updated! You can now login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password_verified.html', title='Reset Password', form=form, email=email)

