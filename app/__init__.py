from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

# Initialize Extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # Redirect here if unauthorized
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.auth.routes import auth
    from app.admin.routes import admin
    from app.faculty.routes import faculty
    from app.student.routes import student
    from app.main.routes import main
    from app.main.api_routes import api

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(faculty)
    app.register_blueprint(student)
    app.register_blueprint(main)
    app.register_blueprint(api, url_prefix='/api')

    return app
