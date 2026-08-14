from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import BudgetPeriodEnum, BudgetScopeEnum


class BudgetForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    amount = DecimalField('Montant', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    period = SelectField('Période', choices=[
        (p.value, p.value.capitalize()) for p in BudgetPeriodEnum
    ], validators=[DataRequired()])
    scope = SelectField('Portée', choices=[
        (s.value, s.value.capitalize()) for s in BudgetScopeEnum
    ], validators=[DataRequired()])
    start_date = DateField('Date de début', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('Date de fin', validators=[DataRequired()], format='%Y-%m-%d')
    category_id = SelectField('Catégorie', coerce=int, validators=[Optional()])
    account_id = SelectField('Compte', coerce=int, validators=[Optional()])
    alert_threshold = DecimalField(
        'Seuil d\'alerte (%)', validators=[DataRequired(), NumberRange(min=0, max=100)],
        default=80, places=0,
    )
    submit = SubmitField('Enregistrer')

    def populate_choices(self, categories, accounts):
        self.category_id.choices = [(0, 'Toutes')] + [(c.id, c.name) for c in categories]
        self.account_id.choices = [(0, 'Tous')] + [(a.id, a.name) for a in accounts]


class BudgetFilterForm(FlaskForm):
    period = SelectField('Période', choices=[
        ('', 'Toutes')] + [(p.value, p.value.capitalize()) for p in BudgetPeriodEnum
    ], validators=[Optional()])
    is_active = SelectField('Statut', choices=[
        ('', 'Tous'), ('1', 'Actifs'), ('0', 'Inactifs')
    ], validators=[Optional()])
    submit = SubmitField('Filtrer')
