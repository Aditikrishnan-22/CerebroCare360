from flask import Blueprint
scan_bp = Blueprint('scan', __name__)
from app.blueprints.scan import routes