from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')


class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(), Length(min=3, max=80)
    ])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(), Length(min=8)
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(), EqualTo('password', message='Les mots de passe doivent correspondre.')
    ])
    submit = SubmitField('S\'inscrire')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé.')


class ResetPasswordRequestForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Demander la réinitialisation')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(), Length(min=8)
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(), EqualTo('password', message='Les mots de passe doivent correspondre.')
    ])
    submit = SubmitField('Réinitialiser le mot de passe')


class ProfileForm(FlaskForm):
    first_name = StringField('Prénom', validators=[Length(max=50)])
    last_name = StringField('Nom', validators=[Length(max=50)])
    email = EmailField('Email', validators=[Email()])
    locale = StringField('Langue', validators=[Length(max=10)])
    currency = StringField('Devise', validators=[Length(max=3)])
    theme = StringField('Thème', validators=[Length(max=20)])
    timezone = StringField('Fuseau horaire', validators=[Length(max=50)])
    submit = SubmitField('Enregistrer')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mot de passe actuel', validators=[DataRequired()])
    password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(), Length(min=8)
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(), EqualTo('password', message='Les mots de passe doivent correspondre.')
    ])
    submit = SubmitField('Changer le mot de passe')