from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.scan import scan_bp
from app.blueprints.scan.forms import ScanUploadForm
from app.extensions import db
from app.models.mri_scan import MRIScan
from app.models.prediction import Prediction
from app.services.image_service import validate_and_save
from app.services.ai_service import predict
import os
from flask import current_app

@scan_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = ScanUploadForm()
    if form.validate_on_submit():
        file = request.files.get('mri_image')
        filename, error = validate_and_save(file)
        if error:
            flash(error, 'danger')
            return redirect(url_for('scan.upload'))

        scan = MRIScan(
            user_id        = current_user.id,
            image_filename = filename,
            original_name  = file.filename,
            file_size      = request.content_length
        )
        db.session.add(scan)
        db.session.flush()

        # Run AI ensemble prediction
        try:
            image_path = os.path.join(
                current_app.root_path, 'static', 'uploads', filename
            )
            result = predict(image_path)

            prediction = Prediction(
                scan_id         = scan.id,
                has_tumor       = result['has_tumor'],
                tumor_type      = result['tumor_type'],
                confidence      = result['confidence'],
                prob_glioma     = result['prob_glioma'],
                prob_meningioma = result['prob_meningioma'],
                prob_notumor    = result['prob_notumor'],
                prob_pituitary  = result['prob_pituitary'],
                model_version   = result['model_version']
            )
        except Exception as e:
            print(f'AI prediction error: {e}')
            flash('AI model not ready yet. Showing placeholder result.', 'warning')
            prediction = Prediction(
                scan_id         = scan.id,
                has_tumor       = False,
                tumor_type      = None,
                confidence      = 0.0,
                prob_glioma     = 0.0,
                prob_meningioma = 0.0,
                prob_notumor    = 1.0,
                prob_pituitary  = 0.0,
                model_version   = 'pending',
                heatmap_filename = result.get('heatmap_filename')
            )

        db.session.add(prediction)
        db.session.commit()

        flash('Scan uploaded successfully!', 'success')
        return redirect(url_for('scan.result', scan_id=scan.id))

    return render_template('scan/upload.html', form=form)


@scan_bp.route('/result/<int:scan_id>')
@login_required
def result(scan_id):
    scan = MRIScan.query.filter_by(
        id=scan_id, user_id=current_user.id
    ).first_or_404()
    prediction = scan.prediction
    return render_template('scan/result.html', scan=scan, prediction=prediction)


@scan_bp.route('/history')
@login_required
def history():
    scans = MRIScan.query.filter_by(
        user_id=current_user.id
    ).order_by(MRIScan.upload_date.desc()).all()
    return render_template('scan/history.html', scans=scans)