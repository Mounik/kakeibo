from marshmallow import fields, Schema, validates_schema, ValidationError
from app.models import (
    User, Account, Income, Expense, Category, Budget, SavingGoal,
    MonthlyReview, Notification,
)


class UserSchema(Schema):
    id = fields.Int()
    username = fields.Str()
    email = fields.Email()
    first_name = fields.Str()
    last_name = fields.Str()
    is_admin = fields.Bool()
    role = fields.Str()
    currency = fields.Str()
    created_at = fields.DateTime()


class AccountSchema(Schema):
    id = fields.Int()
    name = fields.Str(required=True)
    type = fields.Str(required=True)
    currency = fields.Str()
    balance = fields.Float()
    initial_balance = fields.Float()
    institution = fields.Str()
    iban = fields.Str()
    color = fields.Str()
    is_active = fields.Bool()
    is_main = fields.Bool()


class CategorySchema(Schema):
    id = fields.Int()
    name = fields.Str(required=True)
    kind = fields.Str(required=True)
    color = fields.Str()
    icon = fields.Str()


class IncomeSchema(Schema):
    id = fields.Int()
    amount = fields.Float(required=True)
    date = fields.Date(required=True)
    source = fields.Str(required=True)
    description = fields.Str()
    recurrence = fields.Str()
    account_id = fields.Int()
    account = fields.Nested(AccountSchema, dump_only=True)


class ExpenseSchema(Schema):
    id = fields.Int()
    amount = fields.Float(required=True)
    date = fields.Date(required=True)
    merchant = fields.Str()
    description = fields.Str()
    payment_method = fields.Str()
    location = fields.Str()
    category_id = fields.Int()
    account_id = fields.Int(required=True)
    category = fields.Nested(CategorySchema, dump_only=True)
    account = fields.Nested(AccountSchema, dump_only=True)


class BudgetSchema(Schema):
    id = fields.Int()
    name = fields.Str(required=True)
    amount = fields.Float(required=True)
    period = fields.Str()
    scope = fields.Str()
    start_date = fields.Date()
    end_date = fields.Date()
    spent = fields.Float(dump_only=True)
    remaining = fields.Float(dump_only=True)
    category_id = fields.Int()
    account_id = fields.Int()


class SavingGoalSchema(Schema):
    id = fields.Int()
    name = fields.Str(required=True)
    description = fields.Str()
    target_amount = fields.Float(required=True)
    current_amount = fields.Float()
    target_date = fields.Date()
    progress = fields.Float(dump_only=True)


class MonthlyReviewSchema(Schema):
    id = fields.Int()
    year = fields.Int()
    month = fields.Int()
    q1_income = fields.Str()
    q2_savings_target = fields.Str()
    q3_planned_expenses = fields.Str()
    q4_improvement = fields.Str()
    actual_income = fields.Float()
    actual_savings = fields.Float()
    actual_expenses = fields.Float()
    notes = fields.Str()
    savings_rate = fields.Float(dump_only=True)


class NotificationSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    message = fields.Str()
    type = fields.Str()
    is_read = fields.Bool()
    created_at = fields.DateTime()


class StatisticsSchema(Schema):
    total_balance = fields.Float()
    month_income = fields.Float()
    month_expenses = fields.Float()
    month_savings = fields.Float()
    savings_rate = fields.Float()
