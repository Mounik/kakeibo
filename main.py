#!/usr/bin/env python3
"""Point d'entrée de l'application Web Kakeibo Budget (Flask).

Usage :
    python main.py                     # serveur de développement Flask
    FLASK_ENV=production python main.py
"""
import os

from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
