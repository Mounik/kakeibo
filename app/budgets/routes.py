from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.budgets import bp
from app.budgets.forms import BudgetForm, BudgetFilterForm
from app.models import Budget, Category, Account, Notification
from app import db
from sqlalchemy import func, desc
from datetime import date
from decimal import Decimal


@bp.route('/')
@login_required
def index():
    form = BudgetFilterForm(request.args)
    query = Budget.query.filter_by(owner_id=current_user.id)

    if form.period.data:
        query = query.filter_by(period=form.period.data)
    if form.is_active.data:
        query = query.filter_by(is_active=form.is_active.data == '1')

    budgets = query.order_by(Budget.is_active.desc(), Budget.start_date.desc()).all()
    for budget in budgets:
        budget.recalculate_spent()

    total_budgeted = sum(float(b.amount) for b in budgets if b.is_active)
    total_spent = sum(float(b.spent) for b in budgets if b.is_active)

    return render_template(
        'budgets/index.html',
        title='Budgets',
        budgets=budgets,
        form=form,
        total_budgeted=total_budgeted,
        total_spent=total_spent,
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = BudgetForm()
    _populate_choices(form)

    if form.validate_on_submit():
        budget = Budget(
            name=form.name.data,
            amount=form.amount.data,
            period=form.period.data,
            scope=form.scope.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            category_id=form.category_id.data if form.category_id.data else None,
            account_id=form.account_id.data if form.account_id.data else None,
            alert_threshold=Decimal(form.alert_threshold.data) / 100,
            owner_id=current_user.id,
        )
        db.session.add(budget)
        db.session.commit()
        flash('Budget créé avec succès.', 'success')
        return redirect(url_for('budgets.index'))

    return render_template('budgets/form.html', form=form, title='Nouveau budget')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    budget = Budget.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    form = BudgetForm(obj=budget)
    form.alert_threshold.data = float(budget.alert_threshold) * 100
    _populate_choices(form)

    if form.validate_on_submit():
        form.populate_obj(budget)
        budget.category_id = form.category_id.data if form.category_id.data else None
        budget.account_id = form.account_id.data if form.account_id.data else None
        budget.alert_threshold = Decimal(form.alert_threshold.data) / 100
        db.session.commit()
        flash('Budget mis à jour.', 'success')
        return redirect(url_for('budgets.index'))

    return render_template('budgets/form.html', form=form, budget=budget, title='Modifier le budget')


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    budget = Budget.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    flash('Budget supprimé.', 'success')
    return redirect(url_for('budgets.index'))


@bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle(id):
    budget = Budget.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    budget.is_active = not budget.is_active
    db.session.commit()
    if request.headers.get('HX-Request'):
        return _budget_card(budget)
    return redirect(url_for('budgets.index'))


def _budget_card(budget):
    return render_template('budgets/_card.html', budget=budget)


def _populate_choices(form):
    categories = Category.query.filter_by(owner_id=current_user.id).order_by(Category.kind, Category.name).all()
    accounts = Account.query.filter_by(owner_id=current_user.id, is_active=True).all()
    form.populate_choices(categories, accounts)
