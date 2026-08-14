def test_create_expense_flow(auth_client, db):
    response = auth_client.post('/expenses/create', data={
        'amount': '42.00',
        'date': '2026-01-20',
        'merchant': 'SuperMarché',
        'category_id': '1',
        'account_id': '1',
        'payment_method': 'card',
        'description': 'Courses',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'SuperMarch' in response.data


def test_create_income_flow(auth_client, db):
    response = auth_client.post('/incomes/create', data={
        'amount': '1500.00',
        'date': '2026-01-25',
        'source': 'Freelance',
        'account_id': '1',
        'recurrence': 'none',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Freelance' in response.data


def test_create_account_flow(auth_client, db):
    response = auth_client.post('/accounts/create', data={
        'name': 'Livret A',
        'type': 'savings',
        'currency': 'EUR',
        'initial_balance': '0',
        'include_in_total': 'y',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Livret A' in response.data


def test_create_budget_flow(auth_client, db):
    response = auth_client.post('/budgets/create', data={
        'name': 'Budget courses',
        'amount': '300.00',
        'period': 'monthly',
        'scope': 'category',
        'start_date': '2026-01-01',
        'end_date': '2026-01-31',
        'category_id': '1',
        'alert_threshold': '80',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Budget courses' in response.data


def test_kakeibo_month_flow(auth_client, db):
    response = auth_client.post('/kakeibo/month', data={
        'q1_income': 'Jai 2000',
        'q2_savings_target': '400',
        'q3_planned_expenses': '1500',
        'q4_improvement': 'moins de restaurants',
        'notes': 'bon mois',
    }, follow_redirects=True)
    assert response.status_code == 200


def test_kakeibo_generate(auth_client, db):
    from datetime import date
    auth_client.post('/api/expenses', json={
        'amount': 100.0,
        'date': str(date.today()),
        'merchant': 'Test',
        'account_id': 1,
    })
    response = auth_client.post('/kakeibo/generate', follow_redirects=True)
    assert response.status_code == 200


def test_export_csv(auth_client, db):
    response = auth_client.get('/reports/export/csv?type=expenses')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'


def test_import_csv(auth_client, db):
    import io
    content = 'Date;Montant;Commerçant;Description\n01/02/2026;15,50;Librairie;Livre\n'
    data = {
        'type': 'expenses',
        'file': (io.BytesIO(content.encode('utf-8')), 'test.csv'),
    }
    response = auth_client.post('/reports/import', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
