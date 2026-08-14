from flask import current_app, render_template
from flask_mail import Message
from app import mail
from datetime import datetime, date
from decimal import Decimal
import csv
import io


def send_email(subject, recipients, template, **kwargs):
    if not current_app.config.get('MAIL_USERNAME'):
        return False
    try:
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            html=render_template(template, **kwargs),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Erreur envoi email: {e}')
        return False


def format_currency(amount, currency='EUR'):
    if amount is None:
        amount = 0
    symbols = {'EUR': '€', 'USD': '$', 'GBP': '£', 'CHF': 'CHF'}
    symbol = symbols.get(currency, currency)
    return f'{amount:,.2f} {symbol}'.replace(',', ' ')


def format_date(date_obj, format_str='%d/%m/%Y'):
    if date_obj is None:
        return ''
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime(format_str)


def format_percentage(value, decimals=1):
    if value is None:
        return '0%'
    return f'{value:.{decimals}f}%'


def get_month_range(year, month):
    from calendar import monthrange
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    return first_day, last_day


def get_current_month_range():
    today = date.today()
    return get_month_range(today.year, today.month)


def get_previous_month_range():
    today = date.today()
    if today.month == 1:
        return get_month_range(today.year - 1, 12)
    return get_month_range(today.year, today.month - 1)


def calculate_savings_rate(income, expenses):
    if income <= 0:
        return 0
    savings = income - expenses
    return max(0, (savings / income) * 100)


def export_to_csv(data, headers, filename='export.csv'):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    output.seek(0)
    return output.getvalue()


def import_from_csv(file, model_class, field_mapping, user_id):
    from app import db
    from app.models import Category, Account
    import csv
    import io

    stream = io.StringIO(file.stream.read().decode('utf-8'))
    reader = csv.DictReader(stream)

    count = 0
    for row in reader:
        try:
            obj_data = {}
            for field, csv_col in field_mapping.items():
                if csv_col in row:
                    value = row[csv_col]
                    if hasattr(model_class, field):
                        col_type = getattr(model_class.__table__.columns, field).type
                        if hasattr(col_type, 'python_type'):
                            if col_type.python_type == Decimal:
                                value = Decimal(value) if value else Decimal('0')
                            elif col_type.python_type == date:
                                from datetime import datetime
                                value = datetime.strptime(value, '%Y-%m-%d').date()
                            elif col_type.python_type == bool:
                                value = value.lower() in ('true', '1', 'yes', 'oui')
                obj_data[field] = value

            obj_data['owner_id'] = user_id
            obj = model_class(**obj_data)
            db.session.add(obj)
            count += 1
        except Exception as e:
            current_app.logger.error(f'Erreur import ligne: {e}')
            continue

    db.session.commit()
    return count


def allowed_file(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'csv', 'ofx', 'qif', 'xlsx', 'xls'})


def format_number(value, decimals=2):
    if value is None:
        value = 0
    return f'{value:,.{decimals}f}'.replace(',', ' ')