from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import login_required
from db import db
from datetime import datetime
import csv
import io

bp = Blueprint('borrowers', __name__, url_prefix='/borrowers')

@bp.route('/')
@login_required
def view_borrowers():
    try:
        # Query existing borrowers using SQLAlchemy ORM
        borrowers = db.session.execute(
            """
            SELECT 
                b.id,
                b.full_name,
                b.date_of_birth,
                b.gender,
                b.marital_status,
                b.email,
                b.phone,
                b.position,
                b.department,
                b.employer_name,
                b.employer_address,
                b.address,
                b.city,
                b.state,
                b.bank_name,
                b.account_number,
                b.bsb_code,
                b.account_type
            FROM borrowers b
            ORDER BY b.full_name
            """
        ).fetchall()
        return render_template('borrowers/index.html', borrowers=borrowers)
    except Exception as e:
        flash(f'Error loading borrowers: {str(e)}', 'error')
        return render_template('borrowers/index.html', borrowers=[])
    
    # Loan Funding Details
    bank_name = db.Column(db.String(100))
    bank_branch = db.Column(db.String(100))
    bsb_code = db.Column(db.String(20))
    account_name = db.Column(db.String(200))
    account_number = db.Column(db.String(50))
    account_type = db.Column(db.String(20))
    
    # Relationships
    user = db.relationship('User', backref=db.backref('borrower', lazy=True))
    
    def __repr__(self):
        return f'<Borrower {self.surname}, {self.given_name}>'
    
    # Personal Details
    surname = db.Column(db.String(100), nullable=False)
    given_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    
    # Employment Details
    company_department = db.Column(db.String(200), nullable=False)
    file_number = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    postal_address = db.Column(db.String(200), nullable=False)
    work_phone = db.Column(db.String(20), nullable=False)
    date_employed = db.Column(db.Date, nullable=False)
    paymaster = db.Column(db.String(200), nullable=False)
    
    # Residential Address
    lot = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    suburb = db.Column(db.String(100), nullable=False)
    street_name = db.Column(db.String(200), nullable=False)
    marital_status = db.Column(db.String(20), nullable=False)
    spouse_name = db.Column(db.String(200))
    spouse_employer = db.Column(db.String(200))
    spouse_contact = db.Column(db.String(20))
    
    # Loan Funding Details
    bank_name = db.Column(db.String(100))
    bank_branch = db.Column(db.String(100))
    bsb_code = db.Column(db.String(20))
    account_name = db.Column(db.String(200))
    account_number = db.Column(db.String(50))
    account_type = db.Column(db.String(20))

    def __repr__(self):
        return f'<Borrower {self.surname}, {self.given_name}>'

# Route already defined above

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_borrower():
    if request.method == 'POST':
        try:
            borrower = Borrower(
                # Personal Details
                surname=request.form['surname'],
                given_name=request.form['given_name'],
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d'),
                gender=request.form['gender'],
                mobile_number=request.form['mobile_number'],
                email=request.form['email'],
                
                # Employment Details
                company_department=request.form['company_department'],
                file_number=request.form['file_number'],
                position=request.form['position'],
                postal_address=request.form['postal_address'],
                work_phone=request.form['work_phone'],
                date_employed=datetime.strptime(request.form['date_employed'], '%Y-%m-%d'),
                paymaster=request.form['paymaster'],
                
                # Residential Address
                lot=request.form['lot'],
                section=request.form['section'],
                suburb=request.form['suburb'],
                street_name=request.form['street_name'],
                marital_status=request.form['marital_status'],
                spouse_name=request.form.get('spouse_name'),
                spouse_employer=request.form.get('spouse_employer'),
                spouse_contact=request.form.get('spouse_contact'),
                
                # Loan Funding Details
                bank_name=request.form['bank_name'],
                bank_branch=request.form['bank_branch'],
                bsb_code=request.form['bsb_code'],
                account_name=request.form['account_name'],
                account_number=request.form['account_number'],
                account_type=request.form['account_type']
            )
            
            db.session.add(borrower)
            db.session.commit()
            flash('Borrower added successfully', 'success')
            return redirect(url_for('borrowers.view_borrowers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding borrower: {str(e)}', 'error')
    
    return render_template('borrowers/add.html')

@bp.route('/upload', methods=['POST'])
@login_required
def bulk_upload_borrowers():
    if 'file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('borrowers.view_borrowers'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('borrowers.view_borrowers'))
    
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('borrowers.view_borrowers'))
    
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        for row in csv_reader:
            borrower = Borrower(
                surname=row['surname'],
                given_name=row['given_name'],
                date_of_birth=datetime.strptime(row['date_of_birth'], '%Y-%m-%d'),
                gender=row['gender'],
                mobile_number=row['mobile_number'],
                email=row['email'],
                company_department=row['company_department'],
                file_number=row['file_number'],
                position=row['position'],
                postal_address=row['postal_address'],
                work_phone=row['work_phone'],
                date_employed=datetime.strptime(row['date_employed'], '%Y-%m-%d'),
                paymaster=row['paymaster'],
                lot=row['lot'],
                section=row['section'],
                suburb=row['suburb'],
                street_name=row['street_name'],
                marital_status=row['marital_status'],
                spouse_name=row.get('spouse_name'),
                spouse_employer=row.get('spouse_employer'),
                spouse_contact=row.get('spouse_contact'),
                bank_name=row['bank_name'],
                bank_branch=row['bank_branch'],
                bsb_code=row['bsb_code'],
                account_name=row['account_name'],
                account_number=row['account_number'],
                account_type=row['account_type']
            )
            db.session.add(borrower)
        
        db.session.commit()
        flash('Borrowers imported successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error importing borrowers: {str(e)}', 'error')
    
    return redirect(url_for('borrowers.view_borrowers'))
