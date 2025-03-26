from flask import Blueprint, app, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import BankingDetails, Company, db, Camp, CampPackage, TourOperator, BookingForm, Country, User, School, Banks
from forms import BankDetailsForm, CampPackageForm, ProfileForm, PasswordForm, CompanyForm, BankingDetailsForm
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.exc import SQLAlchemyError
import json

tour_operator = Blueprint('tour_operator', __name__)

def is_tour_operator():
    """Check if current user is a tour operator"""
    if not current_user.tour_operator:
        flash('Access denied. You must be a tour operator.', 'danger')
        return False
    return True

@tour_operator.route('/dashboard')
@login_required
def dashboard():
    if not is_tour_operator():
        return redirect(url_for('main.index'))
    
    # Get tour operator's packages
    packages = CampPackage.query.filter_by(tour_operator_id=current_user.tour_operator.id).all()
    
    # Calculate statistics
    stats = {
        'total_packages': len(packages),
        'total_bookings': BookingForm.query.join(
            CampPackage, BookingForm.package_id == CampPackage.id
        ).filter(
            CampPackage.tour_operator_id == current_user.tour_operator.id,
            BookingForm.status == 'booked'
        ).count(),
        'total_revenue': db.session.query(func.sum(BookingForm.total_amount)).join(
            CampPackage, BookingForm.package_id == CampPackage.id
        ).filter(
            CampPackage.tour_operator_id == current_user.tour_operator.id,
            BookingForm.status == 'booked'
        ).scalar() or 0,
        'total_students': db.session.query(func.sum(BookingForm.children)).join(
            CampPackage, BookingForm.package_id == CampPackage.id
        ).filter(
            CampPackage.tour_operator_id == current_user.tour_operator.id,
            BookingForm.status == 'booked'
        ).scalar() or 0
    }
    
    # Get recent bookings
    recent_bookings = BookingForm.query.join(
        CampPackage, BookingForm.package_id == CampPackage.id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id,
        BookingForm.status == 'booked'
    ).order_by(
        BookingForm.created_at.desc()
    ).limit(5).all()
    
    # Format recent bookings for template
    formatted_bookings = []
    for booking in recent_bookings:
        formatted_bookings.append({
            'school_name': booking.user.school.name if booking.user.school else 'N/A',
            'package_name': booking.package.name if booking.package else 'N/A',
            'students': booking.children,
            'date': booking.created_at,
            'status': booking.status,
            'status_color': 'success' if booking.status == 'booked' else 'warning' if booking.status == 'pending' else 'danger',
            'amount': float(booking.total_amount)
        })
    
    # Get popular packages
    popular_packages = db.session.query(
        CampPackage.id,
        CampPackage.name,
        func.count(BookingForm.id).label('booking_count'),
        func.sum(BookingForm.total_amount).label('total_revenue')
    ).join(
        BookingForm, CampPackage.id == BookingForm.package_id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id,
        BookingForm.status == 'booked'
    ).group_by(
        CampPackage.id,
        CampPackage.name
    ).order_by(
        desc('booking_count')
    ).limit(5).all()
    
    # Format popular packages for template
    formatted_packages = []
    for package_id, package_name, bookings, revenue in popular_packages:
        # Calculate growth (placeholder - you might want to implement actual growth calculation)
        growth = 0  # This should be calculated based on your business logic
        
        formatted_packages.append({
            'name': package_name,
            'bookings': bookings,
            'revenue': float(revenue or 0),
            'growth': growth
        })
    
    # Get upcoming events (bookings)
    upcoming_events = BookingForm.query.join(
        CampPackage, BookingForm.package_id == CampPackage.id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id,
        BookingForm.check_in_date >= datetime.utcnow().date(),
        BookingForm.status == 'booked'
    ).order_by(
        BookingForm.check_in_date
    ).limit(5).all()
    
    # Format upcoming events for template
    formatted_events = []
    for event in upcoming_events:
        formatted_events.append({
            'name': f"{event.package.name if event.package else 'N/A'} - {event.user.school.name if event.user.school else 'N/A'}",
            'date': event.check_in_date,
            'status': event.status,
            'status_color': 'success' if event.status == 'booked' else 'warning' if event.status == 'pending' else 'danger'
        })
    
    # Get initial revenue data for chart (weekly)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    revenue_data = db.session.query(
        func.format(func.cast(BookingForm.created_at, db.Date), 'yyyy-MM-dd').label('date'),
        func.sum(BookingForm.total_amount).label('revenue')
    ).join(
        CampPackage, BookingForm.package_id == CampPackage.id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id,
        BookingForm.status == 'booked',
        BookingForm.created_at.between(start_date, end_date)
    ).group_by(
        func.cast(BookingForm.created_at, db.Date)
    ).order_by(
        func.cast(BookingForm.created_at, db.Date)
    ).all()
    
    # Format revenue data for chart
    labels = []
    values = []
    for date, revenue in revenue_data:
        labels.append(str(date))
        values.append(float(revenue or 0))
    
    # Create JSON-serializable data structure
    chart_data = {
        'labels': labels,
        'values': values
    }
    
    # Convert to JSON string to ensure serialization
    chart_data = json.dumps(chart_data)
    
    return render_template('tour_operator/dashboard.html',
                         stats=stats,
                         recent_bookings=formatted_bookings,
                         popular_packages=formatted_packages,
                         upcoming_events=formatted_events,
                         revenue_data=chart_data)

@tour_operator.route('/revenue-data')
@login_required
def get_revenue_data():
    if not is_tour_operator():
        return jsonify({'error': 'Access denied'}), 403
    
    period = request.args.get('period', 'weekly')
    
    # Get the date range based on period
    end_date = datetime.utcnow()
    if period == 'weekly':
        start_date = end_date - timedelta(days=7)
        date_format = 'yyyy-MM-dd'
    elif period == 'monthly':
        start_date = end_date - timedelta(days=30)
        date_format = 'yyyy-MM-dd'
    else:  # yearly
        start_date = end_date - timedelta(days=365)
        date_format = 'yyyy-MM'
    
    # Query revenue data using SQL Server's date functions
    revenue_data = db.session.query(
        func.format(func.cast(BookingForm.created_at, db.Date), date_format).label('date'),
        func.sum(BookingForm.total_amount).label('revenue')
    ).join(
        CampPackage, BookingForm.package_id == CampPackage.id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id,
        BookingForm.status == 'booked',
        BookingForm.created_at.between(start_date, end_date)
    ).group_by(
        func.cast(BookingForm.created_at, db.Date)
    ).order_by(
        func.cast(BookingForm.created_at, db.Date)
    ).all()
    
    # Format data for chart
    labels = []
    values = []
    for date, revenue in revenue_data:
        labels.append(date)
        values.append(float(revenue or 0))
    
    return jsonify({
        'labels': labels,
        'values': values
    })

@tour_operator.route('/packages')
@login_required
def list_packages():
    if not is_tour_operator():
        return redirect(url_for('main.index'))
    
    packages = CampPackage.query.join(TourOperator).filter(
        TourOperator.user_id == current_user.id
    ).order_by(CampPackage.created_at.desc()).all()
    
    return render_template('tour_operator/packages.html', packages=packages)

@tour_operator.route('/packages/new', methods=['GET', 'POST'])
@login_required
def create_package():
    if not is_tour_operator():
        return redirect(url_for('main.index'))
    
    form = CampPackageForm()
    # Get camps associated with the tour operator's company
    form.camp_id.choices = [(c.id, c.name) for c in Camp.query.filter_by(
        organiser_id=current_user.id
    ).order_by(Camp.name).all()]
    
    if form.validate_on_submit():
        try:
            package = CampPackage(
                camp_id=form.camp_id.data,
                tour_operator_id=current_user.tour_operator.id,
                name=form.name.data,
                description=form.description.data,
                min_students=form.min_students.data,
                max_students=form.max_students.data,
                price_per_student=form.price_per_student.data,
                price_per_teacher=form.price_per_teacher.data,
                duration_days=form.duration_days.data,
                included_activities=form.included_activities.data,
                requirements=form.requirements.data,
                status=form.status.data
            )
            db.session.add(package)
            db.session.commit()
            flash('Camp package created successfully!', 'success')
            return redirect(url_for('tour_operator.list_packages'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Error creating camp package. Please try again.', 'danger')
            app.logger.error(f"Error creating camp package: {str(e)}")
    
    return render_template('tour_operator/package_form.html', form=form, is_edit=False)

@tour_operator.route('/packages/<int:package_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_package(package_id):
    if not is_tour_operator():
        return redirect(url_for('main.index'))
    
    package = CampPackage.query.get_or_404(package_id)
    # Verify ownership
    if package.tour_operator.user_id != current_user.id:
        flash('Access denied. You can only edit your own packages.', 'danger')
        return redirect(url_for('tour_operator.list_packages'))
    
    form = CampPackageForm(obj=package)
    form.camp_id.choices = [(c.id, c.name) for c in Camp.query.filter_by(
        organiser_id=current_user.id
    ).order_by(Camp.name).all()]
    
    if form.validate_on_submit():
        try:
            form.populate_obj(package)
            db.session.commit()
            flash('Camp package updated successfully!', 'success')
            return redirect(url_for('tour_operator.list_packages'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Error updating camp package. Please try again.', 'danger')
            app.logger.error(f"Error updating camp package: {str(e)}")
    
    return render_template('tour_operator/package_form.html', form=form, is_edit=True)

@tour_operator.route('/packages/<int:package_id>/delete', methods=['POST'])
@login_required
def delete_package(package_id):
    if not is_tour_operator():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    package = CampPackage.query.get_or_404(package_id)
    if package.tour_operator.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        db.session.delete(package)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Package deleted successfully'})
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Error deleting camp package: {str(e)}")
        return jsonify({'success': False, 'message': 'Error deleting package'}), 500

@tour_operator.route('/packages/<int:package_id>')
def view_package(package_id):
    package = CampPackage.query.get_or_404(package_id)
    return render_template('tour_operator/package_detail.html', package=package)

@tour_operator.route('/banking', methods=['GET', 'POST'])
@login_required
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
        return redirect(url_for('tour_operator.banking'))
    
    return render_template('tour_operator/banking.html', form=form, bank_details=bank_details)

@tour_operator.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not is_tour_operator():
        return redirect(url_for('main.index'))
    
    # Get the active tab from query parameters, default to 'profile'
    active_tab = request.args.get('tab', 'profile')
    
    # Get user's company
    company = current_user.tour_operator.company if current_user.tour_operator else None
    
    # Get user's banking details
    bank_details = BankingDetails.query.filter_by(user_id=current_user.id).first()
    
    # Get all countries for the dropdown - only select existing columns
    countries = db.session.query(Country.id, Country.country).order_by(Country.country).all()
    
    # Get all banks for the dropdown
    banks = Banks.query.order_by(Banks.bank_name).all()
    
    # Initialize forms with current user data
    profile_form = ProfileForm(current_user=current_user)
    profile_form.name.data = current_user.name
    profile_form.lastname.data = current_user.lastname
    profile_form.email.data = current_user.email
    profile_form.phone_number.data = current_user.phone_number
    profile_form.date_of_birth.data = current_user.date_of_birth
    profile_form.gender.data = current_user.gender
    profile_form.country_id.data = current_user.country_id
    
    # Get currency from country if country is set
    if current_user.country_id:
        country = Country.query.get(current_user.country_id)
        if country:
            profile_form.currency_id.data = country.currency_id
    
    password_form = PasswordForm()
    company_form = CompanyForm(obj=company)
    banking_form = BankingDetailsForm(obj=bank_details)
    
    # Set choices for forms
    profile_form.country_id.choices = [(c.id, c.country) for c in countries]
    banking_form.bank_id.choices = [(b.id, b.bank_name) for b in banks]
    
    if request.method == 'POST':
        if active_tab == 'profile' and profile_form.validate_on_submit():
            try:
                # Update user profile
                current_user.name = profile_form.name.data
                current_user.lastname = profile_form.lastname.data
                current_user.email = profile_form.email.data
                current_user.phone_number = profile_form.phone_number.data
                current_user.date_of_birth = profile_form.date_of_birth.data
                current_user.gender = profile_form.gender.data
                
                # Only update country if it hasn't been set before
                if not current_user.country_id:
                    current_user.country_id = profile_form.country_id.data
                    # Get the currency_id from the selected country
                    country = Country.query.get(profile_form.country_id.data)
                    if country:
                        current_user.currency_id = country.currency_id
                
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating profile: {str(e)}', 'error')
                
        elif active_tab == 'password' and password_form.validate_on_submit():
            try:
                if current_user.check_password(password_form.current_password.data):
                    current_user.set_password(password_form.new_password.data)
                    db.session.commit()
                    flash('Password updated successfully!', 'success')
                else:
                    flash('Current password is incorrect.', 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating password: {str(e)}', 'error')
                
        elif active_tab == 'company' and company_form.validate_on_submit():
            try:
                if not company:
                    company = Company(user_id=current_user.id)
                    db.session.add(company)
                
                company.company_name = company_form.company_name.data
                company.company_registration_number = company_form.company_registration_number.data
                company.tax_number = company_form.tax_number.data
                
                db.session.commit()
                flash('Company details updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating company details: {str(e)}', 'error')
                
        elif active_tab == 'banking' and banking_form.validate_on_submit():
            try:
                if not bank_details:
                    bank_details = BankingDetails(user_id=current_user.id)
                    db.session.add(bank_details)
                
                bank_details.bank_id = banking_form.bank_id.data
                bank_details.account_number = banking_form.account_number.data
                bank_details.account_holder_name = banking_form.account_holder_name.data
                bank_details.account_type = banking_form.account_type.data
                bank_details.branch = banking_form.branch.data
                bank_details.branch_code = banking_form.branch_code.data
                bank_details.account_iban = banking_form.account_iban.data
                
                db.session.commit()
                flash('Banking details updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating banking details: {str(e)}', 'error')
    
    return render_template('tour_operator/settings.html',
                         active_tab=active_tab,
                         profile_form=profile_form,
                         password_form=password_form,
                         company_form=company_form,
                         banking_form=banking_form,
                         company=company,
                         bank_details=bank_details,
                         countries=countries,
                         banks=banks)

@tour_operator.route('/bookings')
@login_required
def bookings():
    if not is_tour_operator():
        return redirect(url_for('main.index'))
    
    # Get all bookings for the tour operator with related information
    bookings = BookingForm.query.join(
        CampPackage, BookingForm.package_id == CampPackage.id
    ).join(
        User, BookingForm.user_id == User.id
    ).join(
        School, User.school_id == School.id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id
    ).order_by(
        BookingForm.created_at.desc()
    ).all()

    # Format bookings for template
    formatted_bookings = []
    for booking in bookings:
        formatted_bookings.append({
            'id': booking.id,
            'school_name': booking.user.school.name if booking.user.school else 'N/A',
            'package_name': booking.package.name if booking.package else 'N/A',
            'students': booking.children,
            'teachers': booking.teachers,
            'check_in_date': booking.check_in_date,
            'check_out_date': booking.check_out_date,
            'total_amount': float(booking.total_amount),
            'status': booking.status,
            'status_color': 'success' if booking.status == 'booked' else 'warning' if booking.status == 'pending' else 'danger',
            'created_at': booking.created_at,
            'contact_name': f"{booking.user.name} {booking.user.lastname}",
            'contact_email': booking.user.email,
            'contact_phone': booking.user.phone_number,
            'special_requirements': booking.special_requirements,
            'included_activities': booking.package.included_activities if booking.package else '',
            'requirements': booking.package.requirements if booking.package else ''
        })

    return render_template('tour_operator/bookings.html', bookings=formatted_bookings)

@tour_operator.route('/analytics')
@login_required
def analytics():
    if not is_tour_operator():
        return redirect(url_for('main.index'))
    
    # Get date range for analytics (last 12 months)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    
    # Monthly booking statistics
    monthly_stats = db.session.query(
        func.format(func.cast(BookingForm.created_at, db.Date), 'yyyy-MM').label('month'),
        func.count(BookingForm.id).label('total_bookings'),
        func.sum(BookingForm.total_amount).label('total_revenue'),
        func.sum(BookingForm.children).label('total_students')
    ).join(
        CampPackage, BookingForm.package_id == CampPackage.id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id,
        BookingForm.created_at.between(start_date, end_date)
    ).group_by(
        func.format(func.cast(BookingForm.created_at, db.Date), 'yyyy-MM')
    ).order_by(
        func.format(func.cast(BookingForm.created_at, db.Date), 'yyyy-MM')
    ).all()
    
    # Package performance statistics
    package_stats = db.session.query(
        CampPackage.name,
        func.count(BookingForm.id).label('booking_count'),
        func.sum(BookingForm.total_amount).label('total_revenue'),
        func.sum(BookingForm.children).label('total_students'),
        func.avg(BookingForm.total_amount).label('avg_revenue')
    ).join(
        BookingForm, CampPackage.id == BookingForm.package_id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id,
        BookingForm.created_at.between(start_date, end_date)
    ).group_by(
        CampPackage.name
    ).order_by(
        desc('total_revenue')
    ).all()
    
    # Status distribution
    status_distribution = db.session.query(
        BookingForm.status,
        func.count(BookingForm.id).label('count')
    ).join(
        CampPackage, BookingForm.package_id == CampPackage.id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id,
        BookingForm.created_at.between(start_date, end_date)
    ).group_by(
        BookingForm.status
    ).all()
    
    # Peak booking months
    peak_months = db.session.query(
        func.format(func.cast(BookingForm.check_in_date, db.Date), 'yyyy-MM').label('month'),
        func.count(BookingForm.id).label('booking_count')
    ).join(
        CampPackage, BookingForm.package_id == CampPackage.id
    ).filter(
        CampPackage.tour_operator_id == current_user.tour_operator.id,
        BookingForm.created_at.between(start_date, end_date)
    ).group_by(
        func.format(func.cast(BookingForm.check_in_date, db.Date), 'yyyy-MM')
    ).order_by(
        desc('booking_count')
    ).limit(5).all()
    
    # Format data for charts
    monthly_data = {
        'labels': [stat.month for stat in monthly_stats],
        'bookings': [stat.total_bookings for stat in monthly_stats],
        'revenue': [float(stat.total_revenue or 0) for stat in monthly_stats],
        'students': [stat.total_students for stat in monthly_stats]
    }
    
    package_data = {
        'labels': [stat.name for stat in package_stats],
        'bookings': [stat.booking_count for stat in package_stats],
        'revenue': [float(stat.total_revenue or 0) for stat in package_stats],
        'students': [stat.total_students for stat in package_stats],
        'avg_revenue': [float(stat.avg_revenue or 0) for stat in package_stats]
    }
    
    status_data = {
        'labels': [stat.status for stat in status_distribution],
        'values': [stat.count for stat in status_distribution]
    }
    
    peak_months_data = {
        'labels': [stat.month for stat in peak_months],
        'values': [stat.booking_count for stat in peak_months]
    }
    
    # Calculate summary statistics
    total_bookings = sum(stat.total_bookings for stat in monthly_stats)
    total_revenue = sum(float(stat.total_revenue or 0) for stat in monthly_stats)
    total_students = sum(stat.total_students for stat in monthly_stats)
    avg_revenue_per_booking = total_revenue / total_bookings if total_bookings > 0 else 0
    
    # Calculate growth rates
    if len(monthly_stats) >= 2:
        current_month = monthly_stats[-1]
        previous_month = monthly_stats[-2]
        revenue_growth = ((float(current_month.total_revenue or 0) - float(previous_month.total_revenue or 0)) / 
                         float(previous_month.total_revenue or 1)) * 100
        booking_growth = ((current_month.total_bookings - previous_month.total_bookings) / 
                         previous_month.total_bookings) * 100
    else:
        revenue_growth = 0
        booking_growth = 0
    
    return render_template('tour_operator/analytics.html',
                         monthly_data=json.dumps(monthly_data),
                         package_data=json.dumps(package_data),
                         status_data=json.dumps(status_data),
                         peak_months_data=json.dumps(peak_months_data),
                         total_bookings=total_bookings,
                         total_revenue=total_revenue,
                         total_students=total_students,
                         avg_revenue_per_booking=avg_revenue_per_booking,
                         revenue_growth=revenue_growth,
                         booking_growth=booking_growth)






