from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Camp, CampRegistration, Payment, BankingDetails, Message, Teacher, Company
from forms import CampForm, BankDetailsForm, MessageForm
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from functools import wraps

organiser = Blueprint('organiser', __name__)

# Ensure user is an organiser
def organiser_required(f):
    @wraps(f)  # This preserves the original function's metadata
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'organiser':
            flash('Access denied. Organiser privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@organiser.route('/dashboard')
@organiser_required
def dashboard():
    # Get summary statistics for camps where user is either teacher or organiser
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if teacher:
        camps = Camp.query.filter(
            (Camp.teacher_id == teacher.id) | (Camp.organiser_id == current_user.id)
        ).all()
    else:
        camps = Camp.query.filter_by(organiser_id=current_user.id).all()

    total_registrations = sum(len(camp.registrations) for camp in camps)
    total_revenue = sum(payment.amount for camp in camps 
                       for registration in camp.registrations 
                       for payment in registration.payments)
    
    # Fix the query for recent registrations
    if teacher:
        recent_registrations = CampRegistration.query.join(Camp).filter(
            (Camp.teacher_id == teacher.id) | (Camp.organiser_id == current_user.id)
        ).order_by(CampRegistration.created_at.desc()).limit(5).all()
    else:
        recent_registrations = CampRegistration.query.join(Camp).filter(
            Camp.organiser_id == current_user.id
        ).order_by(CampRegistration.created_at.desc()).limit(5).all()

    return render_template('organiser/dashboard.html',
                         camps=camps,
                         total_registrations=total_registrations,
                         total_revenue=total_revenue,
                         recent_registrations=recent_registrations)

@organiser.route('/camps')
@organiser_required
def camps():
    # Get camps where user is either teacher or organiser
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if teacher:
        camps = Camp.query.filter(
            (Camp.teacher_id == teacher.id) | (Camp.organiser_id == current_user.id)
        ).all()
    else:
        camps = Camp.query.filter_by(organiser_id=current_user.id).all()
    return render_template('organiser/camps.html', camps=camps)

@organiser.route('/camp/create', methods=['GET', 'POST'])
@organiser_required
def create_camp():
    form = CampForm()
    if form.validate_on_submit():
        # Get or create teacher record for current user
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher:
            teacher = Teacher(user_id=current_user.id)
            db.session.add(teacher)
            db.session.flush()  # This will assign an ID to the teacher

        # Calculate nights if not provided
        nights = form.nights.data
        if not nights and form.start_date.data and form.end_date.data:
            nights = (form.end_date.data - form.start_date.data).days

        camp = Camp(
            name=form.name.data,
            description=form.description.data,
            camp_objectives=form.camp_objectives.data,
            location=form.location.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            nights=nights,
            price_per_adult=form.price_per_adult.data,
            price_per_child=form.price_per_child.data,
            capacity=form.capacity.data,
            age_range_min=form.age_range_min.data,
            age_range_max=form.age_range_max.data,
            teacher_id=teacher.id,
            organiser_id=current_user.id,
            camp_status=form.camp_status.data,
            camp_type=form.camp_type.data,
            camp_category=form.camp_category.data
        )
        
        if form.camp_image.data:
            file = form.camp_image.data
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/uploads/camps', filename))
            camp.camp_image = filename
        
        try:
            db.session.add(camp)
            db.session.commit()
            flash('Camp created successfully!', 'success')
            return redirect(url_for('organiser.camps'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating camp: {str(e)}', 'error')
            return render_template('organiser/create_camp.html', form=form)
    
    return render_template('organiser/create_camp.html', form=form)

@organiser.route('/camp/<int:camp_id>/edit', methods=['GET', 'POST'])
@organiser_required
def edit_camp(camp_id):
    camp = Camp.query.get_or_404(camp_id)
    # Check if user is either the teacher or organiser of the camp
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher or (camp.teacher_id != teacher.id and camp.organiser_id != current_user.id):
        flash('Access denied.', 'danger')
        return redirect(url_for('organiser.camps'))
    
    form = CampForm(obj=camp)
    if form.validate_on_submit():
        camp.name = form.name.data
        camp.description = form.description.data
        camp.location = form.location.data
        camp.start_date = form.start_date.data
        camp.end_date = form.end_date.data
        camp.price_per_adult = form.price_per_adult.data
        camp.price_per_child = form.price_per_child.data
        camp.capacity = form.capacity.data
        camp.age_range_min = form.age_range_min.data
        camp.age_range_max = form.age_range_max.data
        
        if form.camp_image.data:
            file = form.camp_image.data
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/uploads/camps', filename))
            camp.camp_image = filename

        db.session.commit()
        flash('Camp updated successfully!', 'success')
        return redirect(url_for('organiser.camps'))
    
    return render_template('organiser/edit_camp.html', form=form, camp=camp)

@organiser.route('/camp/<int:camp_id>/registrations')
@organiser_required
def camp_registrations(camp_id):
    if not camp_id:
        flash('Invalid camp ID', 'danger')
        return redirect(url_for('organiser.camps'))

    camp = Camp.query.get_or_404(camp_id)
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Check if user is either the teacher or organiser of the camp
    if not teacher or (camp.teacher_id != teacher.id and camp.organiser_id != current_user.id):
        flash('Access denied.', 'danger')
        return redirect(url_for('organiser.camps'))
    
    registrations = CampRegistration.query.filter_by(camp_id=camp_id).all()
    return render_template('organiser/registrations.html', camp=camp, registrations=registrations)

@organiser.route('/banking', methods=['GET', 'POST'])
@organiser_required
def banking():
    bank_details = BankingDetails.query.filter_by(user_id=current_user.id).first()
    form = BankDetailsForm(obj=bank_details)
    
    if form.validate_on_submit():
        if not bank_details:
            bank_details = BankingDetails(user_id=current_user.id)
        
        bank_details.bank_name = form.bank_name.data
        bank_details.account_holder = form.account_holder.data
        bank_details.account_number = form.account_number.data
        bank_details.branch_code = form.branch_code.data
        bank_details.account_type = form.account_type.data
        
        db.session.add(bank_details)
        db.session.commit()
        flash('Banking details updated successfully!', 'success')
        return redirect(url_for('organiser.banking'))
    
    return render_template('organiser/banking.html', form=form, bank_details=bank_details)

@organiser.route('/payouts')
@organiser_required
def payouts():
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if teacher:
        payments = Payment.query.join(CampRegistration).join(Camp).filter(
            (Camp.teacher_id == teacher.id) | (Camp.organiser_id == current_user.id)
        ).order_by(Payment.created_at.desc()).all()
    else:
        payments = Payment.query.join(CampRegistration).join(Camp).filter(
            Camp.organiser_id == current_user.id
        ).order_by(Payment.created_at.desc()).all()
    
    return render_template('organiser/payouts.html', payments=payments)

@organiser.route('/messages')
@organiser_required
def messages():
    camp_id = request.args.get('camp_id', type=int)
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    if teacher:
        camps = Camp.query.filter(
            (Camp.teacher_id == teacher.id) | (Camp.organiser_id == current_user.id)
        ).all()
    else:
        camps = Camp.query.filter_by(organiser_id=current_user.id).all()
    
    if camp_id:
        messages = Message.query.filter_by(camp_id=camp_id).order_by(Message.created_at.desc()).all()
    else:
        if teacher:
            messages = Message.query.join(Camp).filter(
                (Camp.teacher_id == teacher.id) | (Camp.organiser_id == current_user.id)
            ).order_by(Message.created_at.desc()).all()
        else:
            messages = Message.query.join(Camp).filter(
                Camp.organiser_id == current_user.id
            ).order_by(Message.created_at.desc()).all()
    
    return render_template('organiser/messages.html', messages=messages, camps=camps)

@organiser.route('/send_message', methods=['POST'])
@organiser_required
def send_message():
    form = MessageForm()
    if form.validate_on_submit():
        camp = Camp.query.get_or_404(form.camp_id.data)
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        
        # Check if user is either the teacher or organiser of the camp
        if not teacher or (camp.teacher_id != teacher.id and camp.organiser_id != current_user.id):
            return jsonify({'success': False, 'message': 'Access denied'})
        
        message = Message(
            sender_id=current_user.id,
            camp_id=form.camp_id.data,
            recipient_id=form.recipient_id.data,
            subject=form.subject.data,
            content=form.content.data,
            created_at=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'errors': form.errors})

@organiser.route('/camp/<int:camp_id>/stats')
@organiser_required
def camp_stats(camp_id):
    if not camp_id:
        return jsonify({'success': False, 'message': 'Invalid camp ID'})

    camp = Camp.query.get_or_404(camp_id)
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Check if user is either the teacher or organiser of the camp
    if not teacher or (camp.teacher_id != teacher.id and camp.organiser_id != current_user.id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    total_registrations = len(camp.registrations)
    total_revenue = sum(payment.amount for registration in camp.registrations 
                       for payment in registration.payments)
    available_spots = camp.capacity - total_registrations
    
    return jsonify({
        'success': True,
        'stats': {
            'total_registrations': total_registrations,
            'total_revenue': total_revenue,
            'available_spots': available_spots,
            'occupancy_rate': (total_registrations / camp.capacity) * 100 if camp.capacity > 0 else 0
        }
    })

@organiser.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Handle organiser profile settings and security"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update contact information
            current_user.email = request.form.get('email')
            current_user.phone_number = request.form.get('phone')
            
            # Update company information
            if current_user.company:
                current_user.company.company_name = request.form.get('company_name')
            else:
                company = Company(
                    company_name=request.form.get('company_name'),
                    company_registration_number='TBD',  # These can be updated later
                    tax_number='TBD'
                )
                db.session.add(company)
                current_user.company = company
            
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
                current_user.password = new_password
                db.session.commit()
                flash('Password changed successfully!', 'success')
        
        return redirect(url_for('organiser.settings'))
        
    return render_template('organiser/settings.html') 