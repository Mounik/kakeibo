from flask import Blueprint

bp = Blueprint('budgets', __name__)

from app.budgets import routes, forms