def test_api_ping(client):
    response = client.get('/api/ping')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}


def test_api_requires_auth(client):
    response = client.get('/api/accounts')
    assert response.status_code == 401


def test_api_login(auth_client):
    response = auth_client.get('/api/auth/me')
    assert response.status_code == 200
    data = response.get_json()
    assert data['email'] == 'test@example.com'


def test_api_list_accounts(auth_client):
    response = auth_client.get('/api/accounts')
    assert response.status_code == 200
    accounts = response.get_json()['accounts']
    assert len(accounts) == 2


def test_api_create_account(auth_client, db):
    response = auth_client.post('/api/accounts', json={
        'name': 'Compte Pro',
        'type': 'professional',
        'currency': 'EUR',
    })
    assert response.status_code == 201
    assert response.get_json()['name'] == 'Compte Pro'


def test_api_create_expense(auth_client, db):
    response = auth_client.post('/api/expenses', json={
        'amount': 25.50,
        'date': '2026-01-15',
        'merchant': 'Boulangerie',
        'account_id': 1,
    })
    assert response.status_code == 201
    assert response.get_json()['amount'] == 25.5


def test_api_list_expenses(auth_client, db):
    auth_client.post('/api/expenses', json={
        'amount': 10.0,
        'date': '2026-01-10',
        'merchant': 'Test',
        'account_id': 1,
    })
    response = auth_client.get('/api/expenses')
    assert response.status_code == 200
    assert len(response.get_json()['expenses']) == 1


def test_api_create_income(auth_client, db):
    response = auth_client.post('/api/incomes', json={
        'amount': 2000.0,
        'date': '2026-01-05',
        'source': 'Salaire',
        'account_id': 1,
    })
    assert response.status_code == 201


def test_api_categories(auth_client):
    response = auth_client.get('/api/categories')
    assert response.status_code == 200
    assert len(response.get_json()['categories']) == 4


def test_api_budgets(auth_client, db):
    response = auth_client.post('/api/budgets', json={
        'name': 'Alimentation',
        'amount': 400.0,
        'period': 'monthly',
        'start_date': '2026-01-01',
        'end_date': '2026-01-31',
    })
    assert response.status_code == 201
    assert response.get_json()['name'] == 'Alimentation'


def test_api_goals(auth_client, db):
    response = auth_client.post('/api/goals', json={
        'name': 'Voyage',
        'target_amount': 1000.0,
        'target_date': '2026-12-31',
    })
    assert response.status_code == 201
    assert response.get_json()['progress'] == 0.0


def test_api_statistics_current(auth_client, db):
    response = auth_client.get('/api/statistics/current')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_balance' in data
    assert 'savings_rate' in data


def test_api_kakeibo(auth_client, db):
    response = auth_client.put('/api/kakeibo/2026/1', json={
        'q1_income': '3000',
        'q2_savings_target': '500',
    })
    assert response.status_code == 200
    assert response.get_json()['q2_savings_target'] == '500'

    response = auth_client.get('/api/kakeibo/2026/1')
    assert response.status_code == 200


def test_api_swagger_docs(client):
    response = client.get('/apidocs/')
    assert response.status_code in (200, 302)


def test_admin_api_restricted(auth_client):
    response = auth_client.get('/api/users')
    assert response.status_code == 200
