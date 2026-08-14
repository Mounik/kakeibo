import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')


def _database_uri() -> str:
    url = os.environ.get('DATABASE_URL', '')
    if url.startswith('sqlite:///') and url != 'sqlite:///:memory:':
        path = url[len('sqlite:///'):]
        if path and not path.startswith('/'):
            url = f'sqlite:///{(BASE_DIR / path).resolve()}'
    return url or f'sqlite:///{BASE_DIR}/data/kakeibo.db'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'dev-csrf-secret-key')

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }

    REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Kakeibo Budget <noreply@kakeibo.local>')

    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', 12))

    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('PERMANENT_SESSION_LIFETIME', 86400))

    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))
    UPLOAD_FOLDER = BASE_DIR / os.environ.get('UPLOAD_FOLDER', 'data/uploads')
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'csv,ofx,qif,xlsx,xls').split(','))

    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))

    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / os.environ.get('LOG_FILE', 'data/logs/kakeibo.log')

    BOOTSTRAP_THEME = os.environ.get('BOOTSTRAP_THEME', 'flatly')
    CHART_JS_VERSION = os.environ.get('CHART_JS_VERSION', '4.4.1')
    HTMX_VERSION = os.environ.get('HTMX_VERSION', '1.9.10')
    ALPINE_VERSION = os.environ.get('ALPINE_VERSION', '3.13.0')

    BACKUP_SCHEDULE = os.environ.get('BACKUP_SCHEDULE', '0 2 * * *')
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    BACKUP_PATH = BASE_DIR / os.environ.get('BACKUP_PATH', 'data/backups')

    BOOTSTRAP_SERVE_LOCAL = True
    BOOTSTRAP_USE_MINIFIED = True
    BOOTSTRAP_USE_CDN = False


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///:memory:'
    )
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}