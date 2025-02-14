from flask_login import UserMixin
from datetime import datetime
from extensions import db  # Import db from extensions instead of creating it here

class User(UserMixin, db.Model):
    """User model for authentication and basic user information"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='borrower')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    borrower = db.relationship('Borrower', backref='user', uselist=False)
    loans = db.relationship('Loan', backref='user', lazy=True)

class Borrower(db.Model):
    """Model for storing borrower information"""
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
    
    # Banking Information
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    bsb_code = db.Column(db.String(10))
    account_type = db.Column(db.String(20))
    
    # Metadata
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    loans = db.relationship('Loan', backref='borrower', lazy=True)
    
    def __repr__(self):
        return f'<Borrower {self.full_name}>'
    
    def to_dict(self):
        """Convert borrower object to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'employment_status': self.employment_status,
            'monthly_income': str(self.monthly_income),
            'created_at': self.created_at.isoformat()
        }

class Loan(db.Model):
    """Model for storing loan information"""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrowers.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    term = db.Column(db.Integer)
    interest_rate = db.Column(db.Numeric(5, 2))
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Text, default='pending')
    purpose = db.Column(db.Text)
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by])
    repayments = db.relationship('RepaymentRecord', backref='loan', lazy=True)
    
    def to_dict(self):
        """Convert loan object to dictionary for API responses"""
        return {
            'id': self.id,
            'borrower_id': self.borrower_id,
            'amount': str(self.amount),
            'term': self.term,
            'interest_rate': str(self.interest_rate),
            'status': self.status,
            'purpose': self.purpose,
            'created_at': self.created_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }

class RepaymentRecord(db.Model):
    """Model for tracking loan repayments"""
    __tablename__ = 'repayment_records'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    is_late_payment = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    """Model for storing document information"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_url = db.Column(db.String(500))
    ocr_status = db.Column(db.String(20), default='pending')
    ocr_confidence_score = db.Column(db.Float)
    extracted_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_at = db.Column(db.DateTime)
