from flask import render_template, redirect, url_for, flash, request, send_file, Response, current_app
from flask_login import login_required, current_user
from app.reports import bp
from app.reports.forms import ImportForm, ExportForm
from app.models import Expense, Income, Category, Account
from app import db
from datetime import date, datetime
from decimal import Decimal
import csv
import io
import os


@bp.route('/')
@login_required
def index():
    import_form = ImportForm()
    export_form = ExportForm()
    return render_template(
        'reports/index.html',
        title='Import / Export',
        import_form=import_form,
        export_form=export_form,
    )


@bp.route('/import', methods=['POST'])
@login_required
def import_file():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        if file is None:
            flash('Veuillez sélectionner un fichier.', 'danger')
            return redirect(url_for('reports.index'))

        filename = file.filename
        ext = filename.rsplit('.', 1)[1].lower()
        data_type = form.type.data

        try:
            if ext == 'csv':
                count = _import_csv(file, data_type)
            elif ext == 'ofx':
                count = _import_ofx(file, data_type)
            elif ext == 'qif':
                count = _import_qif(file, data_type)
            else:
                flash('Format non supporté.', 'danger')
                return redirect(url_for('reports.index'))

            flash(f'{count} ligne(s) importée(s) avec succès.', 'success')
        except Exception as exc:
            current_app.logger.exception('Import error')
            flash(f'Erreur lors de l\'import : {exc}', 'danger')
        return redirect(url_for('reports.index'))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field} : {error}', 'danger')
    return redirect(url_for('reports.index'))


@bp.route('/export/<fmt>')
@login_required
def export(fmt):
    data_type = request.args.get('type', 'all')
    start_date = _parse_date(request.args.get('start_date'))
    end_date = _parse_date(request.args.get('end_date'))

    rows = _collect_rows(data_type, start_date, end_date)

    if fmt == 'csv':
        return _export_csv(rows, data_type)
    if fmt == 'xlsx':
        return _export_xlsx(rows, data_type)
    if fmt == 'pdf':
        return _export_pdf(rows, data_type)
    flash('Format d\'export inconnu.', 'danger')
    return redirect(url_for('reports.index'))


def _collect_rows(data_type, start_date, end_date):
    query = Expense.query.filter_by(owner_id=current_user.id)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    expenses = query.order_by(Expense.date.desc()).all()

    if data_type == 'incomes':
        query = Income.query.filter_by(owner_id=current_user.id)
        if start_date:
            query = query.filter(Income.date >= start_date)
        if end_date:
            query = query.filter(Income.date <= end_date)
        incomes = query.order_by(Income.date.desc()).all()
        return _income_rows(incomes)

    if data_type == 'all':
        query = Income.query.filter_by(owner_id=current_user.id)
        if start_date:
            query = query.filter(Income.date >= start_date)
        if end_date:
            query = query.filter(Income.date <= end_date)
        incomes = query.order_by(Income.date.desc()).all()
        rows = _income_rows(incomes)
        rows.extend(_expense_rows(expenses, kind='Dépense'))
        return rows

    return _expense_rows(expenses, kind='Dépense')


def _expense_rows(expenses, kind='Dépense'):
    rows = []
    for exp in expenses:
        category = exp.category.name if exp.category else ''
        account = exp.account.name if exp.account else ''
        rows.append({
            'date': exp.date.strftime('%d/%m/%Y'),
            'type': kind,
            'amount': float(exp.amount),
            'category': category,
            'merchant': exp.merchant or '',
            'account': account,
            'payment_method': exp.payment_method or '',
            'description': exp.description or '',
        })
    return rows


def _income_rows(incomes):
    rows = []
    for inc in incomes:
        account = inc.account.name if inc.account else ''
        rows.append({
            'date': inc.date.strftime('%d/%m/%Y'),
            'type': 'Revenu',
            'amount': float(inc.amount),
            'category': '',
            'merchant': inc.source or '',
            'account': account,
            'payment_method': '',
            'description': inc.description or '',
        })
    return rows


def _export_csv(rows, data_type):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Date', 'Type', 'Montant', 'Catégorie', 'Commerçant/Source', 'Compte', 'Paiement', 'Description'])
    for row in rows:
        writer.writerow([
            row['date'], row['type'], f"{row['amount']:.2f}".replace('.', ','),
            row['category'], row['merchant'], row['account'],
            row['payment_method'], row['description'],
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=kakeibo_{data_type}.csv'},
    )


def _export_xlsx(rows, data_type):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = data_type.capitalize()
    ws.append(['Date', 'Type', 'Montant', 'Catégorie', 'Commerçant/Source', 'Compte', 'Paiement', 'Description'])
    for row in rows:
        ws.append([
            row['date'], row['type'], row['amount'], row['category'], row['merchant'],
            row['account'], row['payment_method'], row['description'],
        ])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return send_file(
        stream,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'kakeibo_{data_type}.xlsx',
    )


def _export_pdf(rows, data_type):
    from weasyprint import HTML
    html = render_template('reports/pdf.html', rows=rows, data_type=data_type, today=date.today())
    pdf = HTML(string=html).write_pdf()
    return Response(
        pdf,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=kakeibo_{data_type}.pdf'},
    )


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _import_csv(file, data_type):
    stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
    reader = csv.DictReader(stream, delimiter=';' if ';' in stream.getvalue()[:2000] else ',')
    count = 0
    accounts = {a.name: a.id for a in Account.query.filter_by(owner_id=current_user.id).all()}

    for row in reader:
        try:
            if data_type == 'expenses':
                obj = Expense(
                    amount=_to_decimal(row.get('Montant') or row.get('amount')),
                    date=_to_date(row.get('Date') or row.get('date')),
                    merchant=row.get('Commerçant') or row.get('merchant'),
                    description=row.get('Description') or row.get('description'),
                    owner_id=current_user.id,
                    account_id=accounts.get(row.get('Compte') or row.get('account'), None),
                )
            else:
                obj = Income(
                    amount=_to_decimal(row.get('Montant') or row.get('amount')),
                    date=_to_date(row.get('Date') or row.get('date')),
                    source=row.get('Source') or row.get('source') or row.get('Commerçant') or row.get('merchant'),
                    description=row.get('Description') or row.get('description'),
                    owner_id=current_user.id,
                    account_id=accounts.get(row.get('Compte') or row.get('account'), None),
                )
            if obj.amount is None or obj.date is None:
                continue
            if data_type == 'expenses' and obj.account_id is None:
                continue
            db.session.add(obj)
            count += 1
        except Exception:
            continue
    db.session.commit()
    return count


def _import_ofx(file, data_type):
    from ofxtools.Parser import OFXTree
    parser = OFXTree()
    parser.parse(file.stream)
    ofx = parser.convert()
    count = 0
    for stmt_trn in ofx.statements:
        for trn in stmt_trn.transactions:
            try:
                amount = float(trn.trnamt)
                date_val = trn.dtposted.date()
                name = str(trn.name or '')
                if data_type == 'expenses' and amount < 0:
                    obj = Expense(
                        amount=abs(amount), date=date_val, merchant=name,
                        description=str(trn.memo or ''), owner_id=current_user.id,
                    )
                    db.session.add(obj)
                    count += 1
                elif data_type == 'incomes' and amount > 0:
                    obj = Income(
                        amount=amount, date=date_val, source=name,
                        description=str(trn.memo or ''), owner_id=current_user.id,
                    )
                    db.session.add(obj)
                    count += 1
            except Exception:
                continue
    db.session.commit()
    return count


def _import_qif(file, data_type):
    import qif
    stream = io.StringIO(file.stream.read().decode('utf-8-sig', errors='replace'))
    try:
        items = qif.parse(stream)
    except Exception:
        items = _parse_qif_simple(stream.getvalue())
    count = 0
    for item in items:
        try:
            amount = item.amount
            date_val = item.date.date() if hasattr(item.date, 'date') else item.date
            if data_type == 'expenses' and amount < 0:
                obj = Expense(
                    amount=abs(amount), date=date_val,
                    merchant=getattr(item, 'payee', '') or '',
                    description=getattr(item, 'memo', '') or '',
                    owner_id=current_user.id,
                )
                db.session.add(obj)
                count += 1
            elif data_type == 'incomes' and amount > 0:
                obj = Income(
                    amount=amount, date=date_val,
                    source=getattr(item, 'payee', '') or '',
                    description=getattr(item, 'memo', '') or '',
                    owner_id=current_user.id,
                )
                db.session.add(obj)
                count += 1
        except Exception:
            continue
    db.session.commit()
    return count


def _parse_qif_simple(content):
    items = []
    current = {}
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith('!'):
            continue
        if line.startswith('^'):
            if current:
                items.append(_qif_item(current))
                current = {}
            continue
        if len(line) < 2:
            continue
        key, value = line[0], line[1:]
        current[key] = value
    if current:
        items.append(_qif_item(current))
    return items


def _qif_item(data):
    class Item:
        pass
    item = Item()
    item.date = datetime.strptime(data.get('D', '01/01/1970'), '%m/%d/%Y').date() if data.get('D') else date.today()
    try:
        item.amount = float(data.get('T', '0').replace(',', '.'))
    except ValueError:
        item.amount = 0.0
    item.payee = data.get('P', '')
    item.memo = data.get('M', '')
    return item


def _to_decimal(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    value = str(value).replace('€', '').strip()
    value = value.replace(' ', '').replace(',', '.')
    try:
        return Decimal(value)
    except Exception:
        return None


def _to_date(value):
    if value is None:
        return None
    value = str(value).strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d.%m.%Y'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
