from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
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
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='borrower')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    loans = db.relationship('Loan', backref='user', lazy=True)

class PersonalDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
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
    product_type = db.Column(db.String(50), nullable=False)  # school_fees, medical, vacation, funeral, customary, others
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
                
                if self.document_type == 'payslip':
                    # Extract salary information
                    salary_pattern = r'Gross\s+Salary:?\s*\$?\s*([\d,]+\.?\d*)'
                    salary_match = re.search(salary_pattern, self.ocr_text, re.IGNORECASE)
                    if salary_match:
                        extracted_data['gross_salary'] = float(salary_match.group(1).replace(',', ''))
                
                elif self.document_type == 'employment_confirmation':
                    # Extract employment details
                    position_pattern = r'Position:?\s*([^\n]+)'
                    date_pattern = r'Date\s+Employed:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
                    
                    position_match = re.search(position_pattern, self.ocr_text, re.IGNORECASE)
                    date_match = re.search(date_pattern, self.ocr_text, re.IGNORECASE)
                    
                    if position_match:
                        extracted_data['position'] = position_match.group(1).strip()
                    if date_match:
                        extracted_data['date_employed'] = date_match.group(1)
                
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
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        department = request.form.get('department')
        
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
            full_name=full_name,
            phone_number=phone_number,
            address=address,
            department=department,
            role='borrower'
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

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

@app.route('/apply-loan', methods=['GET', 'POST'])
@login_required
def apply_loan():
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))

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

    return render_template('customer/loan_application.html')

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