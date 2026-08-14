from flask import jsonify, request, g
from flask_login import login_required, current_user, login_user, logout_user
from app.api import bp
from app.models import (
    User, Account, Income, Expense, Category, Budget, SavingGoal,
    MonthlyReview, Notification, db,
)
from app.api.schemas import (
    UserSchema, AccountSchema, IncomeSchema, ExpenseSchema, CategorySchema,
    BudgetSchema, SavingGoalSchema, MonthlyReviewSchema, NotificationSchema,
)
from sqlalchemy import func
from datetime import date
from marshmallow import ValidationError
from app.common.utils import get_month_range


user_schema = UserSchema()
account_schema = AccountSchema()
income_schema = IncomeSchema()
expense_schema = ExpenseSchema()
category_schema = CategorySchema()
budget_schema = BudgetSchema()
goal_schema = SavingGoalSchema()
review_schema = MonthlyReviewSchema()
notification_schema = NotificationSchema()


@bp.route('/ping')
def ping():
    """Health check endpoint.
    ---
    tags: [Système]
    responses:
      200:
        description: API opérationnelle
    """
    return jsonify({'status': 'ok'})


# ─── Authentification ────────────────────────────────────────────────────────


@bp.route('/auth/login', methods=['POST'])
def auth_login():
    """Connexion d'un utilisateur.
    ---
    tags: [Authentification]
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required: [email, password]
          properties:
            email: {type: string}
            password: {type: string}
    responses:
      200:
        description: Connecté
      401:
        description: Identifiants invalides
    """
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(email=data.get('email', '')).first()
    if user is None or not user.check_password(data.get('password', '')):
        return jsonify({'error': 'Identifiants invalides.'}), 401
    if user.is_locked():
        return jsonify({'error': 'Compte temporairement verrouillé.'}), 403
    user.reset_failed_login()
    db.session.commit()
    login_user(user)
    return jsonify(user_schema.dump(user)), 200


@bp.route('/auth/logout', methods=['POST'])
@login_required
def auth_logout():
    """Déconnexion.
    ---
    tags: [Authentification]
    responses:
      200:
        description: Déconnecté
    """
    logout_user()
    return jsonify({'message': 'Déconnecté.'})


@bp.route('/auth/me')
@login_required
def auth_me():
    """Profil de l'utilisateur connecté.
    ---
    tags: [Authentification]
    responses:
      200:
        description: Profil utilisateur
    """
    return jsonify(user_schema.dump(current_user))


# ─── Utilisateurs ────────────────────────────────────────────────────────────


@bp.route('/users')
@login_required
def list_users():
    """Liste des utilisateurs (réservé aux administrateurs).
    ---
    tags: [Utilisateurs]
    responses:
      200:
        description: Liste des utilisateurs
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Accès réservé aux administrateurs.'}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({'users': user_schema.dump(users, many=True)})


@bp.route('/users/<int:user_id>')
@login_required
def get_user(user_id):
    """Détail d'un utilisateur.
    ---
    tags: [Utilisateurs]
    responses:
      200:
        description: Utilisateur
    """
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'error': 'Accès refusé.'}), 403
    user = User.query.get_or_404(user_id)
    return jsonify(user_schema.dump(user))


# ─── Comptes ─────────────────────────────────────────────────────────────────


@bp.route('/accounts', methods=['GET'])
@login_required
def list_accounts():
    """Liste des comptes de l'utilisateur.
    ---
    tags: [Comptes]
    responses:
      200:
        description: Liste des comptes
    """
    accounts = Account.query.filter_by(owner_id=current_user.id).all()
    return jsonify({'accounts': account_schema.dump(accounts, many=True)})


@bp.route('/accounts', methods=['POST'])
@login_required
def create_account():
    """Création d'un compte.
    ---
    tags: [Comptes]
    responses:
      201:
        description: Compte créé
    """
    data = request.get_json(silent=True) or {}
    errors = account_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    if data.get('is_main'):
        Account.query.filter_by(owner_id=current_user.id, is_main=True).update({'is_main': False})
    account = Account(
        name=data['name'],
        type=data['type'],
        currency=data.get('currency', 'EUR'),
        initial_balance=data.get('initial_balance', 0),
        balance=data.get('initial_balance', 0),
        institution=data.get('institution'),
        iban=data.get('iban'),
        color=data.get('color', '#10b981'),
        owner_id=current_user.id,
    )
    db.session.add(account)
    db.session.commit()
    return jsonify(account_schema.dump(account)), 201


@bp.route('/accounts/<int:account_id>', methods=['GET'])
@login_required
def get_account(account_id):
    """Détail d'un compte.
    ---
    tags: [Comptes]
    responses:
      200:
        description: Compte
    """
    account = Account.query.filter_by(id=account_id, owner_id=current_user.id).first_or_404()
    return jsonify(account_schema.dump(account))


@bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    """Suppression d'un compte.
    ---
    tags: [Comptes]
    responses:
      200:
        description: Compte supprimé
    """
    account = Account.query.filter_by(id=account_id, owner_id=current_user.id).first_or_404()
    db.session.delete(account)
    db.session.commit()
    return jsonify({'message': 'Compte supprimé.'})


# ─── Revenus ─────────────────────────────────────────────────────────────────


@bp.route('/incomes', methods=['GET'])
@login_required
def list_incomes():
    """Liste des revenus.
    ---
    tags: [Revenus]
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
    responses:
      200:
        description: Liste des revenus
    """
    limit = request.args.get('limit', type=int)
    query = Income.query.filter_by(owner_id=current_user.id).order_by(Income.date.desc())
    if limit:
        query = query.limit(limit)
    return jsonify({'incomes': income_schema.dump(query.all(), many=True)})


@bp.route('/incomes', methods=['POST'])
@login_required
def create_income():
    """Création d'un revenu.
    ---
    tags: [Revenus]
    responses:
      201:
        description: Revenu créé
    """
    data = request.get_json(silent=True) or {}
    try:
        data = income_schema.load(data)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    income = Income(
        amount=data['amount'],
        date=data['date'],
        source=data['source'],
        description=data.get('description'),
        recurrence=data.get('recurrence', 'none'),
        account_id=data.get('account_id'),
        owner_id=current_user.id,
    )
    db.session.add(income)
    _adjust_balance(data.get('account_id'), data['amount'])
    db.session.commit()
    return jsonify(income_schema.dump(income)), 201


@bp.route('/incomes/<int:income_id>', methods=['DELETE'])
@login_required
def delete_income(income_id):
    """Suppression d'un revenu.
    ---
    tags: [Revenus]
    responses:
      200:
        description: Revenu supprimé
    """
    income = Income.query.filter_by(id=income_id, owner_id=current_user.id).first_or_404()
    _adjust_balance(income.account_id, -float(income.amount))
    db.session.delete(income)
    db.session.commit()
    return jsonify({'message': 'Revenu supprimé.'})


# ─── Dépenses ────────────────────────────────────────────────────────────────


@bp.route('/expenses', methods=['GET'])
@login_required
def list_expenses():
    """Liste des dépenses.
    ---
    tags: [Dépenses]
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
    responses:
      200:
        description: Liste des dépenses
    """
    limit = request.args.get('limit', type=int)
    query = Expense.query.filter_by(owner_id=current_user.id).order_by(Expense.date.desc())
    if limit:
        query = query.limit(limit)
    return jsonify({'expenses': expense_schema.dump(query.all(), many=True)})


@bp.route('/expenses', methods=['POST'])
@login_required
def create_expense():
    """Création d'une dépense.
    ---
    tags: [Dépenses]
    responses:
      201:
        description: Dépense créée
    """
    data = request.get_json(silent=True) or {}
    try:
        data = expense_schema.load(data)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    expense = Expense(
        amount=data['amount'],
        date=data['date'],
        merchant=data.get('merchant'),
        description=data.get('description'),
        payment_method=data.get('payment_method'),
        location=data.get('location'),
        category_id=data.get('category_id'),
        account_id=data['account_id'],
        owner_id=current_user.id,
    )
    db.session.add(expense)
    _adjust_balance(data['account_id'], -float(data['amount']))
    db.session.commit()
    return jsonify(expense_schema.dump(expense)), 201


@bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    """Suppression d'une dépense.
    ---
    tags: [Dépenses]
    responses:
      200:
        description: Dépense supprimée
    """
    expense = Expense.query.filter_by(id=expense_id, owner_id=current_user.id).first_or_404()
    _adjust_balance(expense.account_id, float(expense.amount))
    db.session.delete(expense)
    db.session.commit()
    return jsonify({'message': 'Dépense supprimée.'})


# ─── Catégories ──────────────────────────────────────────────────────────────


@bp.route('/categories', methods=['GET'])
@login_required
def list_categories():
    """Liste des catégories.
    ---
    tags: [Catégories]
    responses:
      200:
        description: Liste des catégories
    """
    categories = Category.query.filter_by(owner_id=current_user.id).order_by(Category.kind, Category.name).all()
    return jsonify({'categories': category_schema.dump(categories, many=True)})


@bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    """Création d'une catégorie.
    ---
    tags: [Catégories]
    responses:
      201:
        description: Catégorie créée
    """
    data = request.get_json(silent=True) or {}
    errors = category_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    category = Category(
        name=data['name'],
        kind=data['kind'],
        color=data.get('color', '#6366f1'),
        icon=data.get('icon'),
        owner_id=current_user.id,
    )
    db.session.add(category)
    db.session.commit()
    return jsonify(category_schema.dump(category)), 201


# ─── Budgets ─────────────────────────────────────────────────────────────────


@bp.route('/budgets', methods=['GET'])
@login_required
def list_budgets():
    """Liste des budgets.
    ---
    tags: [Budgets]
    responses:
      200:
        description: Liste des budgets
    """
    budgets = Budget.query.filter_by(owner_id=current_user.id).all()
    return jsonify({'budgets': budget_schema.dump(budgets, many=True)})


@bp.route('/budgets', methods=['POST'])
@login_required
def create_budget():
    """Création d'un budget.
    ---
    tags: [Budgets]
    responses:
      201:
        description: Budget créé
    """
    data = request.get_json(silent=True) or {}
    try:
        data = budget_schema.load(data)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    budget = Budget(
        name=data['name'],
        amount=data['amount'],
        period=data.get('period', 'monthly'),
        scope=data.get('scope', 'global'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        category_id=data.get('category_id'),
        account_id=data.get('account_id'),
        alert_threshold=data.get('alert_threshold', 0.8),
        owner_id=current_user.id,
    )
    db.session.add(budget)
    db.session.commit()
    return jsonify(budget_schema.dump(budget)), 201


# ─── Objectifs d'épargne ─────────────────────────────────────────────────────


@bp.route('/goals', methods=['GET'])
@login_required
def list_goals():
    """Liste des objectifs d'épargne.
    ---
    tags: [Objectifs]
    responses:
      200:
        description: Liste des objectifs
    """
    goals = SavingGoal.query.filter_by(owner_id=current_user.id).all()
    return jsonify({'goals': goal_schema.dump(goals, many=True)})


@bp.route('/goals', methods=['POST'])
@login_required
def create_goal():
    """Création d'un objectif d'épargne.
    ---
    tags: [Objectifs]
    responses:
      201:
        description: Objectif créé
    """
    data = request.get_json(silent=True) or {}
    try:
        data = goal_schema.load(data)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    goal = SavingGoal(
        name=data['name'],
        description=data.get('description'),
        target_amount=data['target_amount'],
        current_amount=data.get('current_amount', 0),
        target_date=data.get('target_date'),
        owner_id=current_user.id,
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify(goal_schema.dump(goal)), 201


@bp.route('/goals/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    """Suppression d'un objectif d'épargne.
    ---
    tags: [Objectifs]
    responses:
      200:
        description: Objectif supprimé
    """
    goal = SavingGoal.query.filter_by(id=goal_id, owner_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'message': 'Objectif supprimé.'})


# ─── Journal Kakeibo ─────────────────────────────────────────────────────────


@bp.route('/kakeibo')
@login_required
def list_reviews():
    """Liste des bilans Kakeibo.
    ---
    tags: [Kakeibo]
    responses:
      200:
        description: Liste des bilans
    """
    reviews = MonthlyReview.query.filter_by(owner_id=current_user.id).order_by(
        MonthlyReview.year.desc(), MonthlyReview.month.desc()
    ).all()
    return jsonify({'reviews': review_schema.dump(reviews, many=True)})


@bp.route('/kakeibo/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_review(year, month):
    """Détail d'un bilan Kakeibo.
    ---
    tags: [Kakeibo]
    responses:
      200:
        description: Bilan mensuel
    """
    review = MonthlyReview.query.filter_by(owner_id=current_user.id, year=year, month=month).first_or_404()
    return jsonify(review_schema.dump(review))


@bp.route('/kakeibo/<int:year>/<int:month>', methods=['PUT'])
@login_required
def upsert_review(year, month):
    """Création ou mise à jour d'un bilan Kakeibo.
    ---
    tags: [Kakeibo]
    responses:
      200:
        description: Bilan enregistré
    """
    data = request.get_json(silent=True) or {}
    review = MonthlyReview.query.filter_by(owner_id=current_user.id, year=year, month=month).first()
    if review is None:
        review = MonthlyReview(owner_id=current_user.id, year=year, month=month)
        db.session.add(review)
    review.q1_income = data.get('q1_income', review.q1_income)
    review.q2_savings_target = data.get('q2_savings_target', review.q2_savings_target)
    review.q3_planned_expenses = data.get('q3_planned_expenses', review.q3_planned_expenses)
    review.q4_improvement = data.get('q4_improvement', review.q4_improvement)
    review.notes = data.get('notes', review.notes)
    db.session.commit()
    return jsonify(review_schema.dump(review))


# ─── Statistiques ────────────────────────────────────────────────────────────


@bp.route('/statistics/current')
@login_required
def statistics_current():
    """Statistiques du mois en cours.
    ---
    tags: [Statistiques]
    responses:
      200:
        description: Statistiques mensuelles
    """
    today = date.today()
    first_day, last_day = get_month_range(today.year, today.month)
    balance = db.session.query(func.coalesce(func.sum(Account.balance), 0)).filter(
        Account.owner_id == current_user.id, Account.is_active == True,  # noqa: E712
    ).scalar() or 0
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
    return jsonify({
        'total_balance': float(balance),
        'month_income': float(income),
        'month_expenses': float(expenses),
        'month_savings': savings,
        'savings_rate': max(rate, 0),
    })


@bp.route('/statistics/expenses-by-category')
@login_required
def statistics_expenses_by_category():
    """Dépenses du mois par catégorie.
    ---
    tags: [Statistiques]
    responses:
      200:
        description: Répartition par catégorie
    """
    today = date.today()
    first_day, last_day = get_month_range(today.year, today.month)
    rows = db.session.query(
        Category.name, Category.color, func.coalesce(func.sum(Expense.amount), 0)
    ).join(Expense, Category.id == Expense.category_id).filter(
        Expense.owner_id == current_user.id,
        Expense.date >= first_day,
        Expense.date <= last_day,
        Expense.is_confirmed == True,  # noqa: E712
    ).group_by(Category.id, Category.name, Category.color).order_by(func.sum(Expense.amount).desc()).all()
    return jsonify([{'name': n, 'color': c, 'amount': float(a)} for n, c, a in rows])


# ─── Notifications ───────────────────────────────────────────────────────────


@bp.route('/notifications')
@login_required
def list_notifications():
    """Liste des notifications.
    ---
    tags: [Notifications]
    responses:
      200:
        description: Liste des notifications
    """
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).limit(50).all()
    return jsonify({'notifications': notification_schema.dump(notifications, many=True)})


@bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def read_notification(notification_id):
    """Marque une notification comme lue.
    ---
    tags: [Notifications]
    responses:
      200:
        description: Notification lue
    """
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.mark_read()
    return jsonify(notification_schema.dump(notification))


def _adjust_balance(account_id, amount):
    if not account_id:
        return
    account = db.session.get(Account, account_id)
    if account:
        account.balance = float(account.balance or 0) + float(amount)
