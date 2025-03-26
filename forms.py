from datetime import date
from flask import current_app
from flask_wtf import FlaskForm
from wtforms import DateField, HiddenField, IntegerField, SelectField, StringField, PasswordField, SubmitField, BooleanField, TextAreaField, DecimalField, ValidationError, FileField, MultipleFileField
from typing import Optional
from wtforms.validators import DataRequired, Email, EqualTo, Optional, NumberRange, Length
from flask_wtf.file import FileAllowed, FileRequired
from extensions import db
from models import Country, Currency, Camp, BookingForm, User, Guardian, Child, CampRegistration
from wtforms.widgets import TextArea

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    login_field = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')

class ResendVerificationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Resend Verification Email')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Password Reset Email')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Change Password')


class ProfileForm(FlaskForm):
    name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=15)])
    country_id = SelectField('Country', coerce=str, validators=[Optional()])
    date_of_birth = DateField('Birthday', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),  
        ('M', 'Male'),
        ('F', 'Female'),
        ('N', 'Prefer not to say')
    ], validators=[DataRequired(message="Please select a gender")])
    currency_id = StringField('Currency', render_kw={'readonly': True})
    submit = SubmitField('Update Profile')

    def __init__(self, formdata=None, *args, current_user=None, **kwargs):
        super(ProfileForm, self).__init__(formdata=formdata, *args, **kwargs)
        
        # Always load country choices, regardless of whether it's a GET or POST
        self.country_id.choices = [(c.id, c.country) for c in Country.query.order_by(Country.country).all()]
        
        # Only populate from current_user if this is not a form submission
        if current_user:
            user = db.session.merge(current_user)
            
            if not formdata:  # Only set initial values if not a form submission
                # Pre-populate form data
                self.email.data = user.email
                self.phone_number.data = user.phone_number
                self.date_of_birth.data = user.date_of_birth
                self.gender.data = user.gender or ''
                
                if user.country_id:
                    self.country_id.data = user.country_id
                    currency = Currency.query.select_from(Country).join(Currency)\
                        .filter(Country.id == user.country_id).first()
                    if currency:
                        self.currency_id.data = currency.id
                    self.country_id.render_kw = {'disabled': True}
                
                # Set readonly/disabled fields based on existing data
                if user.date_of_birth:
                    self.date_of_birth.render_kw = {'readonly': True}
                if user.gender:
                    self.gender.render_kw = {'disabled': True}
                if user.phone_number:
                    self.phone_number.render_kw = {'readonly': True}

    def validate_country_id(self, field):
        if field.data:
            # Debug logging
            current_app.logger.debug(f"Validating country: {field.data}")
            current_app.logger.debug(f"Available choices: {dict(self.country_id.choices)}")
            
            # Check if the country exists in the database
            country = Country.query.get(field.data)
            if not country:
                raise ValidationError('Invalid country selection.')

class ProfilePicForm(FlaskForm):
    profile_picture = FileField('Upload Profile Picture', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Upload Picture')

class CSRFOnlyForm(FlaskForm):
    pass

class BookingOrderForm(FlaskForm):
    camp_id = SelectField('Select Camp', coerce=int, validators=[DataRequired()])
    adults = IntegerField('Number of Adults', 
                            validators=[DataRequired(), NumberRange(min=1, message="At least one adult is required")],
                            default=1)
    children = IntegerField('Number of Children',
                              validators=[NumberRange(min=0)],
                              default=0)
    check_in_date = DateField('Check-in Date', 
                             validators=[DataRequired()],
                             default=date.today)
    check_out_date = DateField('Check-out Date',
                              validators=[DataRequired()])
    submit = SubmitField('Proceed to Checkout')

    def __init__(self, *args, **kwargs):
        super(BookingOrderForm, self).__init__(*args, **kwargs)
        # Populate camp choices
        self.camp_id.choices = [(camp.id, f"{camp.name} - {camp.location}") 
                              for camp in Camp.query.order_by(Camp.name).all()]

    def validate(self):
        if not super(BookingOrderForm, self).validate():
            return False

        if self.check_in_date.data < date.today():
            self.check_in_date.errors.append('Check-in date cannot be in the past')
            return False

        if self.check_out_date.data <= self.check_in_date.data:
            self.check_out_date.errors.append('Check-out date must be after check-in date')
            return False

        # Get selected camp
        camp = Camp.query.get(self.camp_id.data)
        if not camp:
            self.camp_id.errors.append('Invalid camp selected')
            return False

        # Check if total guests exceed camp capacity
        total_guests = self.adults.data + self.children.data
        if total_guests > camp.capacity:
            self.adults.errors.append(f'Total number of guests cannot exceed camp capacity of {camp.capacity}')
            return False

        # Check camp availability
        if not camp.is_available(self.check_in_date.data, 
                               self.check_out_date.data, 
                               total_guests):
            self.camp_id.errors.append('Camp is not available for the selected dates and number of guests')
            return False

        return True 

class CampForm(FlaskForm):
    name = StringField('Camp Name', validators=[
        DataRequired(),
        Length(max=100, message='Camp name must be less than 100 characters')
    ])
    description = TextAreaField('Description', validators=[DataRequired()])
    camp_objectives = TextAreaField('Camp Objectives')
    location = StringField('Location', validators=[
        DataRequired(),
        Length(max=200, message='Location must be less than 200 characters')
    ])
    
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    nights = IntegerField('Number of nights', validators=[
        Optional(),
        NumberRange(min=0, message='Number of nights must be at least 0')
    ])
    
    price_per_adult = DecimalField('Price per Adult', validators=[
        DataRequired(),
        NumberRange(min=0, message='Price must be 0 or greater')
    ])
    price_per_child = DecimalField('Price per Child', validators=[
        DataRequired(),
        NumberRange(min=0, message='Price must be 0 or greater')
    ])
    
    capacity = IntegerField('Capacity', validators=[
        DataRequired(),
        NumberRange(min=1, message='Capacity must be at least 1')
    ])
    
    camp_status = SelectField('Camp Status', validators=[DataRequired()], choices=[
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ])
    
    camp_type = SelectField('Camp Type', validators=[DataRequired()], choices=[
        ('regular', 'Regular'),
        ('holiday', 'Holiday'),
        ('weekend', 'Weekend'),
        ('special', 'Special Event')
    ])
    
    camp_category = SelectField('Camp Category', validators=[DataRequired()], choices=[
        ('general', 'General'),
        ('sports', 'Sports'),
        ('academic', 'Academic'),
        ('adventure', 'Adventure'),
        ('arts', 'Arts & Crafts'),
        ('science', 'Science'),
        ('music', 'Music'),
        ('leadership', 'Leadership')
    ])
    
    age_range_min = IntegerField('Minimum Age', validators=[
        Optional(),
        NumberRange(min=0, message='Minimum age cannot be negative')
    ])
    age_range_max = IntegerField('Maximum Age', validators=[
        Optional(),
        NumberRange(min=1, message='Maximum age must be at least 1')
    ])
    
    camp_image = FileField('Camp Image', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only! Allowed formats: jpg, png, jpeg')
    ])
    
    submit = SubmitField('Submit')

    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError('End date must be after start date')
        
    def validate_age_range_max(self, field):
        if field.data and self.age_range_min.data and field.data < self.age_range_min.data:
            raise ValidationError('Maximum age must be greater than minimum age')

class BankDetailsForm(FlaskForm):
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    account_holder = StringField('Account Holder Name', validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[DataRequired()])
    branch_code = StringField('Branch Code', validators=[DataRequired()])
    account_type = SelectField('Account Type', choices=[
        ('savings', 'Savings Account'),
        ('checking', 'Checking Account'),
        ('business', 'Business Account')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Banking Details')

class MessageForm(FlaskForm):
    camp_id = SelectField('Camp', coerce=int, validators=[DataRequired()])
    recipient_id = SelectField('Recipient', coerce=int, validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired()])
    content = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        # Populate camp choices - this would typically be filtered by the current user's camps
        self.camp_id.choices = [(camp.id, camp.name) 
                              for camp in Camp.query.order_by(Camp.name).all()]
        # Populate recipient choices - this would typically be filtered by the selected camp
        self.recipient_id.choices = [(user.id, f"{user.name} ({user.role})")
                                   for user in User.query.filter(User.role.in_(['parent', 'child'])).all()] 
        
class GuardianForm(FlaskForm):
    """Form for creating a guardian profile"""
    terms_accepted = BooleanField('I accept the terms and conditions', validators=[DataRequired()])
    submit = SubmitField('Create Guardian Profile')

class SchoolForm(FlaskForm):
    """Form for creating a new school"""
    name = StringField('School Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    latitude = HiddenField('Latitude')
    longitude = HiddenField('Longitude')
    state_id = HiddenField('State ID')
    country_id = HiddenField('Country ID')
    submit = SubmitField('Add School')

class CampPackageForm(FlaskForm):
    name = StringField('Package Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    min_students = IntegerField('Minimum Students', validators=[DataRequired(), NumberRange(min=1)])
    max_students = IntegerField('Maximum Students', validators=[DataRequired(), NumberRange(min=1)])
    price_per_student = DecimalField('Price per Student', validators=[DataRequired(), NumberRange(min=0)])
    price_per_teacher = DecimalField('Price per Teacher', validators=[DataRequired(), NumberRange(min=0)])
    meals = StringField('Meals', validators=[DataRequired(), Length(max=50)])
    thumbnail = FileField('Thumbnail Image', validators=[Optional()])
    photos = MultipleFileField('Additional Photos', validators=[Optional()])
    duration_days = IntegerField('Duration (Days)', validators=[DataRequired(), NumberRange(min=1)])
    included_activities = TextAreaField('Included Activities', validators=[Optional()])
    requirements = TextAreaField('Requirements', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], validators=[DataRequired()])
    camp_id = SelectField('Camp', coerce=int, validators=[Optional()])
    tour_operator_id = SelectField('Tour Operator', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Package')

    def validate_max_students(self, field):
        if field.data < self.min_students.data:
            raise ValidationError('Maximum students must be greater than minimum students')

class PasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])

class CompanyForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(min=2, max=100)])
    company_registration_number = StringField('Company Registration Number', validators=[DataRequired()])
    tax_number = StringField('Tax Number', validators=[DataRequired()])

class BankingDetailsForm(FlaskForm):
    bank_id = SelectField('Bank', coerce=int, validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[DataRequired()])
    account_holder_name = StringField('Account Holder Name', validators=[DataRequired()])
    account_type = SelectField('Account Type', 
                             choices=[
                                 ('', 'Select Account Type'),
                                 ('savings', 'Savings'),
                                 ('checking', 'Checking'),
                                 ('business', 'Business')
                             ],
                             validators=[DataRequired()])
    branch = StringField('Branch', validators=[Optional()])
    branch_code = StringField('Branch Code', validators=[Optional()])
    account_iban = StringField('IBAN', validators=[Optional()])
    is_primary = BooleanField('Set as Primary Account')