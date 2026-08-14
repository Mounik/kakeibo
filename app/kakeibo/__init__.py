from flask import Blueprint

bp = Blueprint('kakeibo', __name__)

from app.kakeibo import routes, forms  # noqa: E402,F401
