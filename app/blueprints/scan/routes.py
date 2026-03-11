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


# ─────────────────────────────────────────────────
#  Upload
# ─────────────────────────────────────────────────
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

        try:
            image_path = os.path.join(
                current_app.root_path, 'static', 'uploads', filename
            )
            result = predict(image_path)

            prediction = Prediction(
                scan_id          = scan.id,
                has_tumor        = result['has_tumor'],
                tumor_type       = result['tumor_type'],
                confidence       = result['confidence'],
                prob_glioma      = result['prob_glioma'],
                prob_meningioma  = result['prob_meningioma'],
                prob_notumor     = result['prob_notumor'],
                prob_pituitary   = result['prob_pituitary'],
                model_version    = result['model_version'],
                heatmap_filename = result.get('heatmap_filename'),
                heatmap_ready    = bool(result.get('heatmap_filename'))
            )
        except Exception as e:
            print(f'AI prediction error: {e}')
            flash('AI model not ready yet. Showing placeholder result.', 'warning')
            prediction = Prediction(
                scan_id          = scan.id,
                has_tumor        = False,
                tumor_type       = None,
                confidence       = 0.0,
                prob_glioma      = 0.0,
                prob_meningioma  = 0.0,
                prob_notumor     = 1.0,
                prob_pituitary   = 0.0,
                model_version    = 'pending',
                heatmap_filename = None,
                heatmap_ready    = False
            )

        db.session.add(prediction)
        db.session.commit()

        flash('Scan uploaded successfully!', 'success')
        return redirect(url_for('scan.result', scan_id=scan.id))

    return render_template('scan/upload.html', form=form)


# ─────────────────────────────────────────────────
#  Result
# ─────────────────────────────────────────────────
@scan_bp.route('/result/<int:scan_id>')
@login_required
def result(scan_id):
    scan = MRIScan.query.filter_by(
        id=scan_id, user_id=current_user.id
    ).first_or_404()
    prediction = scan.prediction

    if not prediction:
        # Fallback if prediction is completely missing (e.g. error during upload)
        prediction = Prediction(
            scan_id=scan.id,
            has_tumor=False,
            tumor_type=None,
            confidence=0.0,
            model_version='pending'
        )

    return render_template('scan/result.html', scan=scan, prediction=prediction)


# ─────────────────────────────────────────────────
#  History
# ─────────────────────────────────────────────────
@scan_bp.route('/history')
@login_required
def history():
    q = request.args.get('q', '').strip().lower()
    result_filter = request.args.get('result', '')
    sort_val = request.args.get('sort', 'newest')

    query = MRIScan.query.filter_by(user_id=current_user.id)

    if sort_val == 'oldest':
        query = query.order_by(MRIScan.upload_date.asc())
    else:
        query = query.order_by(MRIScan.upload_date.desc())

    all_scans = query.all()
    scans = []

    for scan in all_scans:
        match = True
        
        # Result filter
        if result_filter:
            if not scan.prediction:
                match = False
            elif result_filter == 'tumor' and not scan.prediction.has_tumor:
                match = False
            elif result_filter == 'notumor' and scan.prediction.has_tumor:
                match = False
            elif result_filter in ['glioma', 'meningioma', 'pituitary']:
                if scan.prediction.tumor_type != result_filter:
                    match = False
        
        # Search query
        if match and q:
            date_str = scan.upload_date.strftime('%d %b %Y, %H:%M').lower() if scan.upload_date else ''
            tumor_str = scan.prediction.tumor_type.lower() if scan.prediction and scan.prediction.tumor_type else ''
            
            if q not in date_str and q not in tumor_str:
                match = False
        
        if match:
            scans.append(scan)

    return render_template('scan/history.html', scans=scans)


# ─────────────────────────────────────────────────
#  Delete helpers
# ─────────────────────────────────────────────────
def _delete_scan_files(scan):
    """Remove physical files for a scan (image, heatmap, PDF reports)."""
    base = current_app.root_path  # = .../app

    if scan.image_filename:
        _remove(os.path.join(base, 'static', 'uploads', scan.image_filename))

    if scan.prediction:
        if scan.prediction.heatmap_filename:
            _remove(os.path.join(base, 'static', 'heatmaps', scan.prediction.heatmap_filename))
        for report in scan.prediction.reports:
            if report.file_path:
                _remove(os.path.join(base, 'static', report.file_path))

def _remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f'[delete] Could not remove {path}: {e}')


# ─────────────────────────────────────────────────
#  Single delete
# ─────────────────────────────────────────────────
@scan_bp.route('/delete/<int:scan_id>', methods=['POST'])
@login_required
def delete_scan(scan_id):
    scan = MRIScan.query.filter_by(
        id=scan_id, user_id=current_user.id
    ).first_or_404()

    try:
        _delete_scan_files(scan)
        db.session.delete(scan)
        db.session.commit()
        flash('Scan deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting scan: {str(e)}', 'danger')

    return redirect(url_for('scan.history'))


# ─────────────────────────────────────────────────
#  Bulk delete
# ─────────────────────────────────────────────────
@scan_bp.route('/delete-bulk', methods=['POST'])
@login_required
def delete_scans_bulk():
    raw = request.form.get('scan_ids', '')
    if not raw:
        flash('No scans selected.', 'warning')
        return redirect(url_for('scan.history'))

    ids = [int(i.strip()) for i in raw.split(',') if i.strip().isdigit()]
    if not ids:
        flash('No valid scans selected.', 'warning')
        return redirect(url_for('scan.history'))

    scans = MRIScan.query.filter(
        MRIScan.id.in_(ids),
        MRIScan.user_id == current_user.id
    ).all()

    deleted = 0
    for scan in scans:
        try:
            _delete_scan_files(scan)
            db.session.delete(scan)
            deleted += 1
        except Exception as e:
            print(f'[bulk delete] Error on scan {scan.id}: {e}')

    db.session.commit()
    flash(f'{deleted} scan{"s" if deleted != 1 else ""} deleted successfully.', 'success')
    return redirect(url_for('scan.history'))