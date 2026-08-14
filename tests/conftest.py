import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db as _db  # noqa: E402
from app.models import User, Account, Category, Expense, Income, Budget, MonthlyReview  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / 'test_kakeibo.db'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

    class TestConfig:
        TESTING = True
        DEBUG = True
        SECRET_KEY = 'test-secret-key'
        WTF_CSRF_ENABLED = False
        LOGIN_DISABLED = False
        SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
        REDIS_URL = 'redis://localhost:6379/0'
        CELERY_BROKER_URL = 'redis://localhost:6379/0'
        CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
        UPLOAD_FOLDER = str(tmp_path / 'uploads')
        BACKUP_PATH = str(tmp_path / 'backups')
        LOG_FILE = str(tmp_path / 'logs' / 'kakeibo.log')
        MAIL_SERVER = 'localhost'
        MAIL_PORT = 25
        MAIL_USE_TLS = False
        MAIL_USERNAME = None
        MAIL_DEFAULT_SENDER = 'test@example.com'
        ITEMS_PER_PAGE = 20

    app = create_app('testing')
    app.config.update({k: v for k, v in vars(TestConfig).items() if k.isupper()})

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def user(app):
    with app.app_context():
        u = User(
            username='testuser',
            email='test@example.com',
            locale='fr',
            currency='EUR',
            is_admin=True,
        )
        u.set_password('password123')
        _db.session.add(u)
        _db.session.commit()

        for name, kind, color in [
            ('Logement', 'needs', '#ef4444'),
            ('Restaurants', 'wants', '#f59e0b'),
            ('Livres', 'culture', '#8b5cf6'),
            ('Urgences', 'unexpected', '#ec4899'),
        ]:
            _db.session.add(Category(name=name, kind=kind, color=color, is_system=True, owner_id=u.id))

        _db.session.add(Account(
            name='Compte courant', type='checking', currency='EUR',
            initial_balance=100, balance=100, is_main=True, owner_id=u.id,
        ))
        _db.session.add(Account(
            name='Épargne', type='savings', currency='EUR',
            initial_balance=500, balance=500, owner_id=u.id,
        ))
        _db.session.commit()
        return u


@pytest.fixture()
def auth_client(client, user):
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123',
    })
    return client
