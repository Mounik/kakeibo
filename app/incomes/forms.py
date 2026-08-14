from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import IncomeRecurrenceEnum, Account


class IncomeForm(FlaskForm):
    amount = DecimalField('Montant', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    source = StringField('Source', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    recurrence = SelectField('Récurrence', choices=[
        (r.value, r.value.capitalize()) for r in IncomeRecurrenceEnum
    ], validators=[DataRequired()])
    recurrence_end_date = DateField('Fin de récurrence', validators=[Optional()], format='%Y-%m-%d')
    account_id = SelectField('Compte', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Enregistrer')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account_id.choices = [
            (a.id, a.name) for a in Account.query.filter_by(owner_id=None, is_active=True).all()
        ]


class IncomeFilterForm(FlaskForm):
    start_date = DateField('Date début', validators=[Optional()], format='%Y-%m-%d')
    end_date = DateField('Date fin', validators=[Optional()], format='%Y-%m-%d')
    account_id = SelectField('Compte', coerce=int, validators=[Optional()])
    min_amount = DecimalField('Montant min', validators=[Optional(), NumberRange(min=0)], places=2)
    max_amount = DecimalField('Montant max', validators=[Optional(), NumberRange(min=0)], places=2)
    recurrence = SelectField('Récurrence', choices=[('', 'Toutes')] + [(r.value, r.value.capitalize()) for r in IncomeRecurrenceEnum], validators=[Optional()])
    submit = SubmitField('Filtrer')