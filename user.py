from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app import db
from decorators import role_required
from models import Booking, Trek, User

user_bp = Blueprint('user', __name__, url_prefix='/user')

DIFFICULTIES = ['Easy', 'Moderate', 'Hard']


@user_bp.route('/dashboard')
@role_required('trekker')
def dashboard():
    q = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip()

    query = Trek.query.filter_by(status='Open')
    if q:
        query = query.filter(Trek.name.ilike(f'%{q}%'))
    if difficulty in DIFFICULTIES:
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))
    treks = query.order_by(Trek.id).all()

    my_booked_trek_ids = {
        b.trek_id for b in Booking.query.filter_by(user_id=session['user_id'], status='Booked').all()
    }

    return render_template(
        'user/dashboard.html',
        treks=treks,
        q=q,
        difficulty=difficulty,
        location=location,
        difficulties=DIFFICULTIES,
        my_booked_trek_ids=my_booked_trek_ids,
    )


@user_bp.route('/treks/<int:trek_id>/book', methods=['POST'])
@role_required('trekker')
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Open':
        flash('This trek is not open for booking.', 'danger')
        return redirect(url_for('user.dashboard'))

    if trek.available_slots <= 0:
        flash('No slots available for this trek.', 'danger')
        return redirect(url_for('user.dashboard'))

    existing = Booking.query.filter_by(user_id=session['user_id'], trek_id=trek.id, status='Booked').first()
    if existing:
        flash('You have already booked this trek.', 'danger')
        return redirect(url_for('user.dashboard'))

    booking = Booking(user_id=session['user_id'], trek_id=trek.id, status='Booked')
    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()
    flash('Trek booked successfully.', 'success')
    return redirect(url_for('user.dashboard'))


@user_bp.route('/bookings')
@role_required('trekker')
def bookings():
    bookings_list = Booking.query.filter_by(user_id=session['user_id']).order_by(Booking.booking_date.desc()).all()
    return render_template('user/bookings.html', bookings=bookings_list)


@user_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@role_required('trekker')
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session['user_id']:
        flash('You cannot cancel this booking.', 'danger')
        return redirect(url_for('user.bookings'))

    if booking.status != 'Booked':
        flash('Only booked trips can be cancelled.', 'danger')
        return redirect(url_for('user.bookings'))

    booking.status = 'Cancelled'
    booking.trek.available_slots += 1
    db.session.commit()
    flash('Booking cancelled.', 'success')
    return redirect(url_for('user.bookings'))


@user_bp.route('/profile', methods=['GET', 'POST'])
@role_required('trekker')
def profile():
    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Name is required.', 'danger')
            return redirect(url_for('user.profile'))

        user.name = name
        session['name'] = user.name
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html', user=user)
