from datetime import datetime, date
from flask import current_app
from app.models import Account, Budget, SavingGoal, Notification
from flask_login import current_user


def inject_globals():
    return dict(
        current_year=datetime.now().year,
        config=current_app.config,
    )


def inject_user_data():
    if not current_user.is_authenticated:
        return {}

    return dict(
        accounts=Account.query.filter_by(owner_id=current_user.id, is_active=True).all(),
        budgets=Budget.query.filter_by(owner_id=current_user.id, is_active=True).all(),
        savings_goals=SavingGoal.query.filter_by(owner_id=current_user.id, is_completed=False).all(),
        unread_notifications=Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count(),
    )


def inject_kakeibo_categories():
    if not current_user.is_authenticated:
        return {}

    return dict(
        kakeibo_categories={
            'needs': {'label': 'Besoins', 'color': '#ef4444', 'icon': 'heart'},
            'wants': {'label': 'Envies', 'color': '#f59e0b', 'icon': 'star'},
            'culture': {'label': 'Culture', 'color': '#8b5cf6', 'icon': 'book-open'},
            'unexpected': {'label': 'Imprévus', 'color': '#ec4899', 'icon': 'alert-triangle'},
        }
    )


def inject_today():
    return dict(today=date.today())