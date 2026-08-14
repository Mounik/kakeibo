# Architecture technique

## Vue d'ensemble

Application Web Flask (3.13+) modulaire, structurée en Blueprints, avec API
REST indépendante, interface Jinja2 + HTMX + Bootstrap 5 + Chart.js, et
architecture prête pour Celery/Redis.

```
app/
├── auth/          # authentification, inscription, profil
├── dashboard/     # tableau de bord + graphiques
├── accounts/      # comptes
├── incomes/       # revenus
├── expenses/      # dépenses
├── budgets/       # budgets et alertes
├── categories/    # catégories Kakeibo (besoins/envies/culture/imprévus)
├── statistics/    # statistiques (endpoints JSON pour Chart.js)
├── kakeibo/       # journal et bilans mensuels
├── reports/       # import CSV/OFX/QIF, export CSV/XLSX/PDF
├── notifications/ # notifications
├── admin/         # administration
├── api/           # API REST + schémas Marshmallow
└── common/        # utilitaires partagés
```

## Couches

Chaque Blueprint suit le principe de séparation des responsabilités :

- **routes.py** : endpoints HTTP (rendu Jinja2 ou JSON)
- **forms.py** : formulaires WTForms
- **templates/*** : vues Jinja2 avec fragments HTMX

La logique métier est centralisée dans les modèles (`app/models.py`) et les
services communs (`app/common/utils.py`).

## Démarrage de l'application

`app/__init__.py` expose la factory `create_app(config_name)` :

1. Chargement de la configuration (`config.py`), selon `FLASK_ENV`
2. Initialisation des extensions : SQLAlchemy, Flask-Migrate, Flask-Login,
   CSRF, Marshmallow, Bcrypt, Mail, Celery
3. Enregistrement des 13 Blueprints
4. Context processors globaux (utilisateur, catégories Kakeibo, données courantes)
5. Gestionnaires d'erreurs 404/403/500
6. Documentation OpenAPI via flasgger (`/apidocs/`)

## Modèle de données

`app/models.py` : User, Account, Category (kind = needs|wants|culture|unexpected),
Income, Expense, Budget, SavingGoal, MonthlyReview, Notification, Subscription,
Badge, Challenge. Les propriétés `owner_id` rendent les données multi-utilisateurs.

## API REST

Préfixée par `/api/`, indépendante de l'interface HTML :

- `/api/auth/login`, `/api/auth/me`
- `/api/accounts`, `/api/incomes`, `/api/expenses`, `/api/categories`
- `/api/budgets`, `/api/goals`, `/api/kakeibo/<year>/<month>`
- `/api/statistics/current`, `/api/statistics/expenses-by-category`
- `/api/notifications`, `/api/users`

Sérialisation Marshmallow (`app/api/schemas.py`), réponses JSON, erreurs 401/403/404.
Documentation : `/apidocs/` (Swagger UI), spec `/api/apispec.json`.

## Frontend

- Jinja2 + HTMX pour le rendu partiel (fragments `_card.html`, formulaires
  soumis en `hx-post`)
- Bootstrap 5 (CDN) et Chart.js pour les graphiques
- Thème et sidebar dans `app/templates/base.html`, styles dans
  `app/static/css/app.css`

## Qualité

- Tests pytest : `tests/` (pages, flux, API)
- Migrations Alembic : `migrations/`
- Logging structuré et gestion centralisée des exceptions
- Conteneurisation : `Dockerfile`, `docker-compose.yml` (gunicorn, redis, traefik)
