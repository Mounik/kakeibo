from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from app.models import CategoryKindEnum


class CategoryForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    kind = SelectField('Catégorie Kakeibo', choices=[
        (k.value, k.name.capitalize()) for k in CategoryKindEnum
    ], validators=[DataRequired()])
    color = StringField('Couleur', validators=[Length(max=7)], default='#6366f1')
    icon = StringField('Icône', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Enregistrer')


class CategoryFilterForm(FlaskForm):
    kind = SelectField('Type', choices=[
        ('', 'Tous')] + [(k.value, k.name.capitalize()) for k in CategoryKindEnum
    ], validators=[Optional()])
    submit = SubmitField('Filtrer')
