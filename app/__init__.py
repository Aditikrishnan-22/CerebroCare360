from flask import Flask, app, render_template
from app.config import Config
from app.extensions import db, login_manager, bcrypt, migrate
import json



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app.models.user import User
        from app.models.mri_scan import MRIScan
        from app.models.prediction import Prediction
        from app.models.report import Report
        from app.models.hospital import Hospital
        from app.models.symptom_rule import SymptomRule
        from app.models.chat_session import ChatSession, ChatMessage
        db.create_all()

    from app.blueprints.auth import auth_bp
    from app.blueprints.scan import scan_bp
    from app.blueprints.report import report_bp
    from app.blueprints.hospital import hospital_bp
    from app.blueprints.symptom import symptom_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.chat import chat_bp

    app.register_blueprint(auth_bp,     url_prefix='/auth')
    app.register_blueprint(scan_bp,     url_prefix='/scan')
    app.register_blueprint(report_bp,   url_prefix='/report')
    app.register_blueprint(hospital_bp, url_prefix='/hospital')
    app.register_blueprint(symptom_bp,  url_prefix='/symptom')
    app.register_blueprint(admin_bp,    url_prefix='/admin')
    app.register_blueprint(chat_bp)

    @app.template_filter('from_json')
    def from_json_filter(value):
        try:
            return json.loads(value)
        except Exception:
            return []

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

    @app.route('/')
    def index():
        return render_template('index.html')

    return app