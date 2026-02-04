from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db 

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    return render_template('home.html')

@main.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Handle Theme Toggle
        theme = request.form.get('theme')
        if theme in ['light', 'dark']:
            current_user.theme = theme
            db.session.commit()
            flash(f'Theme updated to {theme.title()} Mode!', 'success')
            return redirect(url_for('main.settings'))
            
    return render_template('settings.html')

@main.route("/toggle_theme", methods=['POST'])
@login_required
def toggle_theme():
    new_theme = 'dark' if current_user.theme == 'light' else 'light'
    current_user.theme = new_theme
    db.session.commit()
    # Redirect back to the page they came from
    return redirect(request.referrer or url_for('main.home'))

@main.route("/about")
def about():
    # If using a separate about page, render it
    # If using the section in settings, redirect there
    # User asked for 'about' in navbar, usually implies a page. 
    # Let's create a dedicated about page for better UX.
    return render_template('about.html')
