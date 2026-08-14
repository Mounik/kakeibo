def test_dashboard_index(auth_client):
    response = auth_client.get('/')
    assert response.status_code == 200
    assert b'Tableau de bord' in response.data


def test_dashboard_requires_auth(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/auth/login' in response.headers.get('Location', '')


def test_accounts_listing(auth_client):
    response = auth_client.get('/accounts/')
    assert response.status_code == 200
    assert b'Compte courant' in response.data


def test_expenses_listing(auth_client):
    response = auth_client.get('/expenses/')
    assert response.status_code == 200


def test_incomes_listing(auth_client):
    response = auth_client.get('/incomes/')
    assert response.status_code == 200


def test_budgets_listing(auth_client):
    response = auth_client.get('/budgets/')
    assert response.status_code == 200


def test_categories_listing(auth_client):
    response = auth_client.get('/categories/')
    assert response.status_code == 200
    assert b'Logement' in response.data


def test_statistics_page(auth_client):
    response = auth_client.get('/statistics/')
    assert response.status_code == 200


def test_kakeibo_page(auth_client):
    response = auth_client.get('/kakeibo/')
    assert response.status_code == 200
    assert b'Kakeibo' in response.data


def test_reports_page(auth_client):
    response = auth_client.get('/reports/')
    assert response.status_code == 200


def test_notifications_page(auth_client):
    response = auth_client.get('/notifications/')
    assert response.status_code == 200


def test_faq_page_public(client):
    response = client.get('/faq')
    assert response.status_code == 200
    assert b'Kakeibo' in response.data
    assert b'Combien ai-je' in response.data


def test_admin_page(auth_client):
    response = auth_client.get('/admin/')
    assert response.status_code == 200
