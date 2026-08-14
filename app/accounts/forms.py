from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import AccountTypeEnum


class AccountForm(FlaskForm):
    name = StringField('Nom du compte', validators=[DataRequired(), Length(max=100)])
    type = SelectField('Type de compte', choices=[
        (t.value, t.value.capitalize()) for t in AccountTypeEnum
    ], validators=[DataRequired()])
    currency = StringField('Devise', validators=[DataRequired(), Length(max=3)])
    initial_balance = DecimalField('Solde initial', validators=[NumberRange(min=-1000000, max=1000000)], default=0)
    institution = StringField('Établissement', validators=[Optional(), Length(max=100)])
    iban = StringField('IBAN', validators=[Optional(), Length(max=34)])
    bic = StringField('BIC', validators=[Optional(), Length(max=11)])
    color = StringField('Couleur', validators=[Length(max=7)], default='#10b981')
    icon = StringField('Icône', validators=[Optional(), Length(max=50)])
    is_main = BooleanField('Compte principal')
    include_in_total = BooleanField('Inclure dans le total', default=True)
    submit = SubmitField('Enregistrer')


class AccountFilterForm(FlaskForm):
    type = SelectField('Type', choices=[('', 'Tous')] + [(t.value, t.value.capitalize()) for t in AccountTypeEnum], validators=[Optional()])
    is_active = SelectField('Statut', choices=[('', 'Tous'), ('1', 'Actifs'), ('0', 'Inactifs')], validators=[Optional()])
    submit = SubmitField('Filtrer')