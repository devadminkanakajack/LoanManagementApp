# Standard library imports
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Third-party imports
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func, or_

# Local imports
from extensions import db, login_manager, mail, migrate
from models import User, Borrower, Loan, RepaymentRecord, Document
from modules.analytics import bp as analytics_bp
from modules.borrowers import bp as borrowers_bp
from config import config
from logging_config import setup_logging

def secure_filename_with_timestamp(filename):
    """Generate a secure filename with timestamp."""
    base = secure_filename(filename)
    name, ext = os.path.splitext(base)
    return f"{name}_{int(time.time())}{ext}"

def create_app(config_name=None):
    """Application factory function."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].validate_config()
    
    # Setup logging
    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Setup rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[f"{app.config['RATELIMIT_MAX_REQUESTS']} per {app.config['RATELIMIT_WINDOW']} seconds"]
    )
    
    # Register blueprints
    app.register_blueprint(analytics_bp)
    app.register_blueprint(borrowers_bp)
    
    # Register error handlers
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {
            "error": "ratelimit exceeded",
            "message": str(e.description)
        }, 429
    
    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal error: {str(e)}")
        db.session.rollback()
        return {
            "error": "internal server error",
            "message": "An unexpected error occurred"
        }, 500

    # Ensure upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Register routes and other app setup
    register_routes(app)

    return app

def register_routes(app):
    """Register all routes with the application"""
    # ...existing route definitions (index, login, register, etc)...
    # Move all your existing route handlers here, keeping their code unchanged
    
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
                'pending_applications': Loan.query.filter_by(status='pending').count()
            }
            
            # Get loan distribution data
            loan_types = ['School Fees', 'Medical', 'Vacation', 'Funeral', 'Customary']
            loan_distribution = []
            for loan_type in loan_types:
                count = Loan.query.filter(
                    Loan.purpose.ilike(f"%{loan_type.lower()}%")
                ).count()
                loan_distribution.append(count)
            
            # Get recent applications with user info
            recent_applications = Loan.query\
                .join(User)\
                .order_by(Loan.created_at.desc())\
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
            total_borrowers = Borrower.query.count()
            employment_types = db.session.query(
                Borrower.employment_type,
                func.count(Borrower.id)
            ).group_by(Borrower.employment_type).all()
            
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
        
        applications = Loan.query.filter_by(user_id=current_user.id)\
            .order_by(Loan.created_at.desc()).all()
        
        return render_template('customer/application_status.html', applications=applications)

    @app.route('/document-upload', methods=['GET', 'POST'])
    @login_required
    def upload_documents():
        try:
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
                
                if not allowed_file(file.filename):
                    flash('Invalid file type', 'error')
                    return redirect(request.url)
                
                if not document_type:
                    flash('Please select a document type', 'error')
                    return redirect(request.url)
                    
                try:
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Ensure upload directory exists
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
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
                    db.session.rollback()
                    print(f"Error uploading document: {str(e)}")
                    flash('Error uploading document. Please try again.', 'error')
                    return redirect(request.url)
            
            return render_template('customer/document_upload.html', documents=documents)
        except Exception as e:
            print(f"Error in upload_documents: {str(e)}")
            flash('An unexpected error occurred', 'error')
            return redirect(url_for('index'))

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
                    loan = Loan(
                        user_id=current_user.id,
                        status='pending',
                        amount=0,  # Will be updated later
                        purpose='pending review'
                    )
                    db.session.add(loan)
                    db.session.flush()
                    
                    document.loan_id = loan.id
                    
                    if document.extracted_data:
                        try:
                            # Update or create borrower
                            borrower = Borrower.query.filter_by(user_id=current_user.id).first()
                            if not borrower:
                                borrower = Borrower(
                                    user_id=current_user.id,
                                    full_name=f"{document.extracted_data.get('surname', '')} {document.extracted_data.get('given_name', '')}",
                                    email=document.extracted_data.get('email', ''),
                                    phone=document.extracted_data.get('mobile_number', ''),
                                    position=document.extracted_data.get('position', ''),
                                    department=document.extracted_data.get('company_department', ''),
                                    employer_name=document.extracted_data.get('paymaster', '')
                                )
                                db.session.add(borrower)

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

    @app.route('/upload', methods=['POST'])
    @login_required
    def upload_file():
        try:
            if 'file' not in request.files:
                app.logger.warning("No file part in request")
                return jsonify({"error": "No file part"}), 400
                
            file = request.files['file']
            if file.filename == '':
                app.logger.warning("No selected file")
                return jsonify({"error": "No selected file"}), 400
                
            if not allowed_file(file.filename):
                app.logger.warning(f"Invalid file type: {file.filename}")
                return jsonify({"error": "Invalid file type"}), 400
                
            filename = secure_filename_with_timestamp(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure upload directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save file
            file.save(filepath)
            app.logger.info(f"File uploaded successfully: {filename}")
            
            return jsonify({
                "message": "File uploaded successfully",
                "filename": filename
            }), 200
            
        except Exception as e:
            app.logger.error(f"Error uploading file: {str(e)}")
            return jsonify({"error": "Failed to upload file"}), 500

    def require_api_key(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            if api_key and api_key == os.getenv('API_KEY'):
                return f(*args, **kwargs)
            return jsonify({'message': 'Invalid or missing API key'}), 401
        return decorated

    # API endpoints
    @app.route('/api/v1/loans', methods=['GET'])
    @require_api_key
    def api_get_loans():
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('limit', 10))
            status = request.args.get('status')

            query = Loan.query
            if status:
                query = query.filter_by(status=status)

            loans = query.paginate(page=page, per_page=per_page)
            
            return jsonify({
                'data': [loan.to_dict() for loan in loans.items],
                'pagination': {
                    'page': loans.page,
                    'pages': loans.pages,
                    'total': loans.total
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/v1/borrowers', methods=['GET'])
    @require_api_key
    def api_get_borrowers():
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('limit', 10))
            search = request.args.get('search')

            query = Borrower.query
            if search:
                query = query.filter(
                    or_(
                        Borrower.full_name.ilike(f'%{search}%'),
                        Borrower.email.ilike(f'%{search}%')
                    )
                )

            borrowers = query.paginate(page=page, per_page=per_page)
            
            return jsonify({
                'data': [borrower.to_dict() for borrower in borrowers.items],
                'pagination': {
                    'page': borrowers.page,
                    'pages': borrowers.pages,
                    'total': borrowers.total
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Create the application instance
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        retry_count = 3
        while retry_count > 0:
            try:
                app.logger.info("Creating database tables...")
                db.create_all()
                
                app.logger.info("Checking for admin user...")
                admin = User.query.filter_by(username='DevAdmin').first()
                if not admin:
                    app.logger.info("Creating admin user...")
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
                    app.logger.info("Admin user created successfully")
                
                app.logger.info("Starting Flask application...")
                app.run(
                    host=app.config.get('HOST', '0.0.0.0'),
                    port=app.config.get('PORT', 5000),
                    debug=app.config.get('DEBUG', False)
                )
                break
                
            except Exception as e:
                retry_count -= 1
                app.logger.error(f"Error during initialization (attempts left: {retry_count}): {str(e)}")
                if retry_count == 0:
                    raise
                time.sleep(5)
