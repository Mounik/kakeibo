def test_home_redirects_to_login(client):
    response = client.get('/')
    assert response.status_code == 302


def test_login_page(client):
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert 'Connexion'.encode() in response.data or b'Kakeibo' in response.data


def test_register_flow(client, db):
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'supersecret',
        'password2': 'supersecret',
    }, follow_redirects=False)
    assert response.status_code in (302, 200)


def test_login_success(auth_client):
    response = auth_client.get('/')
    assert response.status_code == 200


def test_login_wrong_password(client):
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'wrong',
    }, follow_redirects=True)
    assert b'invalide' in response.data or b'Invalid' in response.data


def test_logout(auth_client):
    response = auth_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200


def test_profile_page(auth_client):
    response = auth_client.get('/auth/profile')
    assert response.status_code == 200
