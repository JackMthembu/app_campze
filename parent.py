from flask import Blueprint, app, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import GuardianForm
from models import db, User, Child, CampRegistration, Camp, BookingForm, Guardian, School, Country, State, Payment
from datetime import datetime
from sqlalchemy import desc
from flask import current_app
from flask import make_response
import pdfkit
from flask_mail import Message
from io import BytesIO
from extensions import mail

parent_routes = Blueprint('parent', __name__)

@parent_routes.route('/dashboard')
@login_required
def dashboard():
    if not current_user.guardian:
        flash('Please complete your guardian profile first.', 'warning')
        # TODO: Replace with the actual route for setting up guardian profile
        return redirect(url_for('parent.setup_profile'))
    
    children = Child.query.filter_by(guardian_id=current_user.guardian.id).all()
    # Get upcoming camps for all children of this guardian
    upcoming_camps = []
    for child in children:
        child_registrations = CampRegistration.query.filter_by(child_id=child.id).all()
        upcoming_camps.extend(child_registrations)

    return render_template('parent/dashboard.html', 
                         children=children,
                         upcoming_camps=upcoming_camps)

@parent_routes.route('/setup_profile', methods=['GET', 'POST'])
@login_required
def setup_profile():
    """Setup guardian profile - one guardian per user"""
    # Check if user already has a guardian profile
    existing_guardian = Guardian.query.filter_by(user_id=current_user.id).first()
    if existing_guardian:
        flash('You already have a guardian profile.', 'warning')
        return redirect(url_for('parent.dashboard'))
    
    form = GuardianForm()
    if form.validate_on_submit():
        try:
            # Double check to prevent race conditions
            if Guardian.query.filter_by(user_id=current_user.id).first():
                flash('Guardian profile already exists.', 'warning')
                return redirect(url_for('parent.dashboard'))

            # Create new guardian record
            guardian = Guardian(user_id=current_user.id)
            db.session.add(guardian)
            
            # Update user role if not already set
            if current_user.role != 'guardian':
                current_user.role = 'guardian'
            
            db.session.commit()
            flash('Guardian profile created successfully! You can now add your children.', 'success')
            return redirect(url_for('parent.add_child'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating guardian profile: {str(e)}', 'error')
            
    return render_template('parent/setup_profile.html', form=form)

@parent_routes.route('/children')
@login_required
def manage_children():
    """View and manage children profiles"""
    children = Child.query.filter_by(guardian_id=current_user.guardian.id).all()
    return render_template('parent/children.html', children=children)

@parent_routes.route('/camps')
@login_required
def view_camps():
    """View all camps (past, present, future) for children"""
    children = Child.query.filter_by(guardian_id=current_user.guardian.id).all()
    child_camps = {}
    for child in children:
        registrations = CampRegistration.query.filter_by(child_id=child.id).all()
        child_camps[child.id] = registrations
    return render_template('parent/camps.html', 
                         children=children,
                         child_camps=child_camps,
                         now=datetime.now())

@parent_routes.route('/payments')
@login_required
def payments():
    """View and manage payments for camps"""
    bookings = BookingForm.query.filter_by(user_id=current_user.id).order_by(desc(BookingForm.created_at)).all()
    return render_template('parent/payments.html', bookings=bookings)

@parent_routes.route('/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process a payment for camp registration"""
    try:
        # Get form data
        booking_id = request.form.get('booking_id')
        payment_method = request.form.get('payment_method')
        amount = request.form.get('amount')

        if not all([booking_id, payment_method, amount]):
            flash('Missing required payment information.', 'error')
            return redirect(url_for('parent.payments'))

        # Verify booking belongs to current user
        booking = BookingForm.query.get_or_404(booking_id)
        if booking.user_id != current_user.id:
            flash('Unauthorized payment attempt.', 'error')
            return redirect(url_for('parent.payments'))

        # Create payment record
        payment = Payment(
            booking_id=booking_id,
            amount=float(amount),
            payment_method=payment_method,
            status='pending',
            user_id=current_user.id
        )
        
        db.session.add(payment)
        
        # Update booking status
        booking.status = 'payment_pending'
        
        db.session.commit()
        
        # Here you would typically integrate with your payment gateway
        # For now, we'll just simulate a successful payment
        flash('Payment processed successfully!', 'success')
        return redirect(url_for('parent.payments'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error processing payment: {str(e)}', 'error')
        return redirect(url_for('parent.payments'))

@parent_routes.route('/statements')
@login_required
def statements():
    """View and download payment statements"""
    bookings = BookingForm.query.filter_by(user_id=current_user.id).order_by(desc(BookingForm.created_at)).all()
    return render_template('parent/statements.html', bookings=bookings)

@parent_routes.route('/download-statements', methods=['GET'])
@login_required
def download_statements():
    """Download payment statements as PDF"""
    try:
        # Get all bookings for the user
        bookings = BookingForm.query.filter_by(user_id=current_user.id).order_by(desc(BookingForm.created_at)).all()
        
        if not bookings:
            flash('No statements available for download.', 'info')
            return redirect(url_for('parent.statements'))

        # Create a PDF of the statements
        html_content = render_template(
            'parent/statement_pdf.html',
            bookings=bookings,
            user=current_user,
            date_generated=datetime.now()
        )
        
        # Convert HTML to PDF
        pdf = pdfkit.from_string(html_content, False)
        
        # Create the response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=statements_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response

    except Exception as e:
        app.logger.error(f"Error generating statements PDF: {str(e)}")
        flash('Error generating statements. Please try again later.', 'error')
        return redirect(url_for('parent.statements'))

@parent_routes.route('/email-statements', methods=['POST'])
@login_required
def email_statements():
    """Email payment statements to the user"""
    try:
        # Get all bookings for the user
        bookings = BookingForm.query.filter_by(user_id=current_user.id).order_by(desc(BookingForm.created_at)).all()
        
        if not bookings:
            return jsonify({
                'success': False,
                'message': 'No statements available to email.'
            }), 400

        # Generate PDF
        html_content = render_template(
            'parent/statement_pdf.html',
            bookings=bookings,
            user=current_user,
            date_generated=datetime.now()
        )
        
        pdf = pdfkit.from_string(html_content, False)
        
        # Send email with PDF attachment
        msg = Message(
            'Your Campze Payment Statements',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[current_user.email]
        )
        
        msg.body = f"""
        Dear {current_user.name},

        Please find attached your payment statements from Campze.
        
        Best regards,
        The Campze Team
        """
        
        msg.attach(
            f"statements_{datetime.now().strftime('%Y%m%d')}.pdf",
            'application/pdf',
            BytesIO(pdf).read()
        )
        
        mail.send(msg)
        
        return jsonify({
            'success': True,
            'message': 'Statements have been emailed to you successfully.'
        })

    except Exception as e:
        app.logger.error(f"Error emailing statements: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error sending statements. Please try again later.'
        }), 500

@parent_routes.route('/indemnity/<int:child_id>')
@login_required
def manage_indemnity(child_id):
    """Manage indemnity forms for a child"""
    child = Child.query.get_or_404(child_id)
    if child.guardian_id != current_user.guardian.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('parent.dashboard'))
    return render_template('parent/indemnity.html', child=child)

@parent_routes.route('/messages')
@login_required
def messages():
    """Messaging interface for communication"""
    children = Child.query.filter_by(guardian_id=current_user.guardian.id).all()
    return render_template('parent/messages.html', children=children)

# API endpoints for AJAX calls
@parent_routes.route('/api/update-indemnity', methods=['POST'])
@login_required
def update_indemnity():
    """Update indemnity form details"""
    data = request.get_json()
    child = Child.query.get_or_404(data['child_id'])
    if child.guardian_id != current_user.guardian.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Update child's indemnity information
    for key, value in data.items():
        if hasattr(child, key):
            setattr(child, key, value)
    
    db.session.commit()
    return jsonify({'message': 'Updated successfully'})

@parent_routes.route('/api/send-message', methods=['POST'])
@login_required
def send_message():
    """Send a message to camp organizer, teacher, or other parents"""
    data = request.get_json()
    # Message sending logic here
    return jsonify({'message': 'Sent successfully'})

@parent_routes.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Handle parent profile settings and security"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update contact information
            current_user.email = request.form.get('email')
            current_user.phone = request.form.get('phone')
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password changed successfully!', 'success')
        
        return redirect(url_for('parent.settings'))
        
    return render_template('parent/settings.html')

@parent_routes.route('/add_child', methods=['GET', 'POST'])
@login_required
def add_child():

    """Add a child to the guardian's profile"""
    if not current_user.guardian:
        flash('Please complete your guardian profile first.', 'warning')
        return redirect(url_for('parent.setup_profile'))

    if request.method == 'GET':
        schools = School.query.all()
        return render_template('parent/add_child.html', 
                             schools=schools,
                             google_api_key=current_app.config['GOOGLE_MAPS_API_KEY'])

    data = request.get_json()
    try:
        # Create new user for child
        child_user = User(
            name=data.get('name'),
            lastname=data.get('lastname'),
            username=f"{data.get('name').lower()}.{data.get('lastname').lower()}",
            email=data.get('email'),
            role='child',
            date_of_birth=datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d'),
            gender=data.get('gender'),
            school_id=data.get('school_id'),
            grade=data.get('grade')
        )
        db.session.add(child_user)
        db.session.flush()  # Get the user_id without committing

        # Create child record
        child = Child(
            user_id=child_user.id,
            guardian_id=current_user.guardian.id
        )
        db.session.add(child)
        db.session.commit()

        flash('Child added successfully!', 'success')
        return jsonify({
            'message': 'Child added successfully',
            'child_id': child.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@parent_routes.route('/add_school', methods=['POST'])
@login_required
def add_school():
    """Add a new school using Google Places data"""
    data = request.get_json()
    place_data = data.get('place_data', {})
    
    try:
        # Extract state and country from address components
        state_name = None
        country_name = None
        for component in place_data.get('address_components', []):
            if 'administrative_area_level_1' in component.get('types', []):
                state_name = component.get('long_name')
            elif 'country' in component.get('types', []):
                country_name = component.get('long_name')

        # Get or create country and state
        country = Country.query.filter_by(country=country_name).first()
        if not country:
            flash('Country not supported.', 'error')
            return jsonify({'error': 'Country not supported'}), 400

        state = State.query.filter_by(state=state_name, country_id=country.id).first()
        if not state:
            flash('State not supported.', 'error')
            return jsonify({'error': 'State not supported'}), 400

        # Create new school
        school = School(
            name=data.get('name'),
            address=data.get('address'),
            city=data.get('city'),
            state_id=state.id,
            country_id=country.id,
            longitude=float(data.get('longitude')),
            latitude=float(data.get('latitude')),
            phone_number=data.get('phone_number'),
            email=data.get('email')
        )
        
        db.session.add(school)
        db.session.commit()

        return jsonify({
            'message': 'School added successfully',
            'school': {
                'id': school.id,
                'name': school.name
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400 

@parent_routes.route('/cancel-registration', methods=['POST'])
@login_required
def cancel_registration():
    """Cancel a camp registration"""
    try:
        data = request.get_json()
        registration_id = data.get('registration_id')
        
        if not registration_id:
            return jsonify({'success': False, 'message': 'Registration ID is required'}), 400
            
        registration = CampRegistration.query.get_or_404(registration_id)
        
        # Check if the registration belongs to one of the parent's children
        children = Child.query.filter_by(guardian_id=current_user.guardian.id).all()
        child_ids = [child.id for child in children]
        
        if registration.child_id not in child_ids:
            return jsonify({'success': False, 'message': 'Unauthorized to cancel this registration'}), 403
            
        # Check if the camp hasn't started yet
        if registration.camp.start_date <= datetime.now().date():
            return jsonify({'success': False, 'message': 'Cannot cancel registration for a camp that has already started'}), 400
            
        # Cancel the registration
        db.session.delete(registration)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Camp registration cancelled successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error cancelling registration: {str(e)}'
        }), 500 

