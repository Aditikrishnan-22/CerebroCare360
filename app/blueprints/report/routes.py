from flask import redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from app.blueprints.report import report_bp
from app.extensions import db
from app.models.mri_scan import MRIScan
from app.models.prediction import Prediction
from app.models.report import Report
from app.services.report_service import generate_report
import os
from flask import current_app

@report_bp.route('/generate/<int:prediction_id>')
@login_required
def generate(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)
    scan = prediction.scan

    if scan.user_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('scan.history'))

    # Check if report already exists
    existing = Report.query.filter_by(
        prediction_id=prediction_id,
        user_id=current_user.id
    ).order_by(Report.version.desc()).first()

    if existing:
        file_path = existing.file_path
    else:
        file_path = generate_report(scan, prediction, current_user)
        version = (existing.version + 1) if existing else 1
        report = Report(
            prediction_id = prediction_id,
            user_id       = current_user.id,
            file_path     = file_path,
            version       = version
        )
        db.session.add(report)
        db.session.commit()

    # Serve the file
    static_folder = os.path.join(current_app.root_path, 'static')
    directory = os.path.dirname(os.path.join(static_folder, file_path))
    filename  = os.path.basename(file_path)
    return send_from_directory(directory, filename, as_attachment=True)