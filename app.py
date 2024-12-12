from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable is required")

# Ensure the URL starts with postgresql:// instead of postgres://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='borrower')
    full_name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    loans = db.relationship('Loan', backref='user', lazy=True)

class Borrower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    employment_status = db.Column(db.String(50), nullable=False)
    monthly_income = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship('User', backref='borrower_profile', uselist=False)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    term = db.Column(db.Integer, nullable=False)  # in months
    status = db.Column(db.String(20), nullable=False, default='pending')
    purpose = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    documents = db.relationship('Document', backref='loan', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    ocr_status = db.Column(db.String(20), default='pending')
    ocr_result = db.Column(db.JSON)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'borrower':
            return redirect(url_for('customer_portal'))
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'borrower':
        return redirect(url_for('customer_portal'))
    return render_template('dashboard.html')

@app.route('/customer-portal')
def customer_portal():
    if current_user.is_authenticated:
        if current_user.role != 'borrower':
            return redirect(url_for('dashboard'))
        documents = Document.query.filter_by(user_id=current_user.id).all()
        return render_template('customer/document_upload.html', documents=documents)
    return render_template('customer/document_upload.html', documents=[])

@app.route('/upload-document', methods=['POST'])
@login_required
def upload_document():
    if 'document' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('customer_portal'))
    
    file = request.files['document']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('customer_portal'))
    
    if file and allowed_file(file.filename):
        try:
            # Save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Create document record
            document = Document(
                filename=filename,
                document_type=request.form.get('document_type'),
                user_id=current_user.id,
                ocr_status='pending'
            )
            db.session.add(document)
            db.session.commit()
            
            # Process OCR in background (for demo, we'll do it synchronously)
            process_document_ocr(document.id, file_path)
            
            flash('Document uploaded successfully', 'success')
        except Exception as e:
            app.logger.error(f"Error uploading document: {str(e)}")
            flash('Error uploading document', 'error')
    else:
        flash('Invalid file type', 'error')
    
    return redirect(url_for('customer_portal'))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_document_ocr(document_id, file_path):
    try:
        # For now, we'll just store the document without OCR
        # Later we can implement cloud OCR service
        document = Document.query.get(document_id)
        if document:
            document.ocr_status = 'pending'
            document.ocr_result = {'message': 'OCR processing will be available soon'}
            db.session.commit()
            
        app.logger.info(f"Document {document_id} stored successfully, OCR processing skipped")
    except Exception as e:
        app.logger.error(f"Document processing error: {str(e)}")
        document = Document.query.get(document_id)
        if document:
            document.ocr_status = 'failed'
            db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        employment_status = request.form.get('employment_status')
        monthly_income = request.form.get('monthly_income')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        try:
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role='borrower',
                full_name=full_name
            )
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Create borrower profile
            borrower = Borrower(
                user_id=user.id,
                phone_number=phone_number,
                address=address,
                employment_status=employment_status,
                monthly_income=float(monthly_income)
            )
            db.session.add(borrower)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('register'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
