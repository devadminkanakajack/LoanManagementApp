from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
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
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='borrower')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    loans = db.relationship('Loan', backref='user', lazy=True)

class Loan(db.Model):
    __tablename__ = 'loan'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    term = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    purpose = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    documents = db.relationship('Document', backref='loan', lazy=True)

class Document(db.Model):
    __tablename__ = 'document'
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
        department = request.form.get('department')

        # Validate required fields
        if not all([username, email, password, full_name, phone_number, address, department]):
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
        
        try:
            # Check if username exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return redirect(url_for('register'))
            
            # Check if email exists
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return redirect(url_for('register'))
            
            # Create new user
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password,
                full_name=full_name,
                phone_number=phone_number,
                address=address,
                department=department,
                role='borrower'
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html')

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

@app.route('/logout', methods=['POST'])
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
    
@app.route('/apply-loan')
@login_required
def apply_loan():
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    return render_template('customer/loan_application.html')

@app.route('/view-loan/<int:loan_id>')
@login_required
def view_loan_details(loan_id):
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    loan = Loan.query.filter_by(id=loan_id, user_id=current_user.id).first_or_404()
    return render_template('customer/loan_details.html', loan=loan)

@app.route('/upload-document')
@login_required
def upload_document():
    if current_user.role != 'borrower':
        return redirect(url_for('dashboard'))
    return render_template('customer/document_upload.html')

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
    # Get user's loans
    loans = Loan.query.filter_by(user_id=current_user.id).all()
    
    # Get user's documents
    documents = Document.query.join(Loan).filter(Loan.user_id == current_user.id).order_by(Document.uploaded_at.desc()).limit(5).all()
    
    return render_template('customer/portal.html', loans=loans, documents=documents)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
