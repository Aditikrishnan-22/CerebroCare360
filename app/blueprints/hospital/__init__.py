from flask import Blueprint
hospital_bp = Blueprint('hospital', __name__)
from app.blueprints.hospital import routes