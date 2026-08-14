from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, SubmitField, TextAreaField, DateField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import Category, Account


class ExpenseForm(FlaskForm):
    amount = DecimalField('Montant', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    merchant = StringField('Commerçant', validators=[Optional(), Length(max=200)])
    category_id = SelectField('Catégorie', coerce=int, validators=[Optional()])
    account_id = SelectField('Compte', coerce=int, validators=[DataRequired()])
    payment_method = SelectField('Mode de paiement', choices=[
        ('', 'Sélectionner'),
        ('cash', 'Espèces'),
        ('card', 'Carte'),
        ('transfer', 'Virement'),
        ('check', 'Chèque'),
        ('mobile', 'Mobile'),
        ('other', 'Autre'),
    ], validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    location = StringField('Lieu', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Enregistrer')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Category, Account
        self.category_id.choices = [(0, 'Aucune')] + [
            (c.id, f"{c.name} ({c.kind.value.capitalize()})")
            for c in Category.query.filter_by(owner_id=None).all()
        ]  # Will be populated in route


class ExpenseFilterForm(FlaskForm):
    start_date = DateField('Date début', validators=[Optional()], format='%Y-%m-%d')
    end_date = DateField('Date fin', validators=[Optional()], format='%Y-%m-%d')
    category_id = SelectField('Catégorie', coerce=int, validators=[Optional()])
    account_id = SelectField('Compte', coerce=int, validators=[Optional()])
    min_amount = DecimalField('Montant min', validators=[Optional(), NumberRange(min=0)], places=2)
    max_amount = DecimalField('Montant max', validators=[Optional(), NumberRange(min=0)], places=2)
    merchant = StringField('Commerçant', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Filtrer')