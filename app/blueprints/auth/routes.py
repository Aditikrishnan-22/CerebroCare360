from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from app.blueprints.auth.forms import LoginForm, RegisterForm
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.mri_scan import MRIScan
from app.models.report import Report
from app.models.password_reset_request import PasswordResetRequest


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        try:
            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash('Welcome back, ' + user.full_name + '!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Invalid email or password.', 'danger')
        except ValueError:
            flash('Your account requires a password reset due to a security update. Please use the "Forgot Password" feature.', 'warning')
            return redirect(url_for('auth.forgot_password'))
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash('An account with that email already exists.', 'danger')
            return redirect(url_for('auth.register'))
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            full_name     = form.full_name.data,
            email         = form.email.data,
            password_hash = hashed_pw,
            role          = 'user'
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please sign in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from flask_wtf import FlaskForm
    form = FlaskForm()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_info':
            current_user.full_name = request.form.get('full_name')
            current_user.email     = request.form.get('email')
            db.session.commit()
            flash('Profile updated successfully.', 'success')

        elif action == 'change_password':
            current_pw  = request.form.get('current_password')
            new_pw      = request.form.get('new_password')
            confirm_pw  = request.form.get('confirm_password')

            try:
                if not bcrypt.check_password_hash(current_user.password_hash, current_pw):
                    flash('Current password is incorrect.', 'danger')
                elif new_pw != confirm_pw:
                    flash('New passwords do not match.', 'danger')
                elif len(new_pw) < 8:
                    flash('Password must be at least 8 characters.', 'danger')
                else:
                    current_user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
                    db.session.commit()
                    flash('Password updated successfully.', 'success')
            except ValueError:
                flash('Your account requires a password reset due to a security update. Please use the "Forgot Password" feature.', 'warning')

        return redirect(url_for('auth.profile'))

    scan_count   = MRIScan.query.filter_by(user_id=current_user.id).count()
    report_count = Report.query.filter_by(user_id=current_user.id).count()

    return render_template('auth/profile.html',
                           form=form,
                           scan_count=scan_count,
                           report_count=report_count)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('scan.upload'))

    if request.method == 'POST':
        email  = request.form.get('email', '').strip().lower()
        reason = request.form.get('reason', '').strip()

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('If that email is registered, your reset request has been submitted. '
                  'An admin will contact you shortly.', 'info')
            return redirect(url_for('auth.login'))

        existing = PasswordResetRequest.query.filter_by(
            user_id=user.id, status='pending'
        ).first()

        if existing:
            flash('You already have a pending reset request. '
                  'An admin will process it shortly.', 'warning')
            return redirect(url_for('auth.login'))

        req = PasswordResetRequest(user_id=user.id, reason=reason or None)
        db.session.add(req)
        db.session.commit()

        flash('Your password reset request has been submitted. '
              'An admin will send you a temporary password via email shortly.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')