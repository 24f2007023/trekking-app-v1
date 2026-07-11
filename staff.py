from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app import db
from decorators import role_required
from models import Booking, StaffProfile, Trek, User

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


def _current_staff_profile():
    return StaffProfile.query.filter_by(user_id=session['user_id']).first()


@staff_bp.route('/dashboard')
@role_required('staff')
def dashboard():
    profile = _current_staff_profile()
    treks = Trek.query.filter_by(assigned_staff_id=profile.id).order_by(Trek.id).all()

    total_participants = 0
    open_treks = 0
    for trek in treks:
        total_participants += sum(1 for b in trek.bookings if b.status == 'Booked')
        if trek.status == 'Open':
            open_treks += 1

    return render_template(
        'staff/dashboard.html',
        treks=treks,
        total_participants=total_participants,
        open_treks=open_treks,
    )


@staff_bp.route('/treks/<int:trek_id>/manage', methods=['GET', 'POST'])
@role_required('staff')
def manage_trek(trek_id):
    profile = _current_staff_profile()
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != profile.id:
        flash('You are not assigned to manage this trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            status = request.form.get('status')
            if status not in ('Open', 'Closed'):
                flash('Invalid status.', 'danger')
                return redirect(url_for('staff.manage_trek', trek_id=trek.id))
            try:
                available_slots = int(request.form.get('available_slots', ''))
            except ValueError:
                flash('Available slots must be a number.', 'danger')
                return redirect(url_for('staff.manage_trek', trek_id=trek.id))
            if available_slots < 0:
                flash('Available slots cannot be negative.', 'danger')
                return redirect(url_for('staff.manage_trek', trek_id=trek.id))
            trek.available_slots = available_slots
            trek.status = status
            db.session.commit()
            flash('Trek updated.', 'success')

        elif action == 'mark_started':
            trek.status = 'Open'
            db.session.commit()
            flash('Trek marked as started.', 'success')

        elif action == 'mark_completed':
            trek.status = 'Completed'
            for booking in trek.bookings:
                if booking.status == 'Booked':
                    booking.status = 'Completed'
            db.session.commit()
            flash('Trek marked as completed.', 'success')

        return redirect(url_for('staff.manage_trek', trek_id=trek.id))

    participants = Booking.query.filter_by(trek_id=trek.id).join(User).order_by(Booking.booking_date.desc()).all()
    return render_template('staff/manage_trek.html', trek=trek, participants=participants)


@staff_bp.route('/profile', methods=['GET', 'POST'])
@role_required('staff')
def profile():
    profile = _current_staff_profile()
    user = profile.user

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact = request.form.get('contact', '').strip()

        if not name:
            flash('Name is required.', 'danger')
            return redirect(url_for('staff.profile'))

        user.name = name
        profile.contact = contact
        session['name'] = user.name
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('staff.profile'))

    return render_template('staff/profile.html', user=user, profile=profile)
