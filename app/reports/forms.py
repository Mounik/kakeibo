from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SelectField, SubmitField, DateField
from wtforms.validators import Optional, DataRequired
from app.common.utils import allowed_file


class ImportForm(FlaskForm):
    type = SelectField('Type de données', choices=[
        ('expenses', 'Dépenses'),
        ('incomes', 'Revenus'),
    ], validators=[DataRequired()])
    file = FileField('Fichier (CSV / OFX / QIF)', validators=[FileAllowed(['csv', 'ofx', 'qif'], 'Formats acceptés : CSV, OFX, QIF')])
    submit = SubmitField('Importer')

    def validate_file(self, field):
        if field.data is None:
            return
        if not allowed_file(field.data.filename):
            from wtforms.validators import ValidationError
            raise ValidationError('Format de fichier non supporté.')


class ExportForm(FlaskForm):
    type = SelectField('Type de données', choices=[
        ('expenses', 'Dépenses'),
        ('incomes', 'Revenus'),
        ('all', 'Toutes les transactions'),
    ], validators=[DataRequired()])
    start_date = DateField('Date début', validators=[Optional()], format='%Y-%m-%d')
    end_date = DateField('Date fin', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Exporter')
