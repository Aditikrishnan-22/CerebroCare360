from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.blueprints.admin import admin_bp
from app.extensions import db, bcrypt
from app.models.hospital import Hospital
from app.models.user import User
from app.models.mri_scan import MRIScan
from app.models.prediction import Prediction
from app.models.report import Report
from app.models.password_reset_request import PasswordResetRequest
import os
from flask import current_app


# ── Guard decorator ──────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users     = User.query.order_by(User.id.desc()).all()
    hospitals = Hospital.query.order_by(Hospital.name).all()

    # Per-user stats injected into each user object dynamically
    user_stats = {}
    for u in users:
        scans        = u.scans
        total        = len(scans)
        failed       = sum(1 for s in scans if s.prediction and s.prediction.model_version == 'pending')
        tumor        = sum(1 for s in scans if s.prediction and s.prediction.has_tumor)
        last_scan    = max((s.upload_date for s in scans), default=None) if scans else None
        user_stats[u.id] = {
            'total':     total,
            'failed':    failed,
            'tumor':     tumor,
            'last_scan': last_scan
        }

    stats = {
        'total_users':     User.query.count(),
        'total_scans':     MRIScan.query.count(),
        'total_hospitals': Hospital.query.count(),
        'total_reports':   Report.query.count(),
        'failed_scans':    Prediction.query.filter_by(model_version='pending').count(),
    }

    # Pending reset requests
    reset_requests = (PasswordResetRequest.query
                      .filter_by(status='pending')
                      .order_by(PasswordResetRequest.requested_at.asc())
                      .all())
    resolved_requests = (PasswordResetRequest.query
                         .filter(PasswordResetRequest.status != 'pending')
                         .order_by(PasswordResetRequest.resolved_at.desc())
                         .limit(10).all())

    stats['pending_resets'] = len(reset_requests)

    return render_template('admin/dashboard.html',
                           stats=stats, hospitals=hospitals,
                           users=users, user_stats=user_stats,
                           reset_requests=reset_requests,
                           resolved_requests=resolved_requests)


# ── HOSPITAL MANAGEMENT ──────────────────────────────────────────
def _hospital_from_form(h):
    h.name          = request.form.get('name', '').strip()
    h.address       = request.form.get('address', '').strip()
    h.city          = request.form.get('city', '').strip()
    h.state         = request.form.get('state', '').strip()
    h.phone         = request.form.get('phone', '').strip()
    h.email         = request.form.get('email', '').strip()
    h.website       = request.form.get('website', '').strip()
    h.specialty     = request.form.get('specialty', '').strip()
    h.hospital_type = request.form.get('hospital_type', '').strip()
    h.accreditation = request.form.get('accreditation', '').strip()
    h.facilities    = request.form.get('facilities', '').strip()
    h.doctors       = request.form.get('doctors', '').strip()
    h.mri_types     = request.form.get('mri_types', '').strip()
    h.cost_range    = request.form.get('cost_range', '').strip()
    h.is_mri_center = request.form.get('is_mri_center') == '1'
    try:
        h.rating    = float(request.form.get('rating')) if request.form.get('rating') else None
    except ValueError:
        h.rating    = None
    try:
        h.latitude  = float(request.form.get('latitude')) if request.form.get('latitude') else None
    except ValueError:
        h.latitude  = None
    try:
        h.longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
    except ValueError:
        h.longitude = None
    return h


@admin_bp.route('/hospitals/add', methods=['POST'])
@login_required
@admin_required
def add_hospital():
    h = Hospital(is_active=True)
    h = _hospital_from_form(h)
    db.session.add(h)
    db.session.commit()
    flash(f'Hospital "{h.name}" added.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/hospitals/edit/<int:hospital_id>', methods=['POST'])
@login_required
@admin_required
def edit_hospital(hospital_id):
    h = Hospital.query.get_or_404(hospital_id)
    h = _hospital_from_form(h)
    db.session.commit()
    flash(f'Hospital "{h.name}" updated.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/hospitals/toggle/<int:hospital_id>')
@login_required
@admin_required
def toggle_hospital(hospital_id):
    h = Hospital.query.get_or_404(hospital_id)
    h.is_active = not h.is_active
    db.session.commit()
    flash(f'Hospital "{h.name}" {"activated" if h.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/hospitals/delete/<int:hospital_id>')
@login_required
@admin_required
def delete_hospital(hospital_id):
    h = Hospital.query.get_or_404(hospital_id)
    name = h.name
    db.session.delete(h)
    db.session.commit()
    flash(f'Hospital "{name}" deleted.', 'success')
    return redirect(url_for('admin.dashboard'))


# ── USER MANAGEMENT ──────────────────────────────────────────────
@admin_bp.route('/users/toggle-role/<int:user_id>')
@login_required
@admin_required
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.dashboard'))
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    flash(f'{user.full_name} is now {user.role.upper()}.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/toggle-active/<int:user_id>')
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.dashboard'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'{user.full_name} {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'warning')
        return redirect(url_for('admin.dashboard'))
    name = user.full_name
    
    # Delete related password reset requests to avoid NOT NULL constraint errors
    from app.models.password_reset_request import PasswordResetRequest
    PasswordResetRequest.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{name}" deleted.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/<int:user_id>/scans')
@login_required
@admin_required
def user_scans(user_id):
    user  = User.query.get_or_404(user_id)
    scans = MRIScan.query.filter_by(user_id=user_id).order_by(MRIScan.upload_date.desc()).all()
    return render_template('admin/user_scans.html', user=user, scans=scans)


# ────────────────────────────────────────────────────────────────
#  NEW FEATURE 1 — Reset user password
# ────────────────────────────────────────────────────────────────
@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user     = User.query.get_or_404(user_id)
    new_pass = request.form.get('new_password', '').strip()

    if len(new_pass) < 6:
        flash('Password must be at least 6 characters.', 'danger')
        return redirect(url_for('admin.dashboard'))

    user.password_hash = bcrypt.generate_password_hash(new_pass).decode('utf-8')
    db.session.commit()
    flash(f'Password for {user.full_name} has been reset successfully.', 'success')
    return redirect(url_for('admin.dashboard'))


# ────────────────────────────────────────────────────────────────
#  NEW FEATURE 2 — View full scan detail (admin view of result)
# ────────────────────────────────────────────────────────────────
@admin_bp.route('/scans/<int:scan_id>')
@login_required
@admin_required
def view_scan(scan_id):
    scan       = MRIScan.query.get_or_404(scan_id)
    user       = User.query.get_or_404(scan.user_id)
    prediction = scan.prediction
    return render_template('admin/scan_detail.html',
                           scan=scan, user=user, prediction=prediction)


# ────────────────────────────────────────────────────────────────
#  NEW FEATURE 3 — Re-run failed prediction
# ────────────────────────────────────────────────────────────────
@admin_bp.route('/scans/<int:scan_id>/rerun', methods=['POST'])
@login_required
@admin_required
def rerun_prediction(scan_id):
    scan = MRIScan.query.get_or_404(scan_id)

    # Only allow rerun if prediction is pending/failed
    if not scan.prediction or scan.prediction.model_version != 'pending':
        flash('This scan does not have a failed prediction to re-run.', 'warning')
        return redirect(url_for('admin.view_scan', scan_id=scan_id))

    image_path = os.path.join(
        current_app.root_path, 'static', 'uploads', scan.image_filename
    )

    if not os.path.exists(image_path):
        flash('MRI image file not found on server. Cannot re-run prediction.', 'danger')
        return redirect(url_for('admin.view_scan', scan_id=scan_id))

    try:
        from app.services.ai_service import predict
        result = predict(image_path)

        p = scan.prediction
        p.has_tumor        = result['has_tumor']
        p.tumor_type       = result['tumor_type']
        p.confidence       = result['confidence']
        p.prob_glioma      = result['prob_glioma']
        p.prob_meningioma  = result['prob_meningioma']
        p.prob_notumor     = result['prob_notumor']
        p.prob_pituitary   = result['prob_pituitary']
        p.model_version    = result['model_version']
        p.heatmap_filename = result.get('heatmap_filename')
        p.heatmap_ready    = bool(result.get('heatmap_filename'))

        db.session.commit()
        flash(f'Prediction re-run successfully for Scan #{scan_id}. '
              f'Result: {"Tumor — " + (result["tumor_type"] or "Unknown") if result["has_tumor"] else "No Tumor"}.',
              'success')

    except Exception as e:
        flash(f'Re-run failed: {str(e)}', 'danger')

    return redirect(url_for('admin.view_scan', scan_id=scan_id))


# ────────────────────────────────────────────────────────────────
#  NEW FEATURE 4 — Delete a specific scan on behalf of user
# ────────────────────────────────────────────────────────────────
def _remove_file(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f'[admin delete] Could not remove {path}: {e}')


@admin_bp.route('/scans/<int:scan_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_scan(scan_id):
    scan = MRIScan.query.get_or_404(scan_id)
    user_id = scan.user_id
    base    = current_app.root_path

    # Remove files
    if scan.image_filename:
        _remove_file(os.path.join(base, 'static', 'uploads', scan.image_filename))
    if scan.prediction:
        if scan.prediction.heatmap_filename:
            _remove_file(os.path.join(base, 'static', 'heatmaps', scan.prediction.heatmap_filename))
        for report in scan.prediction.reports:
            if report.filename:
                _remove_file(os.path.join(base, 'static', 'reports', report.filename))

    db.session.delete(scan)
    db.session.commit()
    flash(f'Scan #{scan_id} deleted successfully.', 'success')
    return redirect(url_for('admin.user_scans', user_id=user_id))


# ═══════════════════════════════════════════════════════════════
#  PASSWORD RESET REQUEST MANAGEMENT
# ═══════════════════════════════════════════════════════════════
from app.models.password_reset_request import PasswordResetRequest
from app.extensions import mail
from flask_mail import Message
import random, string
from datetime import datetime


def _generate_temp_password(length=10):
    """Generate a readable temp password: letters + digits, no ambiguous chars."""
    chars = string.ascii_letters.replace('l','').replace('O','').replace('I','') + string.digits
    return ''.join(random.choices(chars, k=length))


def _send_temp_password_email(user_email, user_name, temp_password, app_name='CerebroCare360'):
    """Send temp password email to user via Flask-Mail / Gmail SMTP."""
    try:
        msg = Message(
            subject=f'[{app_name}] Your Temporary Password',
            recipients=[user_email]
        )
        msg.html = f"""
        <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;
                    background:#faf9ff;border-radius:16px;border:1px solid #ede9fe;">
          <div style="text-align:center;margin-bottom:24px;">
            <div style="width:56px;height:56px;border-radius:14px;
                        background:linear-gradient(135deg,#7c3aed,#db2777);
                        display:inline-flex;align-items:center;justify-content:center;
                        font-size:26px;color:white;margin-bottom:12px;">🧠</div>
            <h2 style="font-size:1.4rem;color:#1a0533;margin:0;">{app_name}</h2>
          </div>

          <h3 style="color:#1a0533;font-size:1.1rem;margin-bottom:8px;">
            Hi {user_name},
          </h3>
          <p style="color:#5b4f72;font-size:14px;line-height:1.7;margin-bottom:20px;">
            Your password reset request has been reviewed and approved by our admin team.
            Here is your <strong>temporary password</strong>:
          </p>

          <div style="background:white;border:2px dashed #ddd6fe;border-radius:12px;
                      padding:20px;text-align:center;margin-bottom:20px;">
            <span style="font-family:monospace;font-size:1.8rem;font-weight:700;
                         letter-spacing:0.12em;color:#7c3aed;background:#f5f3ff;
                         padding:8px 20px;border-radius:8px;">
              {temp_password}
            </span>
          </div>

          <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                      padding:12px 16px;font-size:13px;color:#78350f;margin-bottom:20px;">
            <strong>⚠️ Important:</strong> This is a temporary password.
            Please log in and change it immediately from your profile settings.
            Do not share this password with anyone.
          </div>

          <p style="color:#5b4f72;font-size:13.5px;line-height:1.6;margin-bottom:6px;">
            Steps to log in:
          </p>
          <ol style="color:#5b4f72;font-size:13.5px;line-height:1.8;padding-left:20px;">
            <li>Go to the {app_name} login page</li>
            <li>Enter your email and the temporary password above</li>
            <li>Change your password from your profile</li>
          </ol>

          <hr style="border:none;border-top:1px solid #ede9fe;margin:20px 0;">
          <p style="color:#9070b0;font-size:12px;text-align:center;margin:0;">
            If you did not request a password reset, please contact our admin immediately.<br>
            © {app_name} — AI Brain Tumor Detection Platform
          </p>
        </div>
        """
        msg.body = (
            f"Hi {user_name},\n\n"
            f"Your temporary password is: {temp_password}\n\n"
            f"Please log in and change it immediately.\n\n"
            f"— {app_name} Team"
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f'[mail] Failed to send email to {user_email}: {e}')
        return False


# ── Updated dashboard — now includes reset requests ─────────────
# Replace the existing dashboard() route with this one
# (already done above — this section adds the query for reset requests)

@admin_bp.route('/users/reset-requests')
@login_required
@admin_required
def reset_requests():
    """Return pending reset request count as JSON (for badge polling)."""
    count = PasswordResetRequest.query.filter_by(status='pending').count()
    return {'count': count}


@admin_bp.route('/users/reset-requests/resolve/<int:req_id>', methods=['POST'])
@login_required
@admin_required
def resolve_reset_request(req_id):
    """Admin resolves a reset request — generates temp password and emails user."""
    req = PasswordResetRequest.query.get_or_404(req_id)

    if req.status != 'pending':
        flash('This request has already been resolved.', 'warning')
        return redirect(url_for('admin.dashboard') + '#tab-users')

    temp_pass = _generate_temp_password()

    # Update user password
    req.user.password_hash = bcrypt.generate_password_hash(temp_pass).decode('utf-8')

    # Update request record
    req.status       = 'resolved'
    req.resolved_at  = datetime.utcnow()
    req.resolved_by  = current_user.id
    req.temp_password= temp_pass   # store for audit (optional — remove if privacy concern)

    db.session.commit()

    # Send email
    email_sent = _send_temp_password_email(
        user_email=req.user.email,
        user_name=req.user.full_name.split()[0],
        temp_password=temp_pass
    )

    if email_sent:
        flash(
            f'Password reset for {req.user.full_name}. '
            f'Temporary password emailed to {req.user.email}.',
            'success'
        )
    else:
        flash(
            f'Password reset for {req.user.full_name}, but email delivery failed. '
            f'Temporary password: {temp_pass} — please share manually.',
            'warning'
        )

    return redirect(url_for('admin.dashboard') + '#tab-users')


@admin_bp.route('/users/reset-requests/reject/<int:req_id>', methods=['POST'])
@login_required
@admin_required
def reject_reset_request(req_id):
    """Admin rejects a reset request."""
    req = PasswordResetRequest.query.get_or_404(req_id)

    if req.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('admin.dashboard') + '#tab-users')

    req.status      = 'rejected'
    req.resolved_at = datetime.utcnow()
    req.resolved_by = current_user.id
    db.session.commit()

    flash(f'Reset request from {req.user.full_name} rejected.', 'info')
    return redirect(url_for('admin.dashboard') + '#tab-users')