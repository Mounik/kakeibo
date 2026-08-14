"""Script de démonstration : crée un utilisateur et des données Kakeibo d'exemple.

Usage :
    FLASK_ENV=development python scripts/seed_demo.py
"""
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, '.')

from app import create_app, db  # noqa: E402
from app.models import User, Account, Category, Income, Expense, Budget, SavingGoal, MonthlyReview  # noqa: E402

app = create_app()


def create_demo_user():
    user = User.query.filter_by(email='demo@kakeibo.example').first()
    if user:
        return user
    user = User(
        username='demo',
        email='demo@kakeibo.example',
        locale='fr',
        currency='EUR',
    )
    user.set_password('demo1234')
    db.session.add(user)
    db.session.commit()
    print(f'Utilisateur demo créé : {user.username} / demo1234')
    return user


def create_default_categories(user):
    specs = [
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
        ('Livres', 'culture', '#8b5cf6', 'book-open'),
        ('Musique', 'culture', '#8b5cf6', 'music'),
        ('Cinéma', 'culture', '#8b5cf6', 'film'),
        ('Formations', 'culture', '#8b5cf6', 'graduation-cap'),
        ('Réparations', 'unexpected', '#ec4899', 'wrench'),
        ('Urgences', 'unexpected', '#ec4899', 'alert-triangle'),
        ('Frais médicaux', 'unexpected', '#ec4899', 'stethoscope'),
    ]
    cats = {}
    for name, kind, color, icon in specs:
        cat = Category.query.filter_by(name=name, owner_id=user.id).first()
        if cat is None:
            cat = Category(name=name, kind=kind, color=color, icon=icon, is_system=True, owner_id=user.id)
            db.session.add(cat)
        cats[name] = cat
    db.session.commit()
    return cats


def create_demo_accounts(user):
    specs = [
        ('Compte courant', 'checking', 1250.00, True),
        ('Épargne', 'savings', 5000.00, False),
        ('Espèces', 'cash', 150.00, False),
    ]
    accounts = {}
    for name, type_, balance, is_main in specs:
        acc = Account.query.filter_by(name=name, owner_id=user.id).first()
        if acc is None:
            acc = Account(
                name=name, type=type_, currency='EUR', balance=balance,
                initial_balance=balance, is_main=is_main, owner_id=user.id,
            )
            db.session.add(acc)
        accounts[name] = acc
    db.session.commit()
    return accounts


def seed_transactions(user, accounts, categories):
    today = date.today()
    if Expense.query.filter_by(owner_id=user.id).count() > 0:
        print('Transactions déjà présentes, skip.')
        return

    db.session.add(Income(
        amount=Decimal('2500.00'), date=today.replace(day=5),
        source='Salaire', description='Salaire mensuel',
        account_id=accounts['Compte courant'].id, owner_id=user.id,
    ))
    db.session.add(Income(
        amount=Decimal('300.00'), date=today.replace(day=10),
        source='Freelance', description='Mission ponctuelle',
        account_id=accounts['Compte courant'].id, owner_id=user.id,
    ))

    samples = [
        ('Loyer', 780.00, 1, 'Logement', 'Loyer appartement'),
        ('Courses', 145.32, 3, 'Alimentation', 'Courses hebdomadaires'),
        ('Boulangerie', 4.80, 3, 'Alimentation', ''),
        ('Restaurant', 32.00, 3, 'Restaurants', 'Dîner entre amis'),
        ('Cinéma', 12.50, 3, 'Cinéma', ''),
        ('Livre', 19.90, 3, 'Livres', ''),
        ('Essence', 55.00, 3, 'Transport', ''),
        ('Prime', 90.00, 3, 'Assurances', ''),
        ('Pharmacie', 23.40, 3, 'Santé', ''),
        ('Shopping', 120.00, 3, 'Shopping', ''),
    ]
    for i, (merchant, amount, account_key, category, desc) in enumerate(samples):
        day = min(1 + i * 2, 28)
        db.session.add(Expense(
            amount=Decimal(str(amount)),
            date=today.replace(day=day),
            merchant=merchant,
            description=desc,
            category_id=categories[category].id,
            account_id=accounts['Compte courant'].id if account_key == 1 else accounts['Espèces'].id,
            owner_id=user.id,
        ))
    db.session.commit()
    print('Transactions d\'exemple créées.')


def seed_budgets(user, categories):
    first = date.today().replace(day=1)
    from calendar import monthrange
    last = date.today().replace(day=monthrange(first.year, first.month)[1])
    if Budget.query.filter_by(owner_id=user.id).count() == 0:
        db.session.add(Budget(
            name='Alimentation', amount=Decimal('400.00'), period='monthly',
            scope='category', start_date=first, end_date=last,
            category_id=categories['Alimentation'].id, owner_id=user.id,
        ))
        db.session.add(Budget(
            name='Loisirs', amount=Decimal('200.00'), period='monthly',
            scope='category', start_date=first, end_date=last,
            category_id=categories['Loisirs'].id, owner_id=user.id,
        ))
        db.session.commit()
        print('Budgets d\'exemple créés.')


def seed_goals(user):
    if SavingGoal.query.filter_by(owner_id=user.id).count() == 0:
        db.session.add(SavingGoal(
            name='Vacances été', description='Fonds vacances',
            target_amount=Decimal('2000.00'), current_amount=Decimal('750.00'),
            target_date=date.today() + timedelta(days=180), owner_id=user.id,
        ))
        db.session.commit()
        print('Objectif d\'épargne créé.')


def seed_review(user):
    if MonthlyReview.query.filter_by(owner_id=user.id, year=date.today().year, month=date.today().month).count() == 0:
        db.session.add(MonthlyReview(
            year=date.today().year, month=date.today().month,
            q1_income='2500 € par mois, plus 300 € de freelance.',
            q2_savings_target='Épargner 500 €.',
            q3_planned_expenses='Environ 1600 € de dépenses.',
            q4_improvement='Limiter les restaurants à une fois par semaine.',
            owner_id=user.id,
        ))
        db.session.commit()
        print('Journal Kakeibo créé.')


def run():
    with app.app_context():
        user = create_demo_user()
        categories = create_default_categories(user)
        accounts = create_demo_accounts(user)
        seed_transactions(user, accounts, categories)
        seed_budgets(user, categories)
        seed_goals(user)
        seed_review(user)
        print('Données de démonstration prêtes. Connectez-vous avec demo@kakeibo.example / demo1234')


if __name__ == '__main__':
    run()
