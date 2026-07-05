from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from models import StaffProfile, User

auth_bp = Blueprint('auth', __name__)

DASHBOARD_ENDPOINT = {
    'admin': 'admin.dashboard',
    'staff': 'staff.dashboard',
    'trekker': 'user.dashboard',
}


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '')

        if role not in ('staff', 'trekker'):
            flash('Please select a valid role.', 'danger')
            return redirect(url_for('auth.register'))

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return redirect(url_for('auth.register'))

        user = User(name=name, email=email, password_hash=generate_password_hash(password), role=role)
        db.session.add(user)
        db.session.flush()

        if role == 'staff':
            db.session.add(StaffProfile(user_id=user.id, approval_status='Pending'))

        db.session.commit()

        if role == 'staff':
            flash('Registration successful. Please wait for admin approval before logging in.', 'success')
        else:
            flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        if user.is_blacklisted:
            flash('Your account has been blacklisted. Contact the admin.', 'danger')
            return redirect(url_for('auth.login'))

        if user.role == 'staff' and (not user.staff_profile or user.staff_profile.approval_status != 'Approved'):
            flash('Your staff account is awaiting admin approval.', 'warning')
            return redirect(url_for('auth.login'))

        session['user_id'] = user.id
        session['name'] = user.name
        session['role'] = user.role

        return redirect(url_for(DASHBOARD_ENDPOINT[user.role]))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
