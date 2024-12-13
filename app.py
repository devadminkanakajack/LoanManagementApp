from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import os

app = Flask(__name__)
from flask_mail import Mail, Message

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
# Configure database with SSL and connection pooling
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if not database_url.endswith('?sslmode=require'):
        database_url += '?sslmode=require'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'pool_recycle': 280,
    'pool_timeout': 20,
    'max_overflow': 2
}

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_number = db.Column(db.String(10), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    department = db.Column(db.String(50), nullable=True)
    is_application_created = db.Column(db.Boolean, default=False)
    password_changed = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False, default='borrower')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    loans = db.relationship('Loan', backref='user', lazy=True)

    @staticmethod
    def generate_client_number():
        """Generate the next client number in sequence KNRFS00001"""
        last_user = User.query.order_by(User.client_number.desc()).first()
        if not last_user:
            return 'KNRFS00001'
        last_number = int(last_user.client_number[5:])
        return f'KNRFS{str(last_number + 1).zfill(5)}'

class PersonalDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
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

class LoanProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    purposes = db.Column(db.JSON, nullable=False)  # Array of selected purposes: ['school_fees', 'medical', etc]
    primary_purpose = db.Column(db.String(50), nullable=False)  # Main purpose
    description = db.Column(db.Text)

class FinancialDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    loan_amount = db.Column(db.Numeric(10, 2), nullable=False)
    fortnightly_repayment = db.Column(db.Numeric(10, 2), nullable=False)
    number_of_fortnights = db.Column(db.Integer, nullable=False)
    total_loan_repayable = db.Column(db.Numeric(10, 2), nullable=False)
    gross_salary = db.Column(db.Numeric(10, 2), nullable=False)
    net_salary = db.Column(db.Numeric(10, 2), nullable=False)

class LoanFundingDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    bank = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    bsb_code = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(200), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    account_type = db.Column(db.String(20), nullable=False)  # savings/cheque

class LoanBreakUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    loan_amount = db.Column(db.Numeric(10, 2), nullable=False)
    existing_loan = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    net_loan_amount = db.Column(db.Numeric(10, 2), nullable=False)

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    signature_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    personal_details = db.relationship('PersonalDetails', backref='application', uselist=False)
    employment_details = db.relationship('EmploymentDetails', backref='application', uselist=False)
    residential_address = db.relationship('ResidentialAddress', backref='application', uselist=False)
    loan_product = db.relationship('LoanProduct', backref='application', uselist=False)
    financial_details = db.relationship('FinancialDetails', backref='application', uselist=False)
    funding_details = db.relationship('LoanFundingDetails', backref='application', uselist=False)
    break_up = db.relationship('LoanBreakUp', backref='application', uselist=False)
    documents = db.relationship('Document', backref='application', lazy=True)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    term = db.Column(db.Integer, nullable=False)  # in fortnights
    status = db.Column(db.String(20), nullable=False, default='pending')
    purpose = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    documents = db.relationship('Document', backref='loan', lazy=True)

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=True)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=True)
    document_type = db.Column(db.String(50), nullable=False)  # payslip, employment_confirmation, data_entry, variation_advice, identification
    file_path = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ocr_status = db.Column(db.String(20), nullable=False, default='pending')
    ocr_text = db.Column(db.Text)
    extracted_data = db.Column(db.JSON)

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
                
                # Extract structured data based on document type
                extracted_data = {}
                
                if self.document_type == 'loan_application':
                    # Personal Details patterns
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
                        
                        # Employment Details
                        'company_department': r'(?:Company|Department):?\s*([^\n]+)',
                        'file_number': r'File\s+Number:?\s*([^\n]+)',
                        'position': r'Position:?\s*([^\n]+)',
                        'postal_address': r'Postal\s+Address:?\s*([^\n]+)',
                        'phone': r'Phone:?\s*([\d\s\-+]+)',
                        'date_employed': r'Date\s+Employed:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                        'paymaster': r'Paymaster:?\s*([^\n]+)',
                        
                        # Residential Address
                        'lot': r'Lot:?\s*([^\n]+)',
                        'section': r'Section:?\s*([^\n]+)',
                        'suburb': r'Suburb:?\s*([^\n]+)',
                        'street_name': r'Street\s+Name:?\s*([^\n]+)',
                        'marital_status': r'Marital\s+Status:?\s*(Single|Married|Divorced|Widowed)',
                        'spouse_last_name': r'Spouse\s+Last\s+Name:?\s*([^\n]+)',
                        'spouse_first_name': r'Spouse\s+First\s+Name:?\s*([^\n]+)',
                        'spouse_employer_name': r'Spouse\s+Employer:?\s*([^\n]+)',
                        'spouse_contact': r'Spouse\s+Contact:?\s*([\d\s\-+]+)',
                        
                        # Financial Details
                        'loan_amount': r'Loan\s+Amount:?\s*\$?\s*([\d,]+\.?\d*)',
                        'fortnightly_repayment': r'Fortnightly\s+Repayment:?\s*\$?\s*([\d,]+\.?\d*)',
                        'number_of_fortnights': r'Number\s+of\s+Fortnights:?\s*(\d+)',
                        'total_loan_repayable': r'Total\s+Loan\s+Repayable:?\s*\$?\s*([\d,]+\.?\d*)',
                        'gross_salary': r'Gross\s+Salary:?\s*\$?\s*([\d,]+\.?\d*)',
                        'net_salary': r'Net\s+Salary:?\s*\$?\s*([\d,]+\.?\d*)',
                        
                        # Loan Purposes (detecting marked/selected items)
                        'school_fees': r'[\☒\✓\×\*]\s*School\s+Fees|School\s+Fees\s*[\☒\✓\×\*]',
                        'medical': r'[\☒\✓\×\*]\s*Medical|Medical\s*[\☒\✓\×\*]',
                        'vacation': r'[\☒\✓\×\*]\s*Vacation|Vacation\s*[\☒\✓\×\*]',
                        'funeral': r'[\☒\✓\×\*]\s*Funeral|Funeral\s*[\☒\✓\×\*]',
                        'customary': r'[\☒\✓\×\*]\s*Customary|Customary\s*[\☒\✓\×\*]',
                        'others': r'[\☒\✓\×\*]\s*Others?|Others?\s*[\☒\✓\×\*]',
                        'product_description': r'Purpose(?:\s+Description)?:?\s*([^\n]+)',
                        
                        # Bank Details
                        'bank': r'Bank:?\s*([^\n]+)',
                        'branch': r'Branch:?\s*([^\n]+)',
                        'bsb_code': r'BSB\s+Code:?\s*([^\n]+)',
                        'account_name': r'Account\s+Name:?\s*([^\n]+)',
                        'account_number': r'Account\s+Number:?\s*([^\n]+)',
                        'account_type': r'Account\s+Type:?\s*(Savings|Cheque)'
                    }
                    
                    # Extract all fields
                    extracted_data = {}
                    for field, pattern in patterns.items():
                        match = re.search(pattern, self.ocr_text, re.IGNORECASE)
                        if match:
                            value = match.group(1).strip()
                            # Convert specific fields to appropriate types
                            if field in ['loan_amount', 'fortnightly_repayment', 'total_loan_repayable', 'gross_salary', 'net_salary']:
                                try:
                                    value = float(value.replace(',', ''))
                                except ValueError:
                                    pass
                            elif field in ['number_of_fortnights']:
                                try:
                                    value = int(value)
                                except ValueError:
                                    pass
                            extracted_data[field] = value
                    
                    if name_match:
                        extracted_data['name'] = name_match.group(1).strip()
                    if email_match:
                        extracted_data['email'] = email_match.group(1).strip()
                    if phone_match:
                        extracted_data['phone'] = phone_match.group(1).strip()
                    if address_match:
                        address = address_match.group(1).strip()
                        # Try to parse address components
                        address_parts = address.split(',')
                        if len(address_parts) >= 3:
                            extracted_data['street_name'] = address_parts[0].strip()
                            extracted_data['suburb'] = address_parts[1].strip()
                            extracted_data['district'] = address_parts[2].strip()
                    if loan_match:
                        extracted_data['loan_amount'] = float(loan_match.group(1).replace(',', ''))
                    if purpose_match:
                        purpose = purpose_match.group(1).strip().lower()
                        # Map purpose to product type
                        purpose_mapping = {
                            'school': 'school_fees',
                            'education': 'school_fees',
                            'medical': 'medical',
                            'health': 'medical',
                            'vacation': 'vacation',
                            'holiday': 'vacation',
                            'funeral': 'funeral',
                            'customary': 'customary'
                        }
                        for key, value in purpose_mapping.items():
                            if key in purpose:
                                extracted_data['product_type'] = value
                                break
                        else:
                            extracted_data['product_type'] = 'others'
                    if term_match:
                        term_months = int(term_match.group(1))
                        extracted_data['number_of_fortnights'] = term_months * 2
                
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
                
                elif self.document_type == 'employment_confirmation':
                    # Extract employment details
                    position_pattern = r'Position:?\s*([^\n]+)'
                    date_pattern = r'Date\s+Employed:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
                    department_pattern = r'Department:?\s*([^\n]+)'
                    
                    position_match = re.search(position_pattern, self.ocr_text, re.IGNORECASE)
                    date_match = re.search(date_pattern, self.ocr_text, re.IGNORECASE)
                    department_match = re.search(department_pattern, self.ocr_text, re.IGNORECASE)
                    
                    if position_match:
                        extracted_data['position'] = position_match.group(1).strip()
                    if date_match:
                        extracted_data['date_employed'] = date_match.group(1)
                    if department_match:
                        extracted_data['company_department'] = department_match.group(1).strip()
                
                self.extracted_data = extracted_data
                
            elif self.file_path.lower().endswith('.pdf'):
                # TODO: Add PDF processing
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
        return redirect(url_for('dashboard'))
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
        
        # Send registration confirmation email
        try:
            send_registration_email(email, username)
            flash('Registration successful! Please check your email for confirmation.')
        except Exception as e:
            flash('Registration successful! However, email notification could not be sent.')
        
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

def create_user_from_application(personal_details):
    """Create a new user account from loan application data"""
    # Generate username from email
    email = personal_details.email
    username = email.split('@')[0]
@app.route('/application-status')
@login_required
def application_status():
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    
    applications = LoanApplication.query.filter_by(user_id=current_user.id)\
        .order_by(LoanApplication.created_at.desc()).all()
    
    return render_template('customer/application_status.html', applications=applications)

    
    # Check if username exists and modify if needed
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    # Create user with default password
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash('password1234'),
        phone_number=personal_details.mobile_number,
        role='borrower',
        is_application_created=True,
        client_number=User.generate_client_number()
    )
    
    db.session.add(user)
    db.session.flush()
    
    # Send email with credentials
    send_credentials_email(email, username)
    
    return user

def send_credentials_email(email, username):
    """Send email with login credentials"""
    # TODO: Implement email sending functionality
    print(f"Sending credentials email to {email}")
    print(f"Username: {username}")
    print(f"Password: password1234")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'borrower':
        return redirect(url_for('customer_portal'))
    return render_template('dashboard.html')

@app.route('/customer-portal')
@login_required
def customer_portal():
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    
    # Get user's loans
    loans = Loan.query.filter_by(user_id=current_user.id).all()
    
    # Get user's documents
    documents = Document.query.join(Loan).filter(
        Loan.user_id == current_user.id
    ).order_by(Document.uploaded_at.desc()).limit(5).all()
    
    return render_template('customer/portal.html', loans=loans, documents=documents)

@app.route('/upload-application', methods=['GET', 'POST'])
@login_required
def upload_application():
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        if 'application_document' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
            
        file = request.files['application_document']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure the file is a valid type
            allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
            if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
                flash('Invalid file type. Please upload PDF or image files.', 'error')
                return redirect(request.url)
            
            try:
                file.save(file_path)
                document = Document(
                    document_type='loan_application',
                    file_path=file_path
                )
                
                db.session.add(document)
                db.session.flush()
                
                # Process OCR immediately
                document.process_ocr()
                
                if document.ocr_status == 'completed' and document.extracted_data:
                    # Create new loan application with extracted data
                    application = LoanApplication(user_id=current_user.id)
                    db.session.add(application)
                    db.session.flush()
                    
                    # Create personal details
                    if any(key in document.extracted_data for key in ['name', 'date_of_birth', 'gender', 'mobile_number']):
                        personal = PersonalDetails(
                            loan_application_id=application.id,
                            name=document.extracted_data.get('name', ''),
                            date_of_birth=datetime.strptime(document.extracted_data.get('date_of_birth', '2000-01-01'), '%d/%m/%Y').date(),
                            gender=document.extracted_data.get('gender', 'M')[0].upper(),
                            mobile_number=document.extracted_data.get('mobile_number', ''),
                            email=document.extracted_data.get('email', ''),
                            village=document.extracted_data.get('village', ''),
                            district=document.extracted_data.get('district', ''),
                            province=document.extracted_data.get('province', ''),
                            nationality=document.extracted_data.get('nationality', '')
                        )
                        db.session.add(personal)
                    
                    # Create employment details
                    if any(key in document.extracted_data for key in ['company_department', 'position', 'file_number']):
                        employment = EmploymentDetails(
                            loan_application_id=application.id,
                            company_department=document.extracted_data.get('company_department', ''),
                            file_number=document.extracted_data.get('file_number', ''),
                            position=document.extracted_data.get('position', ''),
                            postal_address=document.extracted_data.get('postal_address', ''),
                            phone=document.extracted_data.get('phone', ''),
                            date_employed=datetime.strptime(document.extracted_data.get('date_employed', '2000-01-01'), '%d/%m/%Y').date(),
                            paymaster=document.extracted_data.get('paymaster', '')
                        )
                        db.session.add(employment)
                    
                    # Create residential address
                    if any(key in document.extracted_data for key in ['lot', 'section', 'suburb']):
                        residential = ResidentialAddress(
                            loan_application_id=application.id,
                            lot=document.extracted_data.get('lot', ''),
                            section=document.extracted_data.get('section', ''),
                            suburb=document.extracted_data.get('suburb', ''),
                            street_name=document.extracted_data.get('street_name', ''),
                            marital_status=document.extracted_data.get('marital_status', 'single').lower(),
                            spouse_last_name=document.extracted_data.get('spouse_last_name', ''),
                            spouse_first_name=document.extracted_data.get('spouse_first_name', ''),
                            spouse_employer_name=document.extracted_data.get('spouse_employer_name', ''),
                            spouse_contact=document.extracted_data.get('spouse_contact', '')
                        )
                        db.session.add(residential)
                    
                    # Create loan product with extracted purposes
                    purposes = []
                    purpose_fields = ['school_fees', 'medical', 'vacation', 'funeral', 'customary', 'others']
                    
                    # Extract all marked purposes
                    for field in purpose_fields:
                        if field in document.extracted_data:
                            purposes.append(field)
                    
                    # If no purposes were detected but we have a description, add as 'others'
                    if not purposes and document.extracted_data.get('product_description'):
                        purposes.append('others')
                    
                    if purposes:
                        # Determine primary purpose from the first detected purpose or from description
                        primary_purpose = purposes[0]
                        description = document.extracted_data.get('product_description', '').strip()
                        
                        # If description contains keywords, use it to validate/adjust primary purpose
                        description_lower = description.lower()
                        for purpose in purpose_fields:
                            if purpose.replace('_', ' ') in description_lower:
                                primary_purpose = purpose
                                break
                        
                        product = LoanProduct(
                            loan_application_id=application.id,
                            purposes=purposes,
                            primary_purpose=primary_purpose,
                            description=description
                        )
                        db.session.add(product)
                    
                    # Create financial details
                    if any(key in document.extracted_data for key in ['loan_amount', 'gross_salary']):
                        financial = FinancialDetails(
                            loan_application_id=application.id,
                            loan_amount=document.extracted_data.get('loan_amount', 0.0),
                            fortnightly_repayment=document.extracted_data.get('fortnightly_repayment', 0.0),
                            number_of_fortnights=document.extracted_data.get('number_of_fortnights', 0),
                            total_loan_repayable=document.extracted_data.get('total_loan_repayable', 0.0),
                            gross_salary=document.extracted_data.get('gross_salary', 0.0),
                            net_salary=document.extracted_data.get('net_salary', 0.0)
                        )
                        db.session.add(financial)
                    
                    # Link document to application
                    document.application_id = application.id
                    
                    db.session.commit()
                    flash('Application submitted successfully! You can now upload supporting documents.', 'success')
                    return redirect(url_for('upload_document'))
                else:
                    flash('Error processing application document. Please ensure all required information is clearly visible.', 'error')
                    return redirect(request.url)
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing document: {str(e)}', 'error')
                return redirect(request.url)
    
    return render_template('customer/upload_application.html')

@app.route('/apply-loan')
@login_required
def apply_loan():
    # Redirect all loan applications to the document upload route
    return redirect(url_for('upload_application'))

    if request.method == 'POST':
        try:
            # Create new loan application
            application = LoanApplication(user_id=current_user.id)
            db.session.add(application)
            db.session.flush()  # Get the application ID

            # Personal Details
            personal = PersonalDetails(
                loan_application_id=application.id,
                name=request.form['name'],
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date(),
                gender=request.form['gender'],
                mobile_number=request.form['mobile_number'],
                email=request.form['email'],
                village=request.form['village'],
                district=request.form['district'],
                province=request.form['province'],
                nationality=request.form['nationality']
            )
            db.session.add(personal)

            # Employment Details
            employment = EmploymentDetails(
                loan_application_id=application.id,
                company_department=request.form['company_department'],
                file_number=request.form['file_number'],
                position=request.form['position'],
                postal_address=request.form['postal_address'],
                phone=request.form['phone'],
                date_employed=datetime.strptime(request.form['date_employed'], '%Y-%m-%d').date(),
                paymaster=request.form['paymaster']
            )
            db.session.add(employment)

            # Residential Address
            residential = ResidentialAddress(
                loan_application_id=application.id,
                lot=request.form['lot'],
                section=request.form['section'],
                suburb=request.form['suburb'],
                street_name=request.form['street_name'],
                marital_status=request.form['marital_status'],
                spouse_last_name=request.form.get('spouse_last_name'),
                spouse_first_name=request.form.get('spouse_first_name'),
                spouse_employer_name=request.form.get('spouse_employer_name'),
                spouse_contact=request.form.get('spouse_contact')
            )
            db.session.add(residential)

            # Loan Product
            product = LoanProduct(
                loan_application_id=application.id,
                product_type=request.form['product_type'],
                description=request.form.get('product_description')
            )
            db.session.add(product)

            # Financial Details
            financial = FinancialDetails(
                loan_application_id=application.id,
                loan_amount=float(request.form['loan_amount']),
                fortnightly_repayment=float(request.form['fortnightly_repayment']),
                number_of_fortnights=int(request.form['number_of_fortnights']),
                total_loan_repayable=float(request.form['total_loan_repayable']),
                gross_salary=float(request.form['gross_salary']),
                net_salary=float(request.form['net_salary'])
            )
            db.session.add(financial)

            # Loan Funding Details
            funding = LoanFundingDetails(
                loan_application_id=application.id,
                bank=request.form['bank'],
                branch=request.form['branch'],
                bsb_code=request.form['bsb_code'],
                account_name=request.form['account_name'],
                account_number=request.form['account_number'],
                account_type=request.form['account_type']
            )
            db.session.add(funding)

            # Loan Break-Up
            breakup = LoanBreakUp(
                loan_application_id=application.id,
                loan_amount=float(request.form['breakup_loan_amount']),
                existing_loan=float(request.form['existing_loan']),
                net_loan_amount=float(request.form['net_loan_amount'])
            )
            db.session.add(breakup)

            # Process and save documents
            document_types = {
                'payslip_1': 'payslip',
                'payslip_2': 'payslip',
                'employment_letter': 'employment_confirmation',
                'data_entry_form': 'data_entry',
                'variation_form': 'variation_advice',
                'identification': 'identification'
            }

            for form_name, doc_type in document_types.items():
                if form_name in request.files:
                    file = request.files[form_name]
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)

                        document = Document(
                            application_id=application.id,
                            document_type=doc_type,
                            file_path=file_path
                        )
                        db.session.add(document)
                        # Process OCR in background
                        document.process_ocr()

            db.session.commit()
            flash('Loan application submitted successfully', 'success')
            return redirect(url_for('customer_portal'))

        except Exception as e:
            db.session.rollback()
            print(f"Error submitting loan application: {str(e)}")
            flash('Error submitting loan application. Please try again.', 'error')
            return redirect(url_for('apply_loan'))

    return render_template('customer/loan_application.html', prefill_data=prefill_data)

@app.route('/view-loan/<int:loan_id>')
@login_required
def view_loan_details(loan_id):
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    loan = Loan.query.filter_by(id=loan_id, user_id=current_user.id).first_or_404()
    return render_template('customer/loan_details.html', loan=loan)

@app.route('/upload-document', methods=['GET', 'POST'])
@login_required
def upload_document():
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    
    # Get user's active loans
    loans = Loan.query.filter_by(user_id=current_user.id).all()
    documents = Document.query.join(Loan).filter(
        Loan.user_id == current_user.id
    ).order_by(Document.uploaded_at.desc()).all()
    
    if request.method == 'POST':
        if 'document' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
            
        file = request.files['document']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure the file is a valid type
            allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
            if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
                flash('Invalid file type. Please upload PDF or image files.', 'error')
                return redirect(request.url)
            
            try:
                file.save(file_path)
                document_type = request.form.get('document_type')
                loan_id = request.form.get('loan_id')
                
                new_document = Document(
                    loan_id=loan_id,
                    document_type=document_type,
                    file_path=file_path
                )
                
                db.session.add(new_document)
                db.session.commit()
                
                # Process OCR after saving
                new_document.process_ocr()
                
                flash('Document uploaded successfully. OCR processing initiated.', 'success')
                return redirect(url_for('customer_portal'))
                
            except Exception as e:
                flash(f'Error uploading document: {str(e)}', 'error')
                return redirect(request.url)
                
    return render_template('customer/document_upload.html', loans=loans, documents=documents)


@app.route('/view-document/<int:document_id>')
@login_required
def view_document(document_id):
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    document = Document.query.join(Loan).filter(
        Document.id == document_id,
        Loan.user_id == current_user.id
    ).first_or_404()
    return render_template('customer/view_document.html', document=document)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)