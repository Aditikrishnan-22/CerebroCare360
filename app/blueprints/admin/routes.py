from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models.hospital import Hospital
from app.models.user import User
from app.models.mri_scan import MRIScan
from app.models.report import Report


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_users':     User.query.count(),
        'total_scans':     MRIScan.query.count(),
        'total_hospitals': Hospital.query.count(),
        'total_reports':   Report.query.count(),
    }
    hospitals = Hospital.query.order_by(Hospital.name).all()
    users     = User.query.order_by(User.id.desc()).all()
    return render_template('admin/dashboard.html',
                           stats=stats, hospitals=hospitals, users=users)


# ── HOSPITAL MANAGEMENT ─────────────────────────────────────────
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


# ── USER MANAGEMENT ─────────────────────────────────────────────
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