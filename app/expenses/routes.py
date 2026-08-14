from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.expenses import bp
from app.expenses.forms import ExpenseForm, ExpenseFilterForm
from app.models import Expense, Category, Account
from app import db
from sqlalchemy import func, desc
from datetime import date, timedelta
from decimal import Decimal


@bp.route('/')
@login_required
def index():
    form = ExpenseFilterForm(request.args)
    page = request.args.get('page', 1, type=int)

    # Populate choices
    form.category_id.choices = [(0, 'Toutes')] + [
        (c.id, c.name) for c in Category.query.filter_by(owner_id=current_user.id).all()
    ]
    form.account_id.choices = [(0, 'Tous')] + [
        (a.id, a.name) for a in Account.query.filter_by(owner_id=current_user.id, is_active=True).all()
    ]

    query = Expense.query.filter_by(owner_id=current_user.id)

    if form.start_date.data:
        query = query.filter(Expense.date >= form.start_date.data)
    if form.end_date.data:
        query = query.filter(Expense.date <= form.end_date.data)
    if form.category_id.data:
        query = query.filter(Expense.category_id == form.category_id.data)
    if form.account_id.data:
        query = query.filter(Expense.account_id == form.account_id.data)
    if form.min_amount.data:
        query = query.filter(Expense.amount >= form.min_amount.data)
    if form.max_amount.data:
        query = query.filter(Expense.amount <= form.max_amount.data)
    if form.merchant.data:
        query = query.filter(Expense.merchant.ilike(f'%{form.merchant.data}%'))

    pagination = query.order_by(desc(Expense.date), desc(Expense.created_at)).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    total = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.owner_id == current_user.id
    ).scalar() or 0

    return render_template('expenses/index.html',
        title='Dépenses',
        expenses=pagination.items,
        pagination=pagination,
        form=form,
        total=total,
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ExpenseForm()
    _populate_form_choices(form)

    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            date=form.date.data,
            merchant=form.merchant.data,
            category_id=form.category_id.data if form.category_id.data != 0 else None,
            account_id=form.account_id.data,
            payment_method=form.payment_method.data,
            description=form.description.data,
            location=form.location.data,
            owner_id=current_user.id
        )
        db.session.add(expense)
        _update_account_balance(form.account_id.data, -form.amount.data)
        db.session.commit()

        if request.headers.get('HX-Request'):
            return jsonify({'success': True, 'message': 'Dépense enregistrée.'})
        flash('Dépense enregistrée.', 'success')
        return redirect(url_for('expenses.index'))

    return render_template('expenses/form.html', form=form, title='Nouvelle dépense')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    expense = Expense.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    form = ExpenseForm(obj=expense)
    _populate_form_choices(form)

    if form.validate_on_submit():
        old_amount = expense.amount
        old_account_id = expense.account_id

        form.populate_obj(expense)
        expense.category_id = expense.category_id if expense.category_id != 0 else None

        # Update account balance if amount or account changed
        if old_amount != expense.amount or old_account_id != expense.account_id:
            _update_account_balance(old_account_id, old_amount)
            _update_account_balance(expense.account_id, -expense.amount)

        db.session.commit()
        flash('Dépense modifiée.', 'success')
        return redirect(url_for('expenses.index'))

    return render_template('expenses/form.html', form=form, expense=expense, title='Modifier la dépense')


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    expense = Expense.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    _update_account_balance(expense.account_id, expense.amount)
    db.session.delete(expense)
    db.session.commit()
    flash('Dépense supprimée.', 'success')
    return redirect(url_for('expenses.index'))


@bp.route('/api/categories/<kind>')
@login_required
def api_categories(kind):
    categories = Category.query.filter_by(owner_id=current_user.id, kind=kind).all()
    return jsonify([{'id': c.id, 'name': c.name, 'color': c.color, 'icon': c.icon} for c in categories])


def _populate_form_choices(form):
    form.category_id.choices = [(0, 'Aucune')] + [
        (c.id, f"{c.name} ({c.kind.value.capitalize()})")
        for c in Category.query.filter_by(owner_id=current_user.id).order_by(Category.kind, Category.name).all()
    ]
    form.account_id.choices = [
        (a.id, a.name) for a in Account.query.filter_by(owner_id=current_user.id, is_active=True).all()
    ]


def _update_account_balance(account_id, amount_change):
    from app.models import Account
    account = db.session.get(Account, account_id)
    if account:
        account.balance += amount_change
        db.session.add(account)