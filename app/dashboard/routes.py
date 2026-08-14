from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app.dashboard import bp
from app.models import Account, Expense, Income, Budget, SavingGoal, Subscription, Category, MonthlyReview
from app import db
from sqlalchemy import func, extract
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.common.utils import get_month_range, get_previous_month_range


@bp.route('/')
@login_required
def index():
    today = date.today()
    first_day, last_day = get_month_range(today.year, today.month)
    prev_first, prev_last = get_previous_month_range()

    accounts = Account.query.filter_by(owner_id=current_user.id, is_active=True).all()
    total_balance = sum(float(acc.balance) for acc in accounts)

    current_month_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.owner_id == current_user.id,
        Income.date >= first_day,
        Income.date <= last_day,
        Income.is_confirmed == True
    ).scalar() or 0

    current_month_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.owner_id == current_user.id,
        Expense.date >= first_day,
        Expense.date <= last_day,
        Expense.is_confirmed == True
    ).scalar() or 0

    prev_month_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.owner_id == current_user.id,
        Income.date >= prev_first,
        Income.date <= prev_last,
        Income.is_confirmed == True
    ).scalar() or 0

    prev_month_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.owner_id == current_user.id,
        Expense.date >= prev_first,
        Expense.date <= prev_last,
        Expense.is_confirmed == True
    ).scalar() or 0

    savings = float(current_month_income) - float(current_month_expenses)
    savings_rate = (savings / float(current_month_income) * 100) if current_month_income > 0 else 0

    budgets = Budget.query.filter_by(owner_id=current_user.id, is_active=True).all()
    for budget in budgets:
        budget.recalculate_spent()

    savings_goals = SavingGoal.query.filter_by(
        owner_id=current_user.id, is_completed=False
    ).order_by(SavingGoal.target_date.asc().nullslast()).limit(5).all()

    upcoming_payments = Subscription.query.filter(
        Subscription.owner_id == current_user.id,
        Subscription.is_active == True,
        Subscription.next_payment_date <= date.today() + timedelta(days=7)
    ).order_by(Subscription.next_payment_date).limit(5).all()

    recent_expenses = Expense.query.filter_by(
        owner_id=current_user.id, is_confirmed=True
    ).order_by(Expense.date.desc(), Expense.created_at.desc()).limit(10).all()

    expense_by_category = db.session.query(
        Category.name, Category.color,
        func.coalesce(func.sum(Expense.amount), 0)
    ).join(Expense, Category.id == Expense.category_id).filter(
        Expense.owner_id == current_user.id,
        Expense.date >= first_day,
        Expense.date <= last_day,
        Expense.is_confirmed == True
    ).group_by(Category.id, Category.name, Category.color).order_by(
        func.sum(Expense.amount).desc()
    ).limit(8).all()

    monthly_trend = get_monthly_trend(current_user.id, 6)

    return render_template('dashboard/index.html',
        title='Tableau de bord',
        total_balance=total_balance,
        current_month_income=current_month_income,
        current_month_expenses=current_month_expenses,
        savings=savings,
        savings_rate=savings_rate,
        prev_month_income=prev_month_income,
        prev_month_expenses=prev_month_expenses,
        accounts=accounts,
        budgets=budgets,
        savings_goals=savings_goals,
        upcoming_payments=upcoming_payments,
        recent_expenses=recent_expenses,
        expense_by_category=expense_by_category,
        monthly_trend=monthly_trend,
        first_day=first_day,
        last_day=last_day,
    )


@bp.route('/api/summary')
@login_required
def api_summary():
    today = date.today()
    first_day, last_day = get_month_range(today.year, today.month)

    income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.owner_id == current_user.id,
        Income.date >= first_day,
        Income.date <= last_day,
        Income.is_confirmed == True
    ).scalar() or 0

    expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.owner_id == current_user.id,
        Expense.date >= first_day,
        Expense.date <= last_day,
        Expense.is_confirmed == True
    ).scalar() or 0

    return jsonify({
        'income': float(income),
        'expenses': float(expenses),
        'balance': float(income) - float(expenses),
    })


@bp.route('/api/expenses-by-category')
@login_required
def api_expenses_by_category():
    today = date.today()
    first_day, last_day = get_month_range(today.year, today.month)

    data = db.session.query(
        Category.name, Category.color,
        func.coalesce(func.sum(Expense.amount), 0)
    ).join(Expense, Category.id == Expense.category_id).filter(
        Expense.owner_id == current_user.id,
        Expense.date >= first_day,
        Expense.date <= last_day,
        Expense.is_confirmed == True
    ).group_by(Category.id, Category.name, Category.color).order_by(
        func.sum(Expense.amount).desc()
    ).all()

    return jsonify([{
        'name': name,
        'color': color,
        'amount': float(amount)
    } for name, color, amount in data])


@bp.route('/api/monthly-trend')
@login_required
def api_monthly_trend():
    months = int(request.args.get('months', 6))
    data = get_monthly_trend(current_user.id, months)
    return jsonify(data)


def get_monthly_trend(user_id, months=6):
    from datetime import date
    from dateutil.relativedelta import relativedelta

    today = date.today()
    data = []

    for i in range(months - 1, -1, -1):
        target_date = today - relativedelta(months=i)
        first_day, last_day = get_month_range(target_date.year, target_date.month)

        income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.owner_id == current_user.id,
            Income.date >= first_day,
            Income.date <= last_day,
            Income.is_confirmed == True
        ).scalar() or 0

        expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.owner_id == current_user.id,
            Expense.date >= first_day,
            Expense.date <= last_day,
            Expense.is_confirmed == True
        ).scalar() or 0

        data.append({
            'month': target_date.strftime('%m/%Y'),
            'month_short': target_date.strftime('%b %Y'),
            'income': float(income),
            'expenses': float(expenses),
            'balance': float(income) - float(expenses),
        })

    return data


def get_month_range(year, month):
    from calendar import monthrange
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    return first_day, last_day