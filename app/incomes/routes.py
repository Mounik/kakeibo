from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.incomes import bp
from app.incomes.forms import IncomeForm, IncomeFilterForm
from app.models import Income, Account
from app import db
from sqlalchemy import func, desc


@bp.route('/')
@login_required
def index():
    form = IncomeFilterForm(request.args)
    page = request.args.get('page', 1, type=int)

    form.account_id.choices = [(0, 'Tous')] + [
        (a.id, a.name) for a in Account.query.filter_by(owner_id=current_user.id, is_active=True).all()
    ]

    query = Income.query.filter_by(owner_id=current_user.id)

    if form.start_date.data:
        query = query.filter(Income.date >= form.start_date.data)
    if form.end_date.data:
        query = query.filter(Income.date <= form.end_date.data)
    if form.account_id.data:
        query = query.filter(Income.account_id == form.account_id.data)
    if form.min_amount.data:
        query = query.filter(Income.amount >= form.min_amount.data)
    if form.max_amount.data:
        query = query.filter(Income.amount <= form.max_amount.data)
    if form.recurrence.data:
        query = query.filter(Income.recurrence == form.recurrence.data)

    pagination = query.order_by(desc(Income.date), desc(Income.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )

    total = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.owner_id == current_user.id
    ).scalar() or 0

    return render_template('incomes/index.html',
        title='Revenus',
        incomes=pagination.items,
        pagination=pagination,
        form=form,
        total=total,
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = IncomeForm()
    form.account_id.choices = [
        (a.id, a.name) for a in Account.query.filter_by(owner_id=current_user.id, is_active=True).all()
    ]

    if form.validate_on_submit():
        income = Income(
            amount=form.amount.data,
            date=form.date.data,
            source=form.source.data,
            description=form.description.data,
            recurrence=form.recurrence.data,
            recurrence_end_date=form.recurrence_end_date.data,
            is_recurring=form.recurrence.data != 'none',
            account_id=form.account_id.data,
            owner_id=current_user.id
        )
        db.session.add(income)
        _update_account_balance(form.account_id.data, form.amount.data)
        db.session.commit()
        flash('Revenu enregistré.', 'success')
        return redirect(url_for('incomes.index'))

    return render_template('incomes/form.html', form=form, title='Nouveau revenu')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    income = Income.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    form = IncomeForm(obj=income)
    form.account_id.choices = [
        (a.id, a.name) for a in Account.query.filter_by(owner_id=current_user.id, is_active=True).all()
    ]

    if form.validate_on_submit():
        old_amount = income.amount
        old_account_id = income.account_id

        form.populate_obj(income)
        income.is_recurring = income.recurrence != 'none'

        if old_amount != income.amount or old_account_id != income.account_id:
            _update_account_balance(old_account_id, -old_amount)
            _update_account_balance(income.account_id, income.amount)

        db.session.commit()
        flash('Revenu modifié.', 'success')
        return redirect(url_for('incomes.index'))

    return render_template('incomes/form.html', form=form, income=income, title='Modifier le revenu')


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    income = Income.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    _update_account_balance(income.account_id, -income.amount)
    db.session.delete(income)
    db.session.commit()
    flash('Revenu supprimé.', 'success')
    return redirect(url_for('incomes.index'))


def _update_account_balance(account_id, amount_change):
    from app.models import Account
    account = db.session.get(Account, account_id)
    if account:
        account.balance += amount_change
        db.session.add(account)