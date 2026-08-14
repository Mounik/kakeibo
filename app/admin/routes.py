from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app.admin import bp
from app.models import User, Account, Expense, Income, Budget, Category
from app import db
from sqlalchemy import func


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return wrapped


@bp.route('/')
@admin_required
def index():
    total_users = User.query.count()
    total_accounts = Account.query.count()
    total_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar() or 0
    total_incomes = db.session.query(func.coalesce(func.sum(Income.amount), 0)).scalar() or 0
    total_budgets = Budget.query.count()
    total_categories = Category.query.count()
    return render_template(
        'admin/index.html',
        title='Administration',
        stats={
            'users': total_users,
            'accounts': total_accounts,
            'expenses': float(total_expenses),
            'incomes': float(total_incomes),
            'budgets': total_budgets,
            'categories': total_categories,
        },
    )


@bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', title='Utilisateurs', users=pagination.items, pagination=pagination)


@bp.route('/users/<int:id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier votre propre rôle.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_admin = not user.is_admin
    user.role = 'admin' if user.is_admin else 'user'
    db.session.commit()
    flash(f'Rôle de {user.username} mis à jour.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:id>/toggle-active', methods=['POST'])
@admin_required
def toggle_active(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'Compte de {user.username} {"activé" if user.is_active else "désactivé"}.', 'success')
    return redirect(url_for('admin.users'))
