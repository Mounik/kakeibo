from flask import Blueprint

bp = Blueprint('common', __name__)

from app.common import utils, context_processors, routes