from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash
from app.auth import bp
from app.auth.forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm
from app.models import User, Category, Account, db
from app.common.utils import send_email
from datetime import datetime, timedelta


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Email ou mot de passe invalide.', 'danger')
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                user.increment_failed_login()
                db.session.commit()
            return redirect(url_for('auth.login'))

        if user.is_locked():
            flash('Compte temporairement verrouillé. Réessayez plus tard.', 'danger')
            return redirect(url_for('auth.login'))

        user.reset_failed_login()
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard.index')
        return redirect(next_page)

    return render_template('auth/login.html', form=form, title='Connexion')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            locale='fr',
            currency='EUR'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        create_default_categories(user)
        create_default_accounts(user)

        flash('Inscription réussie ! Bienvenue sur Kakeibo Budget.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='Inscription')


def create_default_categories(user):
    categories = [
        ('Logement', 'needs', '#ef4444', 'home'),
        ('Alimentation', 'needs', '#ef4444', 'utensils'),
        ('Santé', 'needs', '#ef4444', 'heart-pulse'),
        ('Énergie', 'needs', '#ef4444', 'bolt'),
        ('Transport', 'needs', '#ef4444', 'car'),
        ('Assurances', 'needs', '#ef4444', 'shield'),
        ('Restaurants', 'wants', '#f59e0b', 'utensils-crossed'),
        ('Shopping', 'wants', '#f59e0b', 'shopping-bag'),
        ('Vêtements', 'wants', '#f59e0b', 'shirt'),
        ('Loisirs', 'wants', '#f59e0b', 'gamepad-2'),
        ('Voyages', 'wants', '#f59e0b', 'plane'),
        ('Livres', 'culture', '#8b5cf6', 'book-open'),
        ('Musique', 'culture', '#8b5cf6', 'music'),
        ('Cinéma', 'culture', '#8b5cf6', 'film'),
        ('Formations', 'culture', '#8b5cf6', 'graduation-cap'),
        ('Réparations', 'unexpected', '#ec4899', 'wrench'),
        ('Urgences', 'unexpected', '#ec4899', 'alert-triangle'),
        ('Frais médicaux', 'unexpected', '#ec4899', 'stethoscope'),
    ]
    for name, kind, color, icon in categories:
        cat = Category(name=name, kind=kind, color=color, icon=icon, is_system=True, owner_id=user.id)
        db.session.add(cat)
    db.session.commit()


def create_default_accounts(user):
    accounts = [
        ('Compte courant', 'checking', 'EUR', 0, True, '#10b981', 'banknote'),
        ('Espèces', 'cash', 'EUR', 0, False, '#f59e0b', 'wallet'),
        ('Épargne', 'savings', 'EUR', 0, False, '#3b82f6', 'piggy-bank'),
    ]
    for name, type_, currency, balance, is_main, color, icon in accounts:
        acc = Account(
            name=name, type=type_, currency=currency,
            balance=balance, initial_balance=balance,
            is_main=is_main, color=color, icon=icon,
            owner_id=user.id
        )
        db.session.add(acc)
    db.session.commit()


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        db.session.commit()
        flash('Profil mis à jour.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html', form=form, title='Profil')


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Mot de passe actuel incorrect.', 'danger')
        else:
            current_user.set_password(form.password.data)
            db.session.commit()
            flash('Mot de passe modifié avec succès.', 'success')
            return redirect(url_for('auth.profile'))
    return render_template('auth/change_password.html', form=form, title='Changer le mot de passe')