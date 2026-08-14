from datetime import datetime, date, timedelta
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import validates
from app import db, bcrypt


class CategoryKindEnum(str, Enum):
    NEEDS = 'needs'
    WANTS = 'wants'
    CULTURE = 'culture'
    UNEXPECTED = 'unexpected'


class AccountTypeEnum(str, Enum):
    CHECKING = 'checking'
    SAVINGS = 'savings'
    CASH = 'cash'
    CREDIT_CARD = 'credit_card'
    INVESTMENT = 'investment'
    PROFESSIONAL = 'professional'


class IncomeRecurrenceEnum(str, Enum):
    NONE = 'none'
    WEEKLY = 'weekly'
    BIWEEKLY = 'biweekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'


class BudgetPeriodEnum(str, Enum):
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'


class BudgetScopeEnum(str, Enum):
    GLOBAL = 'global'
    CATEGORY = 'category'
    ACCOUNT = 'account'


class TransactionTypeEnum(str, Enum):
    EXPENSE = 'expense'
    INCOME = 'income'


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')
    locale = db.Column(db.String(10), default='fr')
    currency = db.Column(db.String(3), default='EUR')
    theme = db.Column(db.String(20), default='flatly')
    timezone = db.Column(db.String(50), default='Europe/Paris')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)

    accounts = db.relationship('Account', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    incomes = db.relationship('Income', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    expenses = db.relationship('Expense', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    savings_goals = db.relationship('SavingGoal', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('Category', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    monthly_reviews = db.relationship('MonthlyReview', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    badges = db.relationship('Badge', secondary='user_badges', back_populates='users')
    challenges = db.relationship('Challenge', secondary='user_challenges', back_populates='participants')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)

    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.locked_until = None

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    kind = db.Column(db.Enum(CategoryKindEnum), nullable=False, index=True)
    icon = db.Column(db.String(50))
    color = db.Column(db.String(7), default='#6366f1')
    is_system = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship('User', back_populates='categories')
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    expenses = db.relationship('Expense', back_populates='category', lazy='dynamic')
    budgets = db.relationship('Budget', back_populates='category', lazy='dynamic')

    __table_args__ = (
        UniqueConstraint('name', 'owner_id', name='uq_category_name_owner'),
        Index('ix_category_owner_kind', 'owner_id', 'kind'),
    )

    @property
    def full_name(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def __repr__(self):
        return f'<Category {self.name} ({self.kind.value})>'


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum(AccountTypeEnum), nullable=False, index=True)
    currency = db.Column(db.String(3), default='EUR')
    balance = db.Column(db.Numeric(12, 2), default=0)
    initial_balance = db.Column(db.Numeric(12, 2), default=0)
    institution = db.Column(db.String(100))
    iban = db.Column(db.String(34))
    bic = db.Column(db.String(11))
    color = db.Column(db.String(7), default='#10b981')
    icon = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_main = db.Column(db.Boolean, default=False)
    include_in_total = db.Column(db.Boolean, default=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship('User', back_populates='accounts')
    expenses = db.relationship('Expense', back_populates='account', lazy='dynamic')
    incomes = db.relationship('Income', back_populates='account', lazy='dynamic')
    budgets = db.relationship('Budget', back_populates='account', lazy='dynamic')
    subscriptions = db.relationship('Subscription', back_populates='account', lazy='dynamic')

    __table_args__ = (
        Index('ix_account_owner_active', 'owner_id', 'is_active'),
    )

    def update_balance(self):
        from sqlalchemy import func
        income_sum = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.account_id == self.id
        ).scalar()
        expense_sum = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.account_id == self.id
        ).scalar()
        self.balance = self.initial_balance + income_sum - expense_sum
        db.session.commit()
        return self.balance

    def __repr__(self):
        return f'<Account {self.name} ({self.type.value})>'


class Income(db.Model):
    __tablename__ = 'incomes'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    source = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    recurrence = db.Column(db.Enum(IncomeRecurrenceEnum), default=IncomeRecurrenceEnum.NONE)
    recurrence_end_date = db.Column(db.Date)
    is_recurring = db.Column(db.Boolean, default=False)
    is_confirmed = db.Column(db.Boolean, default=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = db.relationship('Account', back_populates='incomes')
    owner = db.relationship('User', back_populates='incomes')

    __table_args__ = (
        Index('ix_income_owner_date', 'owner_id', 'date'),
        Index('ix_income_account_date', 'account_id', 'date'),
    )

    def __repr__(self):
        return f'<Income {self.amount} {self.currency} - {self.source}>'


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    merchant = db.Column(db.String(200))
    description = db.Column(db.Text)
    payment_method = db.Column(db.String(50))
    location = db.Column(db.String(200))
    is_recurring = db.Column(db.Boolean, default=False)
    is_confirmed = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('Category', back_populates='expenses')
    account = db.relationship('Account', back_populates='expenses')
    owner = db.relationship('User', back_populates='expenses')

    __table_args__ = (
        Index('ix_expense_owner_date', 'owner_id', 'date'),
        Index('ix_expense_category_date', 'category_id', 'date'),
        Index('ix_expense_account_date', 'account_id', 'date'),
    )

    def __repr__(self):
        return f'<Expense {self.amount} {self.currency} - {self.merchant or self.description}>'


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    spent = db.Column(db.Numeric(12, 2), default=0)
    period = db.Column(db.Enum(BudgetPeriodEnum), default=BudgetPeriodEnum.MONTHLY, index=True)
    scope = db.Column(db.Enum(BudgetScopeEnum), default=BudgetScopeEnum.GLOBAL)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    alert_threshold = db.Column(db.Numeric(3, 2), default=0.80)
    alert_sent = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('Category', back_populates='budgets')
    account = db.relationship('Account', back_populates='budgets')
    owner = db.relationship('User', back_populates='budgets')

    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_budget_amount_positive'),
        CheckConstraint('spent >= 0', name='ck_budget_spent_nonnegative'),
        CheckConstraint('alert_threshold >= 0 AND alert_threshold <= 1', name='ck_budget_alert_threshold'),
        Index('ix_budget_owner_period', 'owner_id', 'period', 'start_date'),
    )

    @property
    def remaining(self):
        return float(self.amount) - float(self.spent)

    @property
    def percentage_used(self):
        if self.amount == 0:
            return 0
        return (float(self.spent) / float(self.amount)) * 100

    @property
    def is_over_budget(self):
        return self.spent > self.amount

    @property
    def is_near_limit(self):
        return self.percentage_used >= (float(self.alert_threshold) * 100)

    def recalculate_spent(self):
        from sqlalchemy import func
        from datetime import date
        today = date.today()

        query = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.owner_id == self.owner_id,
            Expense.date >= self.start_date,
            Expense.date <= self.end_date,
            Expense.is_confirmed == True
        )

        if self.category_id:
            query = query.filter(Expense.category_id == self.category_id)
        if self.account_id:
            query = query.filter(Expense.account_id == self.account_id)

        self.spent = query.scalar() or 0
        db.session.commit()
        return self.spent

    def __repr__(self):
        return f'<Budget {self.name} - {self.percentage_used:.1f}%>'


class SavingGoal(db.Model):
    __tablename__ = 'saving_goals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    current_amount = db.Column(db.Numeric(12, 2), default=0)
    target_date = db.Column(db.Date, nullable=True)
    start_date = db.Column(db.Date, default=date.today)
    icon = db.Column(db.String(50))
    color = db.Column(db.String(7), default='#f59e0b')
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship('User', back_populates='savings_goals')

    __table_args__ = (
        CheckConstraint('target_amount > 0', name='ck_goal_target_positive'),
        CheckConstraint('current_amount >= 0', name='ck_goal_current_nonnegative'),
    )

    @property
    def progress(self):
        if self.target_amount == 0:
            return 0
        return (float(self.current_amount) / float(self.target_amount)) * 100

    @property
    def remaining(self):
        return float(self.target_amount) - float(self.current_amount)

    @property
    def days_remaining(self):
        if self.target_date:
            delta = self.target_date - date.today()
            return max(delta.days, 0)
        return None

    @property
    def daily_saving_needed(self):
        days = self.days_remaining
        if days and days > 0:
            return self.remaining / days
        return None

    def add_contribution(self, amount):
        self.current_amount += amount
        if self.current_amount >= self.target_amount and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<SavingGoal {self.name} - {self.progress:.1f}%>'


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default='EUR')
    billing_cycle = db.Column(db.Enum(IncomeRecurrenceEnum), default=IncomeRecurrenceEnum.MONTHLY)
    next_payment_date = db.Column(db.Date, nullable=False, index=True)
    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_auto_renew = db.Column(db.Boolean, default=True)
    payment_method = db.Column(db.String(50))
    merchant = db.Column(db.String(200))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = db.relationship('Account', back_populates='subscriptions')
    owner = db.relationship('User', back_populates='subscriptions')

    __table_args__ = (
        Index('ix_subscription_owner_next_payment', 'owner_id', 'next_payment_date'),
    )

    @property
    def is_due_soon(self, days=7):
        from datetime import date, timedelta
        return self.next_payment_date <= date.today() + timedelta(days=days)

    @property
    def monthly_cost(self):
        cycle_multiplier = {
            'weekly': 4.33,
            'biweekly': 2.17,
            'monthly': 1,
            'quarterly': 1/3,
            'yearly': 1/12,
        }
        return float(self.amount) * cycle_multiplier.get(self.billing_cycle.value, 1)

    def __repr__(self):
        return f'<Subscription {self.name} - {self.amount} {self.currency}>'


class MonthlyReview(db.Model):
    __tablename__ = 'monthly_reviews'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    q1_income = db.Column(db.Text)
    q2_savings_target = db.Column(db.Text)
    q3_planned_expenses = db.Column(db.Text)
    q4_improvement = db.Column(db.Text)
    actual_income = db.Column(db.Numeric(12, 2))
    actual_savings = db.Column(db.Numeric(12, 2))
    actual_expenses = db.Column(db.Numeric(12, 2))
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship('User', back_populates='monthly_reviews')

    __table_args__ = (
        UniqueConstraint('owner_id', 'year', 'month', name='uq_review_owner_year_month'),
    )

    @property
    def period_label(self):
        return f"{self.month:02d}/{self.year}"

    @property
    def savings_rate(self):
        if self.actual_income and self.actual_income > 0:
            return (float(self.actual_savings) / float(self.actual_income)) * 100
        return 0

    def __repr__(self):
        return f'<MonthlyReview {self.period_label}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')
    is_read = db.Column(db.Boolean, default=False)
    related_type = db.Column(db.String(50))
    related_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)

    user = db.relationship('User', back_populates='notifications')

    __table_args__ = (
        Index('ix_notification_user_read', 'user_id', 'is_read'),
    )

    def mark_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<Notification {self.title} ({self.type})>'


class Badge(db.Model):
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    color = db.Column(db.String(7), default='#f59e0b')
    criteria = db.Column(db.JSON)

    users = db.relationship('User', secondary='user_badges', back_populates='badges')

    def __repr__(self):
        return f'<Badge {self.name}>'


user_badges = db.Table(
    'user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badges.id'), primary_key=True),
    db.Column('earned_at', db.DateTime, default=datetime.utcnow),
)


class Challenge(db.Model):
    __tablename__ = 'challenges'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50))
    target_value = db.Column(db.Numeric(12, 2))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    reward_badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'))
    is_active = db.Column(db.Boolean, default=True)

    badge = db.relationship('Badge')
    participants = db.relationship('User', secondary='user_challenges', back_populates='challenges')

    def __repr__(self):
        return f'<Challenge {self.name}>'


user_challenges = db.Table(
    'user_challenges',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('challenge_id', db.Integer, db.ForeignKey('challenges.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow),
    db.Column('completed_at', db.DateTime),
    db.Column('progress', db.Numeric(12, 2), default=0),
)


expense_categories = db.Table(
    'expense_categories',
    db.Column('expense_id', db.Integer, db.ForeignKey('expenses.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True),
)