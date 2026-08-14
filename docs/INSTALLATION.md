# Guide d'installation et de déploiement

## Prérequis

- Python 3.13+
- Docker + Docker Compose (déploiement conteneurisé)
- Traefik (reverse proxy, optionnel en développement)

## Développement local

```bash
# 1. Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt
pip install pytest   # pour les tests

# 3. Configurer l'environnement
cp .env.example .env

# 4. Appliquer les migrations et créer les tables
flask db upgrade

# 5. (Optionnel) Données de démonstration
python scripts/seed_demo.py   # demo@kakeibo.example / demo1234

# 6. Lancer le serveur de développement
python main.py
```

L'application est alors disponible sur http://localhost:5000 et la
documentation OpenAPI (Swagger) sur http://localhost:5000/apidocs/.

## Exécution des tests

```bash
pytest
```

## Déploiement avec Docker

```bash
# 1. Configurer les variables d'environnement de production
cp .env.example .env
# Éditer SECRET_KEY, TRAEFIK_DOMAIN, TRAEFIK_EMAIL, MAIL_*

# 2. Lancer l'application, Redis et Traefik
docker compose up -d --build
```

L'application est servie par **gunicorn** (4 workers) dans le conteneur
`kakeibo`. Traefik termine le TLS via Let's Encrypt et redirige HTTP → HTTPS.

Vérifications :

```bash
docker compose ps                    # tous les services doivent être "healthy"
docker compose logs -f kakeibo       # logs applicatifs
docker compose exec kakeibo python -m flask db current
```

## Sauvegardes

Les données SQLite, les imports et les sauvegardes sont persistés dans le
volume Docker `kakeibo_data` (`/app/data`). Pour une sauvegarde manuelle :

```bash
docker run --rm -v kakeibo_data:/data -v "$PWD":/backup alpine \
    tar czf /backup/kakeibo-backup-$(date +%F).tar.gz /data
```

## Bascule vers PostgreSQL / MariaDB

Modifier uniquement `DATABASE_URL` dans `.env` :

```env
DATABASE_URL=postgresql://kakeibo:password@db:5432/kakeibo
# ou
DATABASE_URL=mysql+pymysql://kakeibo:password@db:3306/kakeibo
```

Puis relancer `docker compose up -d` et `flask db upgrade`.

## Celery / Redis

L'architecture est prête pour Celery (sauvegardes automatiques, rapports PDF,
notifications) : `redis` est déjà démarré dans `docker-compose.yml`. Ajouter un
service `worker` en exécutant `celery -A app.tasks:celery_app worker` si les
tâches asynchrones sont activées.
