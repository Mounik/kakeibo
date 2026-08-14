# Kakeibo Budget

> Application Web de gestion de budget personnel basée sur la méthode japonaise **Kakeibo** (家計簿).

Kakeibo Budget vous aide à appliquer la méthode Kakeibo : planifier au début du mois, suivre chaque dépense au quotidien, analyser en fin de mois et améliorer vos finances en continu — le tout dans une interface Web moderne et réactive.

## Fonctionnalités

- **Méthode Kakeibo** : les 4 questions du début de mois, le journal mensuel et
  le bilan automatique en fin de mois.
- **4 grandes familles** de dépenses : besoins, envies, culture, imprévus.
- **Comptes** : courant, épargne, espèces, professionnel (multi-devises).
- **Revenus & dépenses** : saisie rapide, catégorisation, commerçant, récurrence.
- **Budgets** : budget global, mensuel ou par catégorie, avec alertes automatiques (HTMX) lorsqu'un budget approche sa limite.
- **Objectifs d'épargne** : progression, estimation et historique.
- **Statistiques & graphiques** (Chart.js) : dépenses par catégorie, évolution mensuelle/annuelle, taux d'épargne.
- **Import / Export** : import CSV, OFX, QIF ; export CSV, Excel, PDF.
- **API REST** complète, indépendante de l'interface HTML, documentée en OpenAPI/Swagger (`/apidocs/`).
- **Multi-utilisateurs** : authentification, rôles, isolation stricte des données par utilisateur, protection CSRF.

## Stack technique

| Couche | Technologies |
| --- | --- |
| Backend | Python 3.13+, Flask, SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, Marshmallow, Flask-Bcrypt, Flask-Mail, Gunicorn |
| Frontend | Jinja2, HTMX, Bootstrap 5, Chart.js |
| API | REST + OpenAPI (flasgger/Swagger UI) |
| Base de données | SQLite par défaut ; PostgreSQL / MariaDB / MySQL compatibles (via `DATABASE_URL`) |
| Asynchrone | Celery + Redis (architecture prête) |
| Infrastructure | Docker Compose, Traefik (HTTPS via Let's Encrypt) |

## Architecture

Application Flask modulaire découpée en Blueprints (Clean Architecture /
séparation des responsabilités) :

```text
app/
├── auth/          # connexion, inscription, profil
├── dashboard/     # tableau de bord + graphiques
├── accounts/      # comptes
├── incomes/       # revenus
├── expenses/      # dépenses
├── budgets/       # budgets et alertes
├── categories/    # catégories Kakeibo
├── statistics/    # statistiques (JSON pour Chart.js)
├── kakeibo/       # journal et bilans mensuels
├── reports/       # import / export
├── notifications/ # notifications
├── admin/         # administration
├── api/           # API REST (schémas Marshmallow)
└── common/        # utilitaires, contexte global, FAQ
```

Le modèle de données central est défini dans `app/models.py` (`User`, `Account`, `Category`, `Income`, `Expense`, `Budget`, `SavingGoal`, `MonthlyReview`, `Notification`, ...).

## Démarrage rapide

### Prérequis

- Python 3.13+
- (Optionnel) Docker + Docker Compose

### En local

```bash
# 1. Environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 2. Dépendances
pip install -r requirements.txt
pip install pytest

# 3. Configuration
cp .env.example .env

# 4. Base de données
flask db upgrade

# 5. (Optionnel) Données de démonstration
python scripts/seed_demo.py   # demo@kakeibo.example / demo1234

# 6. Lancement
python main.py
```

L'application est disponible sur http://localhost:5000 et la documentation API
sur http://localhost:5000/apidocs/.

### Avec Docker

```bash
cp .env.example .env        # éditer SECRET_KEY, TRAEFIK_DOMAIN, TRAEFIK_EMAIL
docker compose up -d --build
```

Services :

| Service | Port | Rôle |
| --- | --- | --- |
| `kakeibo` | 5000 (interne) | Application Flask servie par Gunicorn (4 workers) |
| `redis` | 6379 (interne) | Broker Celery / cache |
| `traefik` | 80 / 443 | Reverse proxy, HTTPS (Let's Encrypt), compression |
| `traefik` | 8081 | Entrée HTTP locale (sans TLS) pour le développement |

## Configuration

Toutes les variables sont documentées dans [`.env.example`](.env.example) :

- `SECRET_KEY`, `WTF_CSRF_SECRET_KEY` : secrets à changer en production.
- `DATABASE_URL` : `sqlite:///data/kakeibo.db` par défaut ; exemples
  PostgreSQL / MySQL fournis.
- `MAIL_*` : serveur SMTP pour les e-mails.
- `TRAEFIK_DOMAIN`, `TRAEFIK_EMAIL` : domaine et email ACME.

## Tests

```bash
pytest
```

Suite de tests (pytest) couvrant les pages, les flux métier et l'API (`tests/test_pages.py`, `tests/test_flows.py`, `tests/test_api.py`, `tests/test_auth.py`).

## API REST

Préfixée par `/api/`, indépendante de l'interface HTML :

- `POST /api/auth/login`, `GET /api/auth/me`
- `GET/POST /api/accounts`, `/api/incomes`, `/api/expenses`, `/api/categories`
- `GET/POST /api/budgets`, `/api/goals`
- `GET/PUT /api/kakeibo/<year>/<month>`
- `GET /api/statistics/current`, `/api/statistics/expenses-by-category`
- `GET /api/notifications`, `/api/users`

Documentation interactive : `/apidocs/` (Swagger UI) — spec : `/api/apispec.json`.

## Migrations

Les migrations Alembic sont versionnées dans `migrations/` :

```bash
flask db upgrade                    # applique les migrations
flask db migrate -m "description"   # nouvelle migration
```

## Documentation

- [`docs/INSTALLATION.md`](docs/INSTALLATION.md) — guide d'installation et de déploiement
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — architecture technique
- Page FAQ intégrée : `/faq`

## Roadmap

- Sauvegardes automatiques et rapports asynchrones (Celery, déjà préparé).
- Assistant IA : analyse des habitudes, détection de dépenses inhabituelles, prévisions et recommandations.
- Application mobile Android/iOS consommant l'API REST existante.

## Licence

Projet privé — tous droits réservés.
