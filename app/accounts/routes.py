from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.accounts import bp
from app.accounts.forms import AccountForm, AccountFilterForm
from app.models import Account, Expense, Income
from app import db
from sqlalchemy import func


@bp.route('/')
@login_required
def index():
    form = AccountFilterForm(request.args)
    query = Account.query.filter_by(owner_id=current_user.id)

    if form.type.data:
        query = query.filter_by(type=form.type.data)
    if form.is_active.data:
        query = query.filter_by(is_active=form.is_active.data == '1')

    accounts = query.order_by(Account.is_main.desc(), Account.name).all()

    total_balance = sum(float(acc.balance) for acc in accounts if acc.include_in_total)

    return render_template('accounts/index.html',
        title='Comptes',
        accounts=accounts,
        total_balance=total_balance,
        form=form,
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = AccountForm()
    if form.validate_on_submit():
        if form.is_main.data:
            Account.query.filter_by(owner_id=current_user.id, is_main=True).update({'is_main': False})

        account = Account(
            name=form.name.data,
            type=form.type.data,
            currency=form.currency.data.upper(),
            initial_balance=form.initial_balance.data,
            balance=form.initial_balance.data,
            institution=form.institution.data,
            iban=form.iban.data,
            bic=form.bic.data,
            color=form.color.data,
            icon=form.icon.data,
            is_main=form.is_main.data,
            include_in_total=form.include_in_total.data,
            owner_id=current_user.id
        )
        db.session.add(account)
        db.session.commit()
        flash('Compte créé avec succès.', 'success')
        return redirect(url_for('accounts.index'))

    return render_template('accounts/form.html', form=form, title='Nouveau compte')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    account = Account.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    form = AccountForm(obj=account)

    if form.validate_on_submit():
        if form.is_main.data and not account.is_main:
            Account.query.filter_by(owner_id=current_user.id, is_main=True).update({'is_main': False})

        form.populate_obj(account)
        account.currency = account.currency.upper()
        db.session.commit()
        flash('Compte mis à jour.', 'success')
        return redirect(url_for('accounts.index'))

    return render_template('accounts/form.html', form=form, account=account, title='Modifier le compte')


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    account = Account.query.filter_by(id=id, owner_id=current_user.id).first_or_404()

    if account.is_main:
        flash('Impossible de supprimer le compte principal.', 'danger')
        return redirect(url_for('accounts.index'))

    if Expense.query.filter_by(account_id=id).count() > 0 or Income.query.filter_by(account_id=id).count() > 0:
        account.is_active = False
        flash('Compte désactivé (des transactions y sont liées).', 'info')
    else:
        db.session.delete(account)
        flash('Compte supprimé.', 'success')
    db.session.commit()
    return redirect(url_for('accounts.index'))


@bp.route('/<int:id>/refresh', methods=['POST'])
@login_required
def refresh_balance(id):
    account = Account.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    account.update_balance()
    return jsonify({'balance': float(account.balance), 'success': True})