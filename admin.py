from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from decorators import role_required
from models import Booking, StaffProfile, Trek, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

DIFFICULTIES = ['Easy', 'Moderate', 'Hard']
STATUSES = ['Pending', 'Approved', 'Open', 'Closed', 'Completed']


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%d').date()


def _validate_trek_form(form):
    required = ['name', 'location', 'difficulty', 'duration_days', 'available_slots', 'status']
    for field in required:
        if not form.get(field, '').strip():
            return 'Please fill in all required fields.'
    if form['difficulty'] not in DIFFICULTIES:
        return 'Invalid difficulty selected.'
    if form['status'] not in STATUSES:
        return 'Invalid status selected.'
    try:
        if int(form['duration_days']) <= 0 or int(form['available_slots']) < 0:
            return 'Duration must be positive and slots cannot be negative.'
    except ValueError:
        return 'Duration and slots must be numbers.'
    return None


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    return render_template(
        'admin/dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        recent_bookings=recent_bookings,
    )


@admin_bp.route('/treks')
@role_required('admin')
def treks():
    q = request.args.get('q', '').strip()
    query = Trek.query
    if q:
        query = query.filter(Trek.id == int(q)) if q.isdigit() else query.filter(Trek.name.ilike(f'%{q}%'))
    treks_list = query.order_by(Trek.id).all()
    return render_template('admin/treks.html', treks=treks_list, q=q)


@admin_bp.route('/treks/new', methods=['GET', 'POST'])
@role_required('admin')
def trek_new():
    staff_options = StaffProfile.query.filter_by(approval_status='Approved').all()
    if request.method == 'POST':
        error = _validate_trek_form(request.form)
        if error:
            flash(error, 'danger')
            return redirect(url_for('admin.trek_new'))

        trek = Trek(
            name=request.form['name'].strip(),
            location=request.form['location'].strip(),
            difficulty=request.form['difficulty'],
            duration_days=int(request.form['duration_days']),
            available_slots=int(request.form['available_slots']),
            assigned_staff_id=int(request.form['assigned_staff_id']) if request.form.get('assigned_staff_id') else None,
            status=request.form['status'],
            start_date=_parse_date(request.form.get('start_date')),
            end_date=_parse_date(request.form.get('end_date')),
            description=request.form.get('description', '').strip(),
        )
        db.session.add(trek)
        db.session.commit()
        flash('Trek created successfully.', 'success')
        return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', trek=None, staff_options=staff_options,
                            difficulties=DIFFICULTIES, statuses=STATUSES)


@admin_bp.route('/treks/<int:trek_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def trek_edit(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_options = StaffProfile.query.filter_by(approval_status='Approved').all()
    if request.method == 'POST':
        error = _validate_trek_form(request.form)
        if error:
            flash(error, 'danger')
            return redirect(url_for('admin.trek_edit', trek_id=trek_id))

        trek.name = request.form['name'].strip()
        trek.location = request.form['location'].strip()
        trek.difficulty = request.form['difficulty']
        trek.duration_days = int(request.form['duration_days'])
        trek.available_slots = int(request.form['available_slots'])
        trek.assigned_staff_id = int(request.form['assigned_staff_id']) if request.form.get('assigned_staff_id') else None
        trek.status = request.form['status']
        trek.start_date = _parse_date(request.form.get('start_date'))
        trek.end_date = _parse_date(request.form.get('end_date'))
        trek.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('Trek updated successfully.', 'success')
        return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', trek=trek, staff_options=staff_options,
                            difficulties=DIFFICULTIES, statuses=STATUSES)


@admin_bp.route('/treks/<int:trek_id>/delete', methods=['POST'])
@role_required('admin')
def trek_delete(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash('Trek removed.', 'success')
    return redirect(url_for('admin.treks'))


@admin_bp.route('/staff')
@role_required('admin')
def staff():
    tab = request.args.get('tab', 'pending')
    q = request.args.get('q', '').strip()
    status_map = {'pending': 'Pending', 'approved': 'Approved', 'blacklisted': 'Blacklisted'}
    status = status_map.get(tab, 'Pending')

    query = StaffProfile.query.join(User).filter(StaffProfile.approval_status == status)
    if q:
        query = query.filter(StaffProfile.id == int(q)) if q.isdigit() else query.filter(User.name.ilike(f'%{q}%'))
    profiles = query.all()

    counts = {
        'pending': StaffProfile.query.filter_by(approval_status='Pending').count(),
        'approved': StaffProfile.query.filter_by(approval_status='Approved').count(),
        'blacklisted': StaffProfile.query.filter_by(approval_status='Blacklisted').count(),
    }
    return render_template('admin/staff.html', profiles=profiles, tab=tab, q=q, counts=counts)


@admin_bp.route('/staff/<int:profile_id>/approve', methods=['POST'])
@role_required('admin')
def staff_approve(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    profile.approval_status = 'Approved'
    db.session.commit()
    flash('Staff approved.', 'success')
    return redirect(url_for('admin.staff', tab='pending'))


@admin_bp.route('/staff/<int:profile_id>/reject', methods=['POST'])
@role_required('admin')
def staff_reject(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    user = profile.user
    db.session.delete(profile)
    db.session.delete(user)
    db.session.commit()
    flash('Staff request rejected.', 'success')
    return redirect(url_for('admin.staff', tab='pending'))


@admin_bp.route('/staff/<int:profile_id>/blacklist', methods=['POST'])
@role_required('admin')
def staff_blacklist(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    profile.approval_status = 'Blacklisted'
    db.session.commit()
    flash('Staff blacklisted.', 'success')
    return redirect(url_for('admin.staff', tab='blacklisted'))


@admin_bp.route('/staff/<int:profile_id>/unblacklist', methods=['POST'])
@role_required('admin')
def staff_unblacklist(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    profile.approval_status = 'Approved'
    db.session.commit()
    flash('Staff reinstated.', 'success')
    return redirect(url_for('admin.staff', tab='approved'))


@admin_bp.route('/users')
@role_required('admin')
def users():
    q = request.args.get('q', '').strip()
    query = User.query.filter_by(role='trekker')
    if q:
        query = query.filter(User.id == int(q)) if q.isdigit() else query.filter(User.name.ilike(f'%{q}%'))
    users_list = query.order_by(User.id).all()
    return render_template('admin/users.html', users=users_list, q=q)


@admin_bp.route('/users/<int:user_id>/blacklist', methods=['POST'])
@role_required('admin')
def user_blacklist(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = True
    db.session.commit()
    flash('User blacklisted.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/unblacklist', methods=['POST'])
@role_required('admin')
def user_unblacklist(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = False
    db.session.commit()
    flash('User reinstated.', 'success')
    return redirect(url_for('admin.users'))


BOOKING_STATUSES = ['Booked', 'Cancelled', 'Completed']


@admin_bp.route('/bookings')
@role_required('admin')
def bookings():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()

    query = Booking.query.join(User).join(Trek)
    if q:
        query = query.filter(db.or_(User.name.ilike(f'%{q}%'), Trek.name.ilike(f'%{q}%')))
    if status in BOOKING_STATUSES:
        query = query.filter(Booking.status == status)
    bookings_list = query.order_by(Booking.booking_date.desc()).all()

    return render_template('admin/bookings.html', bookings=bookings_list, q=q, status=status,
                            statuses=BOOKING_STATUSES)
