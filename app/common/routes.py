from flask import render_template
from app.common import bp


@bp.route('/faq')
def faq():
    """Page FAQ : le principe de la méthode Kakeibo et comment utiliser l'application."""
    return render_template('faq.html', title='FAQ - La méthode Kakeibo')
