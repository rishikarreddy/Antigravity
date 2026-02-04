from flask import Blueprint

student = Blueprint('student', __name__)
from app.student import routes
