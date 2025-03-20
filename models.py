import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import random
import string

db = SQLAlchemy()

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(50), nullable=True)
    lastname = db.Column(db.String(50), nullable=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    role = db.Column(db.String(20), nullable=True, default='organiser')
    password_hash = db.Column('password_hash', db.String(255), nullable=False)
    verification = db.Column(db.String(50), nullable=False, default='unverified')
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    account_locked = db.Column(db.Boolean, nullable=False, default=False)
    date_of_birth = db.Column(db.Date, nullable=True) 
    gender = db.Column(db.String(10), nullable=True) 
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    school = db.relationship('School', back_populates='students', foreign_keys=[school_id])
    grade = db.Column(db.String(50), nullable=True)
    administered_schools = db.relationship('School', back_populates='admin', 
                                        foreign_keys='School.super_admin')
    profile_picture = db.Column(db.String(150), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)  
    emergency_contact = db.Column(db.String(150), nullable=True)
    
    diabetic = db.Column(db.Boolean, default=False)
    heart_condition = db.Column(db.Boolean, default=False)
    seizures = db.Column(db.Boolean, default=False)
    wheelchair_support = db.Column(db.Boolean, default=False)
    asthmatic = db.Column(db.Boolean, default=False)
    celiac_disease = db.Column(db.Boolean, default=False)
    epilepsy = db.Column(db.Boolean, default=False)
    other_medical_conditions = db.Column(db.String(100), nullable=True)
    dietary = db.Column(db.String(100), nullable=True)
    nuts = db.Column(db.Boolean, default=False)
    lactose = db.Column(db.Boolean, default=False)
    eggs = db.Column(db.Boolean, default=False)
    soy = db.Column(db.Boolean, default=False)
    pork = db.Column(db.Boolean, default=False)
    red_meat = db.Column(db.Boolean, default=False)
    gluten = db.Column(db.Boolean, default=False)
    sea_food = db.Column(db.Boolean, default=False)
    other = db.Column(db.String(500), nullable=True)
    medical_aid_name = db.Column(db.String(150), nullable=True)
    medical_aid_number = db.Column(db.String(150), nullable=True)
    id_number_of_holder = db.Column(db.String(150), nullable=True)
    photography_consent = db.Column(db.Boolean, default=False)
    water_activities_consent = db.Column(db.Boolean, default=False)
    swimming_level = db.Column(db.String(50), nullable=True)
    post_camp_consent = db.Column(db.Boolean, default=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    # country =  db.Column(db.String(100), nullable=True)
    # currency_id =  db.Column(db.String(3), nullable=True)

    company = db.relationship('Company', back_populates='users')
    guardian = db.relationship('Guardian', back_populates='user', uselist=False)
    banking_details = db.relationship('BankingDetails', back_populates='user', lazy=True)

    # Password property and methods
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)  # Correctly refer to password_hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    from itsdangerous import URLSafeTimedSerializer as Serializer

    # Token generation for email verification
    
    def generate_verification_token(self, secret_key):
        s = URLSafeTimedSerializer(secret_key)
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_verification_token(token, secret_key):
        from itsdangerous import URLSafeTimedSerializer as Serializer
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['user_id'])
    
    def generate_reset_token(self, secret_key, expiration=3600):  # Expiration is 1 hour (3600 seconds)
        s = URLSafeTimedSerializer(secret_key)
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')
    
    @staticmethod
    def verify_reset_token(token, secret_key):
        s = URLSafeTimedSerializer(secret_key)
        try:
            # Here, we're specifying the token expiry time (3600 seconds or 1 hour)
            data = s.loads(token, salt='password-reset-salt', max_age=3600)  # max_age controls expiration
        except Exception as e:
            print(f'Token verification error: {e}')  # Log the error for debugging purposes
            return None
        return User.query.get(data['user_id'])
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
    

class Child(db.Model):
    __tablename__ = 'child'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardian.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    registrations = db.relationship('CampRegistration', backref='child', lazy=True, 
                                  foreign_keys='CampRegistration.child_id')

class CampRegistration(db.Model):
    __tablename__ = 'camp_registration'

    id = db.Column(db.Integer, primary_key=True)
    camp_id = db.Column(db.Integer, db.ForeignKey('camp.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('camp_registrations', lazy=True))

class Camp(db.Model):
    __tablename__ = 'camp'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    camp_objectives = db.Column(db.Text)
    nights = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    price_per_adult = db.Column(db.Numeric(10, 2), nullable=True)
    price_per_child = db.Column(db.Numeric(10, 2), nullable=True)
    capacity = db.Column(db.Integer, nullable=False)
    camp_status = db.Column(db.String(20), nullable=False)
    camp_image = db.Column(db.String(120), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    organiser_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    camp_category = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    camp_type = db.Column(db.String(20), nullable=False)
    age_range_min = db.Column(db.Integer, nullable=True)
    age_range_max = db.Column(db.Integer, nullable=True)
    camp_code = db.Column(db.String(50), unique=True, nullable=False)

    # Relationships
    teacher = db.relationship('Teacher', backref=db.backref('camps', lazy=True))
    registrations = db.relationship('CampRegistration', backref='camp', lazy=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.camp_code:
            self.camp_code = generate_camp_code()

    def to_dict(self):
        """Convert camp to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'description': self.description,
            'price_per_adult': float(self.price_per_adult),
            'price_per_child': float(self.price_per_child),
            'capacity': self.capacity
        }

    def is_available(self, check_in_date, check_out_date, guests):
        """Check if camp is available for the given dates and number of guests"""
        from models import BookingForm
        
        # Check capacity
        if guests > self.capacity:
            return False
            
        # Check existing bookings
        overlapping_bookings = BookingForm.query.filter(
            BookingForm.camp_id == self.id,
            BookingForm.status != 'cancelled',
            BookingForm.check_in_date < check_out_date,
            BookingForm.check_out_date > check_in_date
        ).all()
        
        for booking in overlapping_bookings:
            if booking.adults + booking.children + guests > self.capacity:
                return False
                
        return True 
    
class Teacher(db.Model):
    __tablename__ = 'teacher'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Currency(db.Model):
    __tablename__ = 'currency'
    id = db.Column(db.String(3), primary_key=True)
    currency = db.Column(db.String(20), unique=True, nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    code = db.Column(db.String(3), nullable=False)
    
class Country(db.Model):
    __tablename__ = 'country'

    id = db.Column(db.String(3), primary_key=True)
    country = db.Column(db.String(20), unique=True, nullable=False)
    code = db.Column(db.String(3), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    
class State(db.Model):
    __tablename__ = 'state'
    id = db.Column(db.String(3), primary_key=True)
    state = db.Column(db.String(20), unique=True, nullable=False)
    code = db.Column(db.String(3), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)

class BankingDetails(db.Model):
    __tablename__ = 'banking_details'

    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(50), nullable=False)
    account_holder_name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    branch = db.Column(db.String(100), nullable=True)
    branch_code = db.Column(db.String(10), nullable=True)
    account_iban = db.Column(db.String(34), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False)

    # New fields
    nickname = db.Column(db.String(100), nullable=True)
    is_primary = db.Column(db.Boolean, default=False)

    # Define the relationship with User
    user = db.relationship('User', back_populates='banking_details')
    bank = db.relationship('Banks', back_populates='banking_details')

    def __repr__(self):
        return f'<BankingDetails {self.id} for User {self.user_id}>'

    def set_primary(self):
        # Set this account as primary
        self.is_primary = True
        
        # Unset primary status for all other accounts of the same user
        BankingDetails.query.filter(
            BankingDetails.user_id == self.user_id,
            BankingDetails.id != self.id
        ).update({"is_primary": False})
        
        db.session.commit()

class Banks(db.Model):
    __tablename__ = 'banks'

    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100), nullable=False)
    bank_code = db.Column(db.String(10), nullable=True)
    bank_swift_code = db.Column(db.String(12), nullable=True)
    country_id = db.Column(db.String(3), db.ForeignKey('country.id'), nullable=False)
    state_id = db.Column(db.String(3), db.ForeignKey('state.id'), nullable=True)
    
    banking_details = db.relationship('BankingDetails', back_populates='bank')
    country = db.relationship('Country', backref='banks')
    state = db.relationship('State', backref='banks')

    def __repr__(self):
        return f'<Banks {self.id} {self.bank_name}>'
    
class School(db.Model):
    __tablename__ = 'school'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    super_admin = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relationships
    students = db.relationship('User', back_populates='school', foreign_keys='User.school_id')
    admin = db.relationship('User', back_populates='administered_schools', foreign_keys=[super_admin])

class Guardian(db.Model):
    __tablename__ = 'guardian'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Update the relationship to use back_populates instead of backref
    user = db.relationship('User', back_populates='guardian', lazy=True)

def generate_reference_number():
    """
    Generate a unique booking reference number with format:
    BK-YYMMDD-XXXX where:
    - BK: Booking prefix
    - YYMMDD: Current date (year, month, day)
    - XXXX: Random 4-digit number
    """
    # Get current date components
    date_str = datetime.now().strftime('%y%m%d')  # YYMMDD format
    
    # Generate 4 random digits
    random_digits = ''.join(random.choices(string.digits, k=4))
    
    # Create reference number
    reference = f"BK-{date_str}-{random_digits}"
    
    # Check if reference already exists and regenerate if needed
    # Note: We need to import BookingForm locally to avoid circular import
    from models import BookingForm
    while BookingForm.query.filter_by(reference_number=reference).first() is not None:
        random_digits = ''.join(random.choices(string.digits, k=4))
        reference = f"BK-{date_str}-{random_digits}"
    
    return reference

class BookingForm(db.Model):
    __tablename__ = 'booking_form'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    camp_id = db.Column(db.Integer, db.ForeignKey('camp.id'), nullable=False)
    adults = db.Column(db.Integer, nullable=False)
    children = db.Column(db.Integer, nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    reference_number = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    camp = db.relationship('Camp', backref=db.backref('bookings', lazy=True))

    def __init__(self, **kwargs):
        super(BookingForm, self).__init__(**kwargs)
        if not self.reference_number:
            self.reference_number = generate_reference_number()

    @property
    def nights(self):
        """Calculate the number of nights for the booking"""
        if self.check_in_date and self.check_out_date:
            return (self.check_out_date - self.check_in_date).days
        return 0

    @property
    def adult_total(self):
        """Calculate total cost for adults"""
        return self.adults * self.camp.price_per_adult * self.nights

    @property
    def child_total(self):
        """Calculate total cost for children"""
        return self.children * self.camp.price_per_child * self.nights

    @property
    def subtotal(self):
        """Calculate subtotal before fees and taxes"""
        return self.adult_total + self.child_total

    @property
    def service_fee(self):
        """Calculate service fee (10% of subtotal)"""
        return self.subtotal * 0.10

    @property
    def tax_rate(self):
        """Tax rate (15%)"""
        return 0.15

    @property
    def tax_amount(self):
        """Calculate tax amount"""
        return (self.subtotal + self.service_fee) * self.tax_rate

    def calculate_total(self):
        """Calculate total amount including all fees and taxes"""
        self.total_amount = (
            self.subtotal +
            self.service_fee +
            self.tax_amount
        )
        return self.total_amount

    def to_dict(self):
        """Convert booking to dictionary"""
        return {
            'id': self.id,
            'reference_number': self.reference_number,
            'camp_name': self.camp.name,
            'check_in_date': self.check_in_date.strftime('%Y-%m-%d'),
            'check_out_date': self.check_out_date.strftime('%Y-%m-%d'),
            'adults': self.adults,
            'children': self.children,
            'nights': self.nights,
            'adult_total': float(self.adult_total),
            'child_total': float(self.child_total),
            'service_fee': float(self.service_fee),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'status': self.status
        }

class Payment(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('camp_registration.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    reference = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    registration = db.relationship('CampRegistration', backref=db.backref('payments', lazy=True))

    def __repr__(self):
        return f'<Payment {self.id} for Registration {self.registration_id}>'

class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    camp_id = db.Column(db.Integer, db.ForeignKey('camp.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy=True))
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('received_messages', lazy=True))
    camp = db.relationship('Camp', backref=db.backref('messages', lazy=True))

    def __repr__(self):
        return f'<Message {self.id} from User {self.sender_id} to User {self.recipient_id}>' 

class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    company_registration_number = db.Column(db.String(100), nullable=False)
    tax_number =  db.Column(db.String(100), nullable=False)
    users = db.relationship('User', back_populates='company')

def generate_camp_code():
    """Generate a unique camp code with minimum 5 digits"""
    prefix = 'C'  # Camp prefix
    year = datetime.now().strftime('%y')  # 2-digit year
    # Generate 4 random digits (this plus year makes 5 digits minimum)
    random_digits = ''.join(random.choices(string.digits, k=4))
    
    camp_code = f"{prefix}{year}{random_digits}"
    
    # Check if code already exists and regenerate if needed
    while Camp.query.filter_by(camp_code=camp_code).first() is not None:
        random_digits = ''.join(random.choices(string.digits, k=4))
        camp_code = f"{prefix}{year}{random_digits}"
    
    return camp_code
