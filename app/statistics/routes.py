from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app.statistics import bp
from app.models import Expense, Income, Category, Account
from app import db
from app.common.utils import get_month_range
from sqlalchemy import func, extract, case
from datetime import date
from dateutil.relativedelta import relativedelta


@bp.route('/')
@login_required
def index():
    today = date.today()
    years = list(range(today.year - 4, today.year + 1))
    return render_template('statistics/index.html', title='Statistiques', years=years, today=today)


@bp.route('/api/expenses-by-category')
@login_required
def api_expenses_by_category():
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int)
    if month:
        first_day, last_day = get_month_range(year, month)
    else:
        first_day = date(year, 1, 1)
        last_day = date(year, 12, 31)

    data = db.session.query(
        Category.name, Category.color,
        func.coalesce(func.sum(Expense.amount), 0)
    ).join(Expense, Category.id == Expense.category_id).filter(
        Expense.owner_id == current_user.id,
        Expense.date >= first_day,
        Expense.date <= last_day,
        Expense.is_confirmed == True,  # noqa: E712
    ).group_by(Category.id, Category.name, Category.color).order_by(
        func.sum(Expense.amount).desc()
    ).all()

    return jsonify([{'name': name, 'color': color, 'amount': float(amount)} for name, color, amount in data])


@bp.route('/api/kakeibo-breakdown')
@login_required
def api_kakeibo_breakdown():
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int)
    if month:
        first_day, last_day = get_month_range(year, month)
    else:
        first_day = date(year, 1, 1)
        last_day = date(year, 12, 31)

    data = db.session.query(
        Category.kind,
        func.coalesce(func.sum(Expense.amount), 0)
    ).join(Expense, Category.id == Expense.category_id).filter(
        Expense.owner_id == current_user.id,
        Expense.date >= first_day,
        Expense.date <= last_day,
        Expense.is_confirmed == True,  # noqa: E712
        Expense.category_id.isnot(None),
    ).group_by(Category.kind).all()

    labels = {
        'needs': ('Besoins', '#ef4444'),
        'wants': ('Envies', '#f59e0b'),
        'culture': ('Culture', '#8b5cf6'),
        'unexpected': ('Imprévus', '#ec4899'),
    }
    result = [{'name': labels.get(k, (k, '#64748b'))[0], 'color': labels.get(k, (k, '#64748b'))[1], 'amount': float(v)} for k, v in data]
    return jsonify(result)


@bp.route('/api/monthly-trend')
@login_required
def api_monthly_trend():
    months = request.args.get('months', type=int, default=6)
    today = date.today()
    result = []

    for i in range(months - 1, -1, -1):
        target = today - relativedelta(months=i)
        first_day, last_day = get_month_range(target.year, target.month)

        income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.owner_id == current_user.id,
            Income.date >= first_day,
            Income.date <= last_day,
            Income.is_confirmed == True,  # noqa: E712
        ).scalar() or 0

        expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.owner_id == current_user.id,
            Expense.date >= first_day,
            Expense.date <= last_day,
            Expense.is_confirmed == True,  # noqa: E712
        ).scalar() or 0

        result.append({
            'month': target.strftime('%m/%Y'),
            'month_short': target.strftime('%b %Y'),
            'income': float(income),
            'expenses': float(expenses),
            'balance': float(income) - float(expenses),
        })

    return jsonify(result)


@bp.route('/api/annual')
@login_required
def api_annual():
    year = request.args.get('year', type=int, default=date.today().year)
    result = []
    for month in range(1, 13):
        first_day, last_day = get_month_range(year, month)
        income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.owner_id == current_user.id,
            Income.date >= first_day,
            Income.date <= last_day,
            Income.is_confirmed == True,  # noqa: E712
        ).scalar() or 0
        expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.owner_id == current_user.id,
            Expense.date >= first_day,
            Expense.date <= last_day,
            Expense.is_confirmed == True,  # noqa: E712
        ).scalar() or 0
        result.append({
            'month': month,
            'label': date(year, month, 1).strftime('%b'),
            'income': float(income),
            'expenses': float(expenses),
        })
    return jsonify(result)


@bp.route('/api/savings-evolution')
@login_required
def api_savings_evolution():
    years = request.args.get('years', type=int, default=2)
    today = date.today()
    result = []
    for i in range(years - 1, -1, -1):
        target = today - relativedelta(years=i)
        first_day = date(target.year, 1, 1)
        last_day = date(target.year, 12, 31)
        income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.owner_id == current_user.id,
            Income.date >= first_day,
            Income.date <= last_day,
            Income.is_confirmed == True,  # noqa: E712
        ).scalar() or 0
        expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.owner_id == current_user.id,
            Expense.date >= first_day,
            Expense.date <= last_day,
            Expense.is_confirmed == True,  # noqa: E712
        ).scalar() or 0
        result.append({
            'year': target.year,
            'income': float(income),
            'expenses': float(expenses),
            'savings': float(income) - float(expenses),
        })
    return jsonify(result)


@bp.route('/api/savings-rate')
@login_required
def api_savings_rate():
    months = request.args.get('months', type=int, default=6)
    today = date.today()
    result = []
    for i in range(months - 1, -1, -1):
        target = today - relativedelta(months=i)
        first_day, last_day = get_month_range(target.year, target.month)
        income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.owner_id == current_user.id,
            Income.date >= first_day,
            Income.date <= last_day,
            Income.is_confirmed == True,  # noqa: E712
        ).scalar() or 0
        expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.owner_id == current_user.id,
            Expense.date >= first_day,
            Expense.date <= last_day,
            Expense.is_confirmed == True,  # noqa: E712
        ).scalar() or 0
        savings = float(income) - float(expenses)
        rate = (savings / float(income) * 100) if income > 0 else 0
        result.append({
            'month': target.strftime('%m/%Y'),
            'month_short': target.strftime('%b %Y'),
            'rate': round(max(rate, 0), 1),
        })
    return jsonify(result)
