from flask import Flask, redirect, url_for, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from celery import Celery, Task
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
ma = Marshmallow()
bcrypt = Bcrypt()
mail = Mail()


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config['CELERY'])
    celery_app.set_default()
    app.extensions['celery'] = celery_app
    return celery_app


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    from config import config as config_dict

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_dict[config_name])

    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BACKUP_PATH'], exist_ok=True)
    os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    ma.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Authentification requise.'}), 401
        return redirect(url_for('auth.login', next=request.path))

    app.config['CELERY'] = {
        'broker_url': app.config['CELERY_BROKER_URL'],
        'result_backend': app.config['CELERY_RESULT_BACKEND'],
        'task_ignore_result': True,
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'Europe/Paris',
        'enable_utc': True,
    }
    celery_init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.accounts import bp as accounts_bp
    app.register_blueprint(accounts_bp, url_prefix='/accounts')

    from app.incomes import bp as incomes_bp
    app.register_blueprint(incomes_bp, url_prefix='/incomes')

    from app.expenses import bp as expenses_bp
    app.register_blueprint(expenses_bp, url_prefix='/expenses')

    from app.budgets import bp as budgets_bp
    app.register_blueprint(budgets_bp, url_prefix='/budgets')

    from app.categories import bp as categories_bp
    app.register_blueprint(categories_bp, url_prefix='/categories')

    from app.statistics import bp as statistics_bp
    app.register_blueprint(statistics_bp, url_prefix='/statistics')

    from app.kakeibo import bp as kakeibo_bp
    app.register_blueprint(kakeibo_bp, url_prefix='/kakeibo')

    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')

    from app.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.common import bp as common_bp
    app.register_blueprint(common_bp)

    try:
        from flasgger import Swagger
        swagger_config = {
            'title': 'Kakeibo Budget API',
            'description': 'API REST de l\'application de gestion de budget Kakeibo.',
            'version': '1.0.0',
            'termsOfService': '',
            'specs': [
                {
                    'endpoint': 'apispec',
                    'route': '/api/apispec.json',
                    'rule_filter': lambda rule: rule.rule.startswith('/api/'),
                    'model_filter': lambda tag: True,
                }
            ],
            'static_url_path': '/apidocs/static',
            'swagger_ui': True,
            'specs_route': '/apidocs/',
            'headers': [],
        }
        Swagger(app, config=swagger_config)
    except ImportError:
        app.logger.warning('flasgger non installé : documentation OpenAPI désactivée.')

    from app.common.context_processors import (
        inject_globals, inject_user_data, inject_kakeibo_categories, inject_today,
    )
    app.context_processor(inject_globals)
    app.context_processor(inject_user_data)
    app.context_processor(inject_kakeibo_categories)
    app.context_processor(inject_today)

    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
