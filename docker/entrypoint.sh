#!/bin/bash
set -euo pipefail

echo "========================================="
echo "  Kakeibo Budget - Starting Web App"
echo "========================================="

mkdir -p /app/data/uploads /app/data/backups /app/data/logs

export FLASK_ENV="${FLASK_ENV:-production}"
export DATABASE_URL="${DATABASE_URL:-sqlite:////app/data/kakeibo.db}"

echo "Applying database migrations..."
python -m flask db upgrade
if [ $? -ne 0 ]; then
    echo "Migrations failed, retrying after init..."
    python -m flask db init
    python -m flask db migrate -m "initial"
    python -m flask db upgrade
fi

echo "Database ready. Starting server..."

exec "$@"
