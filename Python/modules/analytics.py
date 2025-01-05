from flask import Blueprint, render_template, current_app
from flask_login import login_required
from sqlalchemy import func, text
from datetime import datetime
from dateutil.relativedelta import relativedelta
from models import db, Loan, Borrower, RepaymentRecord, Document

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/')
@login_required
def index():
    try:
        # Loan statistics
        total_loans = Loan.query.count()
        active_loans = Loan.query.filter(Loan.status.ilike('%approved%')).count()
        total_amount = db.session.query(func.sum(Loan.amount)).filter(Loan.status.ilike('%approved%')).scalar() or 0
        avg_amount = total_amount / active_loans if active_loans > 0 else 0
        
        # Monthly loan trends (last 6 months)
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
            
        # Repayment statistics
        total_repayments = RepaymentRecord.query.count()
        ontime_payments = RepaymentRecord.query.filter_by(is_late_payment=False).count()
        late_payments = RepaymentRecord.query.filter_by(is_late_payment=True).count()
            
        stats = {
            'active_loans': active_loans,
            'avg_loan_amount': float(avg_amount),
            'total_portfolio': float(total_amount),
            'total_repayments': total_repayments,
            'ontime_payment_rate': (ontime_payments / total_repayments * 100) if total_repayments > 0 else 0,
            'late_payment_rate': (late_payments / total_repayments * 100) if total_repayments > 0 else 0
        }
        
        return render_template(
            'analytics/index.html',
            stats=stats,
            monthly_labels=months,
            monthly_amounts=amounts,
            loan_types=loan_types,
            loan_type_distribution=loan_type_distribution
        )
        
    except Exception as e:
        print(f"Analytics error: {str(e)}")
        return render_template(
            'analytics/index.html',
            stats={
                'active_loans': 0,
                'avg_loan_amount': 0,
                'total_portfolio': 0,
                'total_repayments': 0,
                'ontime_payment_rate': 0,
                'late_payment_rate': 0
            },
            monthly_labels=[],
            monthly_amounts=[],
            loan_types=[],
            loan_type_distribution=[]
        )

@bp.route('/loan-performance')
@login_required
def loan_performance():
    try:
        # Get loan performance metrics
        performance_stats = db.session.query(
            func.count(Loan.id).label('total_loans'),
            func.sum(case(
                [(Loan.status == 'defaulted', 1)],
                else_=0
            )).label('defaulted_loans'),
            func.avg(Loan.amount).label('avg_loan_amount')
        ).select_from(Loan).first()
        
        return render_template(
            'analytics/loan_performance.html',
            performance_stats={
                'total_loans': performance_stats.total_loans or 0,
                'defaulted_loans': performance_stats.defaulted_loans or 0,
                'default_rate': (performance_stats.defaulted_loans / performance_stats.total_loans * 100) if performance_stats.total_loans > 0 else 0,
                'avg_loan_amount': float(performance_stats.avg_loan_amount or 0)
            }
        )
    except Exception as e:
        print(f"Loan performance analytics error: {str(e)}")
        return render_template(
            'analytics/loan_performance.html',
            performance_stats={
                'total_loans': 0,
                'defaulted_loans': 0,
                'default_rate': 0,
                'avg_loan_amount': 0
            }
        )
