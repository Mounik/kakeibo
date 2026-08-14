from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Optional, Length


class MonthlyReviewForm(FlaskForm):
    q1_income = TextAreaField(
        'Combien ai-je ?',
        description='Faites le point sur votre argent disponible.',
        validators=[Optional(), Length(max=1000)],
    )
    q2_savings_target = TextAreaField(
        'Combien voudrais-je économiser ?',
        description='Fixez votre objectif d\'épargne du mois.',
        validators=[Optional(), Length(max=1000)],
    )
    q3_planned_expenses = TextAreaField(
        'Combien vais-je dépenser ?',
        description='Prévoyez vos dépenses pour le mois à venir.',
        validators=[Optional(), Length(max=1000)],
    )
    q4_improvement = TextAreaField(
        'Comment puis-je améliorer mes finances ?',
        description='Réfléchissez à vos habitudes de consommation.',
        validators=[Optional(), Length(max=1000)],
    )
    notes = TextAreaField('Notes personnelles', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Enregistrer le journal')
