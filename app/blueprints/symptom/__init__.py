from flask import Blueprint
symptom_bp = Blueprint('symptom', __name__)
from app.blueprints.symptom import routes