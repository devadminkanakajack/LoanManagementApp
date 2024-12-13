import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from flask_migrate import Migrate
from db import db, init_db

# Initialize Flask app
app = Flask(__name__)

# Configure SQLAlchemy
database_url = os.environ.get('DATABASE_URL')
if database_url and not database_url.endswith('?sslmode=require'):
    database_url += '?sslmode=require'

app.config.update(
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        'pool_size': 5,
        'pool_recycle': 280,
        'pool_timeout': 20,
        'max_overflow': 2
    },
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev')
)

# Initialize extensions
init_db(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Email configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER')
)

# Import and initialize modules after db setup
from modules import borrowers
app.register_blueprint(borrowers.bp)

def send_registration_email(user_email, username, is_application=False):
    """Send registration confirmation email"""
    subject = "Welcome to KNR Financial Services"
    if is_application:
        body = f"""
        Dear {username},
        
        Thank you for applying for a loan with KNR Financial Services. Your account has been automatically created with the following credentials:
        
        Username: {username}
        Password: password1234
        
        Please login and change your password at your earliest convenience.
        
        Best regards,
        KNR Financial Services Team
        """
    else:
        body = f"""
        Dear {username},
        
        Thank you for registering with KNR Financial Services. Your account has been successfully created.
        
        You can now login and apply for loans through our portal.
        
        Best regards,
        KNR Financial Services Team
        """
    
    msg = Message(subject, recipients=[user_email], body=body)
    mail.send(msg)

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Models
class Borrower(db.Model):
    """Model for storing borrower information and OCR extracted data"""
    __tablename__ = 'borrowers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Personal Information
    full_name = db.Column(db.String(200), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    marital_status = db.Column(db.String(20))
    dependents = db.Column(db.Integer)
    nationality = db.Column(db.String(100))
    
    # Contact Information
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    
    # Employment Information
    employment_type = db.Column(db.String(50))
    employer_name = db.Column(db.String(200))
    employer_address = db.Column(db.String(300))
    employment_duration = db.Column(db.Integer)  # in months
    position = db.Column(db.String(100))
    department = db.Column(db.String(100))
    employment_status = db.Column(db.String(50))
    
    # Financial Information
    annual_income = db.Column(db.Numeric(12, 2))
    monthly_income = db.Column(db.Numeric(10, 2))
    other_income = db.Column(db.Numeric(10, 2))
    total_expenses = db.Column(db.Numeric(10, 2))
    credit_score = db.Column(db.Integer)
    
    # Banking Information
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    bsb_code = db.Column(db.String(10))
    account_type = db.Column(db.String(20))
    
    # Document Information
    identification_type = db.Column(db.String(50))
    identification_number = db.Column(db.String(50))
    tax_id = db.Column(db.String(50))
    
    # References
    reference_name_1 = db.Column(db.String(100))
    reference_phone_1 = db.Column(db.String(20))
    reference_relation_1 = db.Column(db.String(50))
    reference_name_2 = db.Column(db.String(100))
    reference_phone_2 = db.Column(db.String(20))
    reference_relation_2 = db.Column(db.String(50))
    
    # OCR Processing Data
    ocr_confidence_score = db.Column(db.Float)
    last_ocr_update = db.Column(db.DateTime)
    ocr_raw_text = db.Column(db.Text)
    ocr_extracted_fields = db.Column(db.JSON)
    
    # Metadata
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='borrower', uselist=False)
    loans = db.relationship('Loan', back_populates='borrower', lazy='dynamic')
    
    def __repr__(self):
        return f'<Borrower {self.full_name}>'

    def process_ocr_data(self, ocr_text):
        """Process OCR extracted text and update relevant fields"""
        import re
        self.ocr_raw_text = ocr_text
        extracted_data = {}
        
        # Define patterns for field extraction
        patterns = {
            'full_name': r'Name:?\s*([^\n]+)',
            'date_of_birth': r'Date\s+of\s+Birth:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            'phone': r'Phone:?\s*([\d\s\-+]+)',
            'email': r'Email:?\s*([^\n@]+@[^\n]+)',
            'employer_name': r'Employer:?\s*([^\n]+)',
            'monthly_income': r'Monthly\s+Income:?\s*\$?\s*([\d,]+\.?\d*)',
            'bank_name': r'Bank:?\s*([^\n]+)',
            'account_number': r'Account\s+Number:?\s*(\d+)',
        }
        
        # Extract data using regex patterns
        for field, pattern in patterns.items():
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                extracted_data[field] = match.group(1).strip()
        
        self.ocr_extracted_fields = extracted_data
        self.ocr_confidence_score = 0.8  # Example confidence score
        self.last_ocr_update = datetime.utcnow()
        
        # Update borrower fields with extracted data
        for field, value in extracted_data.items():
            if hasattr(self, field):
                setattr(self, field, value)

class User(UserMixin, db.Model):
    """User model for authentication and basic user information"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    client_number = db.Column(db.String(10), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    department = db.Column(db.String(50), nullable=True)
    is_application_created = db.Column(db.Boolean, default=False)
    password_changed = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False, default='borrower')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    borrower = db.relationship('Borrower', back_populates='user', uselist=False)
    loans = db.relationship('Loan', back_populates='user', lazy='dynamic')
    documents = db.relationship('Document', back_populates='user', lazy=True)
    applications = db.relationship('LoanApplication', back_populates='user', lazy=True)

    @staticmethod
    def generate_client_number():
        """Generate the next client number in sequence KNRFS00001"""
        last_user = User.query.order_by(User.client_number.desc()).first()
        if not last_user or not last_user.client_number:
            return 'KNRFS00001'
        try:
            last_number = int(last_user.client_number[5:])
            return f'KNRFS{str(last_number + 1).zfill(5)}'
        except (ValueError, IndexError):
            return 'KNRFS00001'

    @staticmethod
    def generate_client_number():
        """Generate the next client number in sequence KNRFS00001"""
        last_user = User.query.order_by(User.client_number.desc()).first()
        if not last_user or not last_user.client_number:
            return 'KNRFS00001'
        try:
            last_number = int(last_user.client_number[5:])
            return f'KNRFS{str(last_number + 1).zfill(5)}'
        except (ValueError, IndexError):
            return 'KNRFS00001'

class PersonalDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    application = db.relationship('LoanApplication', back_populates='personal_details')
    surname = db.Column(db.String(100), nullable=False)
    given_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    village = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    nationality = db.Column(db.String(100), nullable=False)

class EmploymentDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    company_department = db.Column(db.String(200), nullable=False)
    file_number = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    postal_address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date_employed = db.Column(db.Date, nullable=False)
    paymaster = db.Column(db.String(200), nullable=False)
    
    # Relationship
    application = db.relationship('LoanApplication', back_populates='employment_details')

class ResidentialAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    lot = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    suburb = db.Column(db.String(100), nullable=False)
    street_name = db.Column(db.String(200), nullable=False)
    marital_status = db.Column(db.String(20), nullable=False)
    spouse_last_name = db.Column(db.String(100))
    spouse_first_name = db.Column(db.String(100))
    spouse_employer_name = db.Column(db.String(200))
    spouse_contact = db.Column(db.String(20))
    
    # Relationship
    application = db.relationship('LoanApplication', back_populates='residential_address')

class LoanProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    purposes = db.Column(db.JSON, nullable=False)  # Array of selected purposes: ['school_fees', 'medical', etc]
    primary_purpose = db.Column(db.String(50), nullable=False)  # Main purpose
    description = db.Column(db.Text)
    
    # Relationship
    application = db.relationship('LoanApplication', back_populates='loan_product')

class FinancialDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    loan_amount = db.Column(db.Numeric(10, 2), nullable=False)
    fortnightly_repayment = db.Column(db.Numeric(10, 2), nullable=False)
    number_of_fortnights = db.Column(db.Integer, nullable=False)
    total_loan_repayable = db.Column(db.Numeric(10, 2), nullable=False)
    gross_salary = db.Column(db.Numeric(10, 2), nullable=False)
    net_salary = db.Column(db.Numeric(10, 2), nullable=False)
    
    # OCR extracted financial data
    annual_income = db.Column(db.Numeric(12, 2))
    monthly_expenses = db.Column(db.Numeric(10, 2))
    existing_loans = db.Column(db.Numeric(10, 2))
    credit_score = db.Column(db.Integer)
    
    # Relationship
    application = db.relationship('LoanApplication', back_populates='financial_details', uselist=False)

class LoanFundingDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    bank = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    bsb_code = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(200), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    account_type = db.Column(db.String(20), nullable=False)  # savings/cheque
    
    # Relationship
    application = db.relationship('LoanApplication', back_populates='funding_details')

class LoanBreakUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    loan_amount = db.Column(db.Numeric(10, 2), nullable=False)
    existing_loan = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    net_loan_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relationship
    application = db.relationship('LoanApplication', back_populates='break_up')

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    signature_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='applications')
    borrower = db.relationship('Borrower', 
                             secondary='user',
                             primaryjoin="LoanApplication.user_id==User.id",
                             secondaryjoin="User.id==Borrower.user_id",
                             backref=db.backref('applications', lazy='dynamic'),
                             lazy='joined')
    personal_details = db.relationship('PersonalDetails', back_populates='application', uselist=False)
    employment_details = db.relationship('EmploymentDetails', back_populates='application', uselist=False)
    residential_address = db.relationship('ResidentialAddress', back_populates='application', uselist=False)
    loan_product = db.relationship('LoanProduct', back_populates='application', uselist=False)
    financial_details = db.relationship('FinancialDetails', back_populates='application', uselist=False)
    funding_details = db.relationship('LoanFundingDetails', back_populates='application', uselist=False)
    break_up = db.relationship('LoanBreakUp', back_populates='application', uselist=False)
    documents = db.relationship('Document', back_populates='application', lazy=True)
    loan = db.relationship('Loan', back_populates='application', uselist=False)

# Removed duplicate Borrower class definition
    
    def process_ocr_data(self, ocr_text):
        """Process OCR extracted text and update relevant fields"""
        self.ocr_raw_text = ocr_text
        extracted_data = {}
        
        # Define patterns for field extraction
        patterns = {
            'full_name': r'Name:?\s*([^\n]+)',
            'date_of_birth': r'Date\s+of\s+Birth:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            'phone': r'Phone:?\s*([\d\s\-+]+)',
            'email': r'Email:?\s*([^\n@]+@[^\n]+)',
            'employer_name': r'Employer:?\s*([^\n]+)',
            'monthly_income': r'Monthly\s+Income:?\s*\$?\s*([\d,]+\.?\d*)',
            'bank_name': r'Bank:?\s*([^\n]+)',
            'account_number': r'Account\s+Number:?\s*(\d+)',
        }
        
        # Extract data using regex patterns
        for field, pattern in patterns.items():
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                extracted_data[field] = match.group(1).strip()
        
        self.ocr_extracted_fields = extracted_data
        self.ocr_confidence_score = 0.8  # Example confidence score
        self.last_ocr_update = datetime.utcnow()
        
        # Update borrower fields with extracted data
        for field, value in extracted_data.items():
            if hasattr(self, field):
                setattr(self, field, value)

class LoanDetails(db.Model):
    __tablename__ = 'loan_details'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)  # Fixed table name to 'loans'
    loan_type = db.Column(db.String(50), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    processing_fee = db.Column(db.Numeric(10, 2))
    insurance_fee = db.Column(db.Numeric(10, 2))
    total_amount_payable = db.Column(db.Numeric(10, 2), nullable=False)
    monthly_installment = db.Column(db.Numeric(10, 2), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    disbursement_date = db.Column(db.DateTime)
    disbursement_method = db.Column(db.String(50))
    disbursement_status = db.Column(db.String(20), default='pending')
    
    # Financial details from OCR
    income_proof = db.Column(db.JSON)
    expense_details = db.Column(db.JSON)
    collateral_details = db.Column(db.JSON)
    
    # Relationship with Loan
    loan = db.relationship('Loan', back_populates='details', uselist=False)

class RepaymentRecord(db.Model):
    """Model for storing loan repayment records and OCR extracted data"""
    __tablename__ = 'repayments'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    
    # Payment Details
    payment_number = db.Column(db.String(20), unique=True)  # For tracking payments sequentially
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True)
    payment_status = db.Column(db.String(20), default='pending')
    receipt_number = db.Column(db.String(50), unique=True)
    notes = db.Column(db.Text)
    
    # Payment breakdown
    principal_amount = db.Column(db.Numeric(10, 2), nullable=False)
    interest_amount = db.Column(db.Numeric(10, 2), nullable=False)
    late_fee = db.Column(db.Numeric(10, 2), default=0)
    total_paid = db.Column(db.Numeric(10, 2))  # principal + interest + late_fee
    
    # Payment tracking
    payment_period = db.Column(db.String(20))  # e.g., 'FN01', 'FN02' for fortnights
    is_late_payment = db.Column(db.Boolean, default=False)
    days_late = db.Column(db.Integer, default=0)
    outstanding_balance = db.Column(db.Numeric(10, 2))  # Remaining loan balance after this payment
    
    # OCR data
    ocr_verified = db.Column(db.Boolean, default=False)
    ocr_confidence_score = db.Column(db.Float)
    ocr_extracted_data = db.Column(db.JSON)
    receipt_image_path = db.Column(db.String(255))
    last_ocr_update = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Track who recorded the payment
    
    # Relationships
    loan = db.relationship('Loan', back_populates='repayments')
    recorder = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<RepaymentRecord {self.payment_number} - Amount: ${self.amount_paid} - Status: {self.payment_status}>'
    
    def calculate_total(self):
        """Calculate total payment including fees"""
        self.total_paid = self.principal_amount + self.interest_amount + self.late_fee
        return self.total_paid
    
    def __init__(self, *args, **kwargs):
        super(RepaymentRecord, self).__init__(*args, **kwargs)
        if self.principal_amount and self.interest_amount and self.late_fee:
            self.total_paid = self.principal_amount + self.interest_amount + self.late_fee
    
    def __repr__(self):
        return f'<RepaymentRecord {self.id} - Amount: ${self.amount_paid} - Status: {self.payment_status}>'
    
    def __repr__(self):
        return f'<RepaymentRecord {self.id} - Amount: {self.amount_paid} - Status: {self.payment_status}>'
    
    def __init__(self, *args, **kwargs):
        super(RepaymentRecord, self).__init__(*args, **kwargs)
        if self.amount_paid and self.late_fee:
            self.total_paid = self.amount_paid + self.late_fee
            
    def __repr__(self):
        return f'<RepaymentRecord {self.id} - Amount: {self.amount_paid} - Status: {self.payment_status}>'
class Loan(db.Model):
    """Model for storing loan information and OCR extracted financial data"""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrowers.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=True)
    
    # Add relationship to LoanDetails
    details = db.relationship('LoanDetails', back_populates='loan', uselist=False, cascade='all, delete-orphan')
    
    # Loan Details
    loan_number = db.Column(db.String(20), unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    term = db.Column(db.Integer, nullable=False)  # in fortnights
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    purpose = db.Column(db.Text, nullable=False)
    
    # Disbursement Details
    disbursement_date = db.Column(db.DateTime)
    disbursement_method = db.Column(db.String(50))
    disbursement_status = db.Column(db.String(20), default='pending')
    
    # Financial Information
    total_amount_payable = db.Column(db.Numeric(10, 2))
    processing_fee = db.Column(db.Numeric(10, 2))
    insurance_fee = db.Column(db.Numeric(10, 2))
    monthly_installment = db.Column(db.Numeric(10, 2))
    
    # OCR extracted financial data
    ocr_confidence_score = db.Column(db.Float)
    last_ocr_update = db.Column(db.DateTime)
    ocr_extracted_data = db.Column(db.JSON)
    income_proof = db.Column(db.JSON)
    expense_details = db.Column(db.JSON)
    collateral_details = db.Column(db.JSON)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='loans')
    borrower = db.relationship('Borrower', back_populates='loans')
    repayments = db.relationship('RepaymentRecord', back_populates='loan', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('Document', back_populates='loan', lazy=True)
    application = db.relationship('LoanApplication', back_populates='loan', single_parent=True)

    def __repr__(self):
        return f'<Loan {self.loan_number} - Amount: ${self.amount} - Status: {self.status}>'

    def __repr__(self):
        return f'<Loan {self.id} - Amount: ${self.amount} - Status: {self.status}>'
    
    def __repr__(self):
        return f'<Loan {self.id} - Amount: {self.amount} - Status: {self.status}>'
    
    def __repr__(self):
        return f'<Loan {self.id} - Amount: {self.amount} - Status: {self.status}>'
    
    def __repr__(self):
        return f'<Loan {self.id} - Amount: {self.amount} - Status: {self.status}>'
    
    def __repr__(self):
        return f'<Loan {self.id} - {self.amount}>'

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=True)
    document_type = db.Column(db.String(50), nullable=False)  # payslip, employment_confirmation, data_entry, variation_advice, identification
    file_name = db.Column(db.String(255), nullable=False)  # Original filename
    file_path = db.Column(db.String(200), nullable=False)  # Full path to stored file
    file_url = db.Column(db.String(200), nullable=False)  # URL to access the file
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ocr_status = db.Column(db.String(20), nullable=False, default='pending')
    ocr_text = db.Column(db.Text)
    extracted_data = db.Column(db.JSON)

    # Relationships
    user = db.relationship('User', back_populates='documents', lazy=True)
    loan = db.relationship('Loan', back_populates='documents', lazy=True)
    application = db.relationship('LoanApplication', back_populates='documents', lazy=True)

    def process_ocr(self):
        """Process OCR on the uploaded document and extract structured data"""
        try:
            import pytesseract
            from PIL import Image
            import re
            
            if self.file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = Image.open(self.file_path)
                self.ocr_text = pytesseract.image_to_string(img)
                self.ocr_status = 'completed'
                
                extracted_data = {}
                
                # Enhanced pattern matching for borrower details
                borrower_patterns = {
                    'marital_status': r'Marital\s+Status:?\s*([^\n]+)',
                    'dependents': r'(?:Number\s+of\s+)?Dependents:?\s*(\d+)',
                    'education': r'Education(?:\s+Level)?:?\s*([^\n]+)',
                    'employment_type': r'Employment\s+Type:?\s*([^\n]+)',
                    'monthly_income': r'Monthly\s+Income:?\s*\$?\s*([\d,]+\.?\d*)',
                    'other_income': r'Other\s+Income:?\s*\$?\s*([\d,]+\.?\d*)',
                    'identification_number': r'(?:ID|Identification)\s+Number:?\s*([^\n]+)',
                    'tax_id': r'Tax\s+(?:ID|Number):?\s*([^\n]+)'
                }
                
                if self.document_type == 'loan_application':
                    # Define patterns for extracting information
                    patterns = {
                        'surname': r'Surname:?\s*([^\n]+)',
                        'given_name': r'Given\s+Name:?\s*([^\n]+)',
                        'date_of_birth': r'Date\s+of\s+Birth:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                        'gender': r'Gender:?\s*([MF]|Male|Female)',
                        'mobile_number': r'Mobile(?:\s+Number)?:?\s*([\d\s\-+]+)',
                        'email': r'Email:?\s*([^\n@]+@[^\n]+)',
                        'village': r'Village:?\s*([^\n]+)',
                        'district': r'District:?\s*([^\n]+)',
                        'province': r'Province:?\s*([^\n]+)',
                        'nationality': r'Nationality:?\s*([^\n]+)',
                        'company_department': r'(?:Company|Department):?\s*([^\n]+)',
                        'file_number': r'File\s+Number:?\s*([^\n]+)',
                        'position': r'Position:?\s*([^\n]+)',
                        'postal_address': r'Postal\s+Address:?\s*([^\n]+)',
                        'phone': r'Phone:?\s*([\d\s\-+]+)',
                        'date_employed': r'Date\s+Employed:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                        'paymaster': r'Paymaster:?\s*([^\n]+)',
                    }
                    
                    # Extract data using patterns
                    for field, pattern in patterns.items():
                        match = re.search(pattern, self.ocr_text, re.IGNORECASE)
                        if match:
                            value = match.group(1).strip()
                            if field in ['date_of_birth', 'date_employed']:
                                try:
                                    value = datetime.strptime(value, '%d/%m/%Y').date()
                                except ValueError:
                                    print(f"Failed to parse date for {field}: {value}")
                                    continue
                            extracted_data[field] = value

                elif self.document_type == 'payslip':
                    # Extract salary information
                    salary_pattern = r'Gross\s+Salary:?\s*\$?\s*([\d,]+\.?\d*)'
                    net_salary_pattern = r'Net\s+Salary:?\s*\$?\s*([\d,]+\.?\d*)'
                    
                    salary_match = re.search(salary_pattern, self.ocr_text, re.IGNORECASE)
                    net_salary_match = re.search(net_salary_pattern, self.ocr_text, re.IGNORECASE)
                    
                    if salary_match:
                        extracted_data['gross_salary'] = float(salary_match.group(1).replace(',', ''))
                    if net_salary_match:
                        extracted_data['net_salary'] = float(net_salary_match.group(1).replace(',', ''))
                
                self.extracted_data = extracted_data
                
            elif self.file_path.lower().endswith('.pdf'):
                self.ocr_status = 'unsupported_format'
            else:
                self.ocr_status = 'invalid_format'
            
            db.session.commit()
            
        except Exception as e:
            print(f"OCR processing error: {str(e)}")
            self.ocr_status = 'failed'
            db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'borrower':
            return redirect(url_for('customer_portal'))
        return redirect(url_for('admin_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='borrower',
            client_number=User.generate_client_number()
        )
        
        db.session.add(user)
        db.session.commit()
        
        try:
            send_registration_email(email, username)
            flash('Registration successful! Please check your email for confirmation.')
        except Exception as e:
            flash('Registration successful! However, email notification could not be sent.')
        
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Check if user is admin
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get loan statistics
        stats = {
            'active_loans': Loan.query.filter_by(status='approved').count(),
            'total_disbursed': float(db.session.query(func.sum(Loan.amount)).filter_by(status='approved').scalar() or 0),
            'pending_applications': LoanApplication.query.filter_by(status='pending').count()
        }
        
        # Get loan distribution data
        loan_types = ['School Fees', 'Medical', 'Vacation', 'Funeral', 'Customary']
        loan_distribution = []
        for loan_type in loan_types:
            count = LoanProduct.query.filter(
                LoanProduct.primary_purpose == loan_type.lower().replace(' ', '_')
            ).count()
            loan_distribution.append(count)
        
        # Get recent applications with user info
        recent_applications = LoanApplication.query\
            .join(User)\
            .order_by(LoanApplication.created_at.desc())\
            .limit(5)\
            .all()
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             loan_types=loan_types,
                             loan_distribution=loan_distribution,
                             recent_applications=recent_applications)
                             
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        flash('Error loading dashboard data', 'error')
        return render_template('admin/dashboard.html',
                             stats={'active_loans': 0, 'total_disbursed': 0, 'pending_applications': 0},
                             loan_types=[],
                             loan_distribution=[],
                             recent_applications=[])

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/loans')
@login_required
def admin_loans():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    loans = Loan.query.all()
    return render_template('admin/loans.html', loans=loans)

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Enhanced loan statistics
        total_loans = Loan.query.count()
        active_loans = Loan.query.filter_by(status='approved').count()
        total_amount = db.session.query(func.sum(Loan.amount)).filter_by(status='approved').scalar() or 0
        avg_amount = total_amount / active_loans if active_loans > 0 else 0
        
        # Borrower demographics
        total_borrowers = BorrowerDetails.query.count()
        avg_credit_score = db.session.query(func.avg(BorrowerDetails.credit_score)).scalar() or 0
        employment_types = db.session.query(
            BorrowerDetails.employment_type,
            func.count(BorrowerDetails.id)
        ).group_by(BorrowerDetails.employment_type).all()
        
        # OCR processing statistics
        documents = Document.query.all()
        successful_ocr = Document.query.filter_by(ocr_status='completed').count()
        total_documents = len(documents)
        avg_ocr_confidence = db.session.query(func.avg(Document.ocr_confidence_score)).scalar() or 0
        
        # Repayment statistics
        total_repayments = RepaymentRecord.query.count()
        ontime_payments = RepaymentRecord.query.filter_by(is_late_payment=False).count()
        late_payments = RepaymentRecord.query.filter_by(is_late_payment=True).count()
        
        stats = {
            'active_loans': active_loans,
            'avg_loan_amount': float(avg_amount),
            'total_portfolio': float(total_amount),
            'documents_processed': total_documents,
            'avg_ocr_confidence': float(avg_ocr_confidence * 100),
            'ocr_success_rate': (successful_ocr / total_documents * 100) if total_documents > 0 else 0,
            'total_repayments': total_repayments,
            'ontime_payment_rate': (ontime_payments / total_repayments * 100) if total_repayments > 0 else 0,
            'late_payment_rate': (late_payments / total_repayments * 100) if total_repayments > 0 else 0
        }
        
        # Monthly trends (last 6 months)
        months = []
        amounts = []
        for i in range(5, -1, -1):
            start_date = datetime.utcnow().replace(day=1) - relativedelta(months=i)
            end_date = (start_date + relativedelta(months=1)).replace(hour=23, minute=59, second=59)
            
            month_amount = db.session.query(func.sum(Loan.amount))\
                .filter(Loan.created_at.between(start_date, end_date))\
                .scalar() or 0
                
            months.append(start_date.strftime('%B'))
            amounts.append(float(month_amount))
        
        # Loan type distribution
        loan_types = ['School Fees', 'Medical', 'Vacation', 'Funeral', 'Customary']
        loan_type_distribution = []
        for loan_type in loan_types:
            count = Loan.query.filter(
                Loan.purpose.ilike(f"%{loan_type.lower()}%")
            ).count()
            loan_type_distribution.append(count)
        
        # Document processing time distribution
        processing_times = [0, 0, 0, 0, 0]  # <1s, 1-2s, 2-5s, 5-10s, >10s
        for doc in documents:
            if doc.ocr_status == 'completed':
                processing_time = (doc.uploaded_at - doc.created_at).total_seconds()
                if processing_time < 1:
                    processing_times[0] += 1
                elif processing_time < 2:
                    processing_times[1] += 1
                elif processing_time < 5:
                    processing_times[2] += 1
                elif processing_time < 10:
                    processing_times[3] += 1
                else:
                    processing_times[4] += 1
        
        return render_template(
            'admin/analytics.html',
            stats=stats,
            monthly_labels=months,
            monthly_amounts=amounts,
            loan_types=loan_types,
            loan_type_distribution=loan_type_distribution,
            processing_time_distribution=processing_times
        )
        
    except Exception as e:
        print(f"Analytics error: {str(e)}")
        flash('Error loading analytics data', 'error')
        return render_template(
            'admin/analytics.html',
            stats={
                'active_loans': 0,
                'avg_loan_amount': 0,
                'total_portfolio': 0,
                'documents_processed': 0,
                'avg_ocr_confidence': 0,
                'ocr_success_rate': 0,
                'total_repayments': 0,
                'ontime_payment_rate': 0,
                'late_payment_rate': 0
            },
            monthly_labels=[],
            monthly_amounts=[],
            loan_types=[],
            loan_type_distribution=[],
            processing_time_distribution=[0, 0, 0, 0, 0]
        )

@app.route('/customer-portal')
@login_required
def customer_portal():
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    
    loans = Loan.query.filter_by(user_id=current_user.id).all()
    documents = Document.query.join(Loan).filter(
        Loan.user_id == current_user.id
    ).order_by(Document.uploaded_at.desc()).limit(5).all()
    
    return render_template('customer/portal.html', loans=loans, documents=documents)

@app.route('/application-status')
@login_required
def application_status():
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    
    applications = LoanApplication.query.filter_by(user_id=current_user.id)\
        .order_by(LoanApplication.created_at.desc()).all()
    
    return render_template('customer/application_status.html', applications=applications)
@app.route('/document-upload', methods=['GET', 'POST'])
@login_required
def upload_documents():
    documents = Document.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        if 'document' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
            
        file = request.files['document']
        document_type = request.form.get('document_type')
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if not document_type:
            flash('Please select a document type', 'error')
            return redirect(request.url)
            
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            file.save(file_path)
            
            document = Document(
                user_id=current_user.id,
                document_type=document_type,
                file_name=filename,
                file_path=file_path,
                file_url=file_path,
                ocr_status='pending'
            )
            
            db.session.add(document)
            db.session.commit()
            
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('upload_documents'))
            
        except Exception as e:
            print(f"Error uploading document: {str(e)}")
            flash('Error uploading document. Please try again.', 'error')
            return redirect(request.url)
    
    return render_template('customer/document_upload.html', documents=documents)

@app.route('/upload-application', methods=['GET', 'POST'])
def upload_application():
    if request.method == 'POST':
        if 'application_document' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
            
        file = request.files['application_document']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            flash('Invalid file type. Please upload PDF or image files.', 'error')
            return redirect(request.url)
        
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            file.save(file_path)
            
            document = Document(
                user_id=current_user.id if current_user.is_authenticated else None,
                document_type='loan_application',
                file_name=filename,
                file_path=file_path,
                file_url=url_for('static', filename=f'uploads/{filename}', _external=True),
                ocr_status='pending',
                uploaded_at=datetime.utcnow()
            )
            
            db.session.add(document)
            db.session.flush()
            
            document.process_ocr()
            
            if document.ocr_status == 'failed':
                flash('Error processing document. Please try again.', 'error')
                return redirect(request.url)
            
            if document.ocr_status == 'completed' and document.extracted_data:
                application = LoanApplication(
                    user_id=current_user.id,
                    status='pending'
                )
                db.session.add(application)
                db.session.flush()
                
                document.application_id = application.id
                
                if document.extracted_data:
                    try:
                        # Create PersonalDetails
                        if any(key in document.extracted_data for key in ['surname', 'given_name', 'date_of_birth']):
                            personal = PersonalDetails(
                                loan_application_id=application.id,
                                surname=document.extracted_data.get('surname', ''),
                                given_name=document.extracted_data.get('given_name', ''),
                                date_of_birth=document.extracted_data.get('date_of_birth'),
                                gender=document.extracted_data.get('gender', 'M')[0].upper(),
                                mobile_number=document.extracted_data.get('mobile_number', ''),
                                email=document.extracted_data.get('email', ''),
                                village=document.extracted_data.get('village', ''),
                                district=document.extracted_data.get('district', ''),
                                province=document.extracted_data.get('province', ''),
                                nationality=document.extracted_data.get('nationality', '')
                            )
                            db.session.add(personal)
                        
                        # Create EmploymentDetails
                        if any(key in document.extracted_data for key in ['company_department', 'position', 'file_number']):
                            employment = EmploymentDetails(
                                loan_application_id=application.id,
                                company_department=document.extracted_data.get('company_department', ''),
                                file_number=document.extracted_data.get('file_number', ''),
                                position=document.extracted_data.get('position', ''),
                                postal_address=document.extracted_data.get('postal_address', ''),
                                phone=document.extracted_data.get('phone', ''),
                                date_employed=document.extracted_data.get('date_employed'),
                                paymaster=document.extracted_data.get('paymaster', '')
                            )
                            db.session.add(employment)
                        
                        db.session.commit()
                        
                        # Create user account if not authenticated
                        if not current_user.is_authenticated:
                            # Generate a username from email or use a timestamp
                            email = document.extracted_data.get('email', '')
                            username = email.split('@')[0] if email else f'user_{int(datetime.now().timestamp())}'
                            
                            # Create new user
                            user = User(
                                username=username,
                                email=email,
                                password_hash=generate_password_hash('password1234'),  # Temporary password
                                role='borrower',
                                client_number=User.generate_client_number(),
                                is_application_created=True
                            )
                            db.session.add(user)
                            db.session.commit()
                            
                            # Update document with user_id
                            document.user_id = user.id
                            db.session.commit()
                            
                            # Send registration email
                            try:
                                send_registration_email(email, username, is_application=True)
                            except Exception as e:
                                print(f"Failed to send registration email: {str(e)}")
                            
                            # Log in the user
                            login_user(user)
                        
                        flash('Application submitted successfully! Please upload your supporting documents.', 'success')
                        return redirect(url_for('upload_documents'))  # This should now work with login_required
                        
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error saving application details: {str(e)}")
                        flash('Error saving application details. Please try again.', 'error')
                        return redirect(request.url)
            else:
                flash('Could not extract data from document. Please try again.', 'error')
                return redirect(request.url)
                
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            flash('Error processing file. Please try again.', 'error')
            return redirect(request.url)
    
    return render_template('customer/upload_application.html')

if __name__ == '__main__':
    print("Initializing application...")
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            
            print("Checking for admin user...")
            admin = User.query.filter_by(username='DevAdmin').first()
            if not admin:
                print("Creating admin user...")
                admin = User(
                    username='DevAdmin',
                    email='admin@knrfinancial.com',
                    full_name='System Administrator',
                    password_hash=generate_password_hash('password1234'),
                    role='admin',
                    client_number=User.generate_client_number()
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully")
            else:
                print("Admin user already exists")
            
            print("Starting Flask application...")
            app.run(host='0.0.0.0', port=5000, debug=True)
        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            raise