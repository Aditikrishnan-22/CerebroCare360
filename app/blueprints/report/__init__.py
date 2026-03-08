from flask import Blueprint
report_bp = Blueprint('report', __name__)
from app.blueprints.report import routes