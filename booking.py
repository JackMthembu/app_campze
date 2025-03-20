import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from forms import BookingOrderForm
from models import Camp, BookingForm
from extensions import db
from datetime import datetime
import paystack
from config import Config

booking_routes = Blueprint('booking_routes', __name__)

@booking_routes.route('/proceed-from-camp/<int:camp_id>')
@login_required
def proceed_from_camp(camp_id):
    camp = Camp.query.get_or_404(camp_id)
    form = BookingOrderForm()

    total_amount = camp.price_per_adult * form.adults.data + camp.price_per_child * form.children.data

    new_booking = BookingForm(
        user_id=current_user.id,
        camp_id=camp_id,
        check_in_date=camp.start_date,
        check_out_date=camp.end_date,
        adults=form.adults.data,
        children=form.children.data,
        status='pending',
        total_amount=total_amount,
        reference=reference
    )

    new_booking.calculate_total()
    # Generate a unique reference
    reference = str(uuid.uuid4())
    new_booking.reference = reference

    try:
        db.session.add(new_booking)
        db.session.commit()
        flash('Booking created successfully', 'success')
    except Exception as e:
        flash(f'An error occurred while creating your booking. Please try again. {e}', 'danger')
        return redirect(url_for('booking_routes.proceed_from_camp', camp_id=camp_id))

    return render_template('dashboard/booking_form.html', 
                         form=form, 
                         selected_camp=camp,
                         new_booking=new_booking)

@booking_routes.route('/callback', methods=['POST'])
def callback():
    pass

@booking_routes.route('/payment-success', methods=['GET'])
def payment_success():
    pass

@booking_routes.route('/payment-failed', methods=['GET'])
def payment_failed():
    pass

def create_paystack_reference():
    return str(uuid.uuid4())

def get_paystack_client():
    return paystack.Paystack(secret_key=Config.PAYSTACK_SECRET_KEY)

