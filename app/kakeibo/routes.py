from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.kakeibo import bp
from app.kakeibo.forms import MonthlyReviewForm
from app.models import MonthlyReview, Expense, Income, Budget
from app import db
from app.common.utils import get_month_range
from sqlalchemy import func
from datetime import date


@bp.route('/')
@login_required
def index():
    today = date.today()
    current_review = MonthlyReview.query.filter_by(
        owner_id=current_user.id, year=today.year, month=today.month
    ).first()

    past_reviews = MonthlyReview.query.filter_by(owner_id=current_user.id).filter(
        MonthlyReview.year < today.year,
    ).order_by(MonthlyReview.year.desc(), MonthlyReview.month.desc()).all()

    reviews_this_year = MonthlyReview.query.filter_by(
        owner_id=current_user.id, year=today.year
    ).filter(MonthlyReview.month < today.month).order_by(MonthlyReview.month.desc()).all()

    past_reviews = past_reviews + reviews_this_year

    return render_template(
        'kakeibo/index.html',
        title='Journal Kakeibo',
        current_review=current_review,
        past_reviews=past_reviews,
        today=today,
    )


@bp.route('/month', methods=['GET', 'POST'])
@login_required
def month():
    today = date.today()
    review = MonthlyReview.query.filter_by(
        owner_id=current_user.id, year=today.year, month=today.month
    ).first()
    form = MonthlyReviewForm(obj=review)

    if form.validate_on_submit():
        if review is None:
            review = MonthlyReview(
                owner_id=current_user.id,
                year=today.year,
                month=today.month,
            )
            db.session.add(review)
        form.populate_obj(review)
        db.session.commit()
        flash('Journal Kakeibo enregistré.', 'success')
        return redirect(url_for('kakeibo.index'))

    stats = _month_stats(current_user.id, today.year, today.month)

    if request.headers.get('HX-Request'):
        return render_template('kakeibo/_month_form.html', form=form, review=review, stats=stats, today=today)
    return render_template(
        'kakeibo/month.html',
        form=form,
        review=review,
        stats=stats,
        today=today,
        title='Journal du mois',
    )


@bp.route('/<int:year>/<int:month>')
@login_required
def view(year, month):
    review = MonthlyReview.query.filter_by(
        owner_id=current_user.id, year=year, month=month
    ).first_or_404()
    stats = _month_stats(current_user.id, year, month)
    return render_template(
        'kakeibo/view.html',
        review=review,
        stats=stats,
        title=f'Bilan {month:02d}/{year}',
    )


@bp.route('/generate', methods=['POST'])
@login_required
def generate():
    today = date.today()
    stats = _month_stats(current_user.id, today.year, today.month)

    review = MonthlyReview.query.filter_by(
        owner_id=current_user.id, year=today.year, month=today.month
    ).first()
    if review is None:
        review = MonthlyReview(owner_id=current_user.id, year=today.year, month=today.month)
        db.session.add(review)

    review.actual_income = stats['income']
    review.actual_expenses = stats['expenses']
    review.actual_savings = stats['income'] - stats['expenses']
    db.session.commit()

    if request.headers.get('HX-Request'):
        return render_template('kakeibo/_bilan.html', stats=stats, review=review)
    flash('Bilan mensuel généré.', 'success')
    return redirect(url_for('kakeibo.month'))


def _month_stats(user_id, year, month):
    first_day, last_day = get_month_range(year, month)

    income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.owner_id == user_id,
        Income.date >= first_day,
        Income.date <= last_day,
        Income.is_confirmed == True,  # noqa: E712
    ).scalar() or 0

    expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.owner_id == user_id,
        Expense.date >= first_day,
        Expense.date <= last_day,
        Expense.is_confirmed == True,  # noqa: E712
    ).scalar() or 0

    savings = float(income) - float(expenses)
    savings_rate = (savings / float(income) * 100) if income > 0 else 0

    budgets = Budget.query.filter_by(owner_id=user_id, is_active=True).all()
    over_budget = []
    for budget in budgets:
        budget.recalculate_spent()
        if budget.is_over_budget:
            over_budget.append({'name': budget.name, 'spent': float(budget.spent), 'amount': float(budget.amount)})

    return {
        'income': float(income),
        'expenses': float(expenses),
        'savings': savings,
        'savings_rate': savings_rate,
        'over_budget': over_budget,
    }
