from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models.hospital import Hospital
from app.models.symptom_rule import SymptomRule
from app.models.user import User
from app.models.mri_scan import MRIScan
from app.models.report import Report
from app.utils.decorators import admin_required
import json

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
        'total_reports':   Report.query.count()
    }
    hospitals = Hospital.query.order_by(Hospital.name).all()
    rules     = SymptomRule.query.all()
    return render_template('admin/dashboard.html',
                           stats=stats,
                           hospitals=hospitals,
                           rules=rules)

@admin_bp.route('/hospitals/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_hospital():
    if request.method == 'POST':
        h = Hospital(
            name          = request.form.get('name'),
            address       = request.form.get('address'),
            city          = request.form.get('city'),
            state         = request.form.get('state'),
            phone         = request.form.get('phone'),
            email         = request.form.get('email'),
            specialty     = request.form.get('specialty'),
            accreditation = request.form.get('accreditation'),
            is_active     = True
        )
        db.session.add(h)
        db.session.commit()
        flash('Hospital added successfully.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/hospitals.html', hospital=None)

@admin_bp.route('/hospitals/edit/<int:hospital_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_hospital(hospital_id):
    h = Hospital.query.get_or_404(hospital_id)
    if request.method == 'POST':
        h.name          = request.form.get('name')
        h.address       = request.form.get('address')
        h.city          = request.form.get('city')
        h.state         = request.form.get('state')
        h.phone         = request.form.get('phone')
        h.email         = request.form.get('email')
        h.specialty     = request.form.get('specialty')
        h.accreditation = request.form.get('accreditation')
        db.session.commit()
        flash('Hospital updated.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/hospitals.html', hospital=h)

@admin_bp.route('/hospitals/delete/<int:hospital_id>')
@login_required
@admin_required
def delete_hospital(hospital_id):
    h = Hospital.query.get_or_404(hospital_id)
    db.session.delete(h)
    db.session.commit()
    flash('Hospital deleted.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/rules/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_rule():
    if request.method == 'POST':
        keys = request.form.getlist('symptom_keys')
        rule = SymptomRule(
            symptom_keys = json.dumps(keys),
            condition    = request.form.get('condition'),
            department   = request.form.get('department'),
            urgency      = request.form.get('urgency'),
            advice       = request.form.get('advice')
        )
        db.session.add(rule)
        db.session.commit()
        flash('Rule added.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/rules.html', rule=None)

@admin_bp.route('/rules/edit/<int:rule_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_rule(rule_id):
    rule = SymptomRule.query.get_or_404(rule_id)
    if request.method == 'POST':
        keys = request.form.getlist('symptom_keys')
        rule.symptom_keys = json.dumps(keys)
        rule.condition    = request.form.get('condition')
        rule.department   = request.form.get('department')
        rule.urgency      = request.form.get('urgency')
        rule.advice       = request.form.get('advice')
        db.session.commit()
        flash('Rule updated.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/rules.html', rule=rule)

@admin_bp.route('/rules/delete/<int:rule_id>')
@login_required
@admin_required
def delete_rule(rule_id):
    rule = SymptomRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    flash('Rule deleted.', 'success')
    return redirect(url_for('admin.dashboard'))