from flask import Blueprint

faculty = Blueprint('faculty', __name__)
from app.faculty import routes
