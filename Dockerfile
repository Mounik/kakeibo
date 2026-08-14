FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libjpeg-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid 1000 kakeibo && \
    adduser --uid 1000 --gid 1000 --disabled-password --gecos "Kakeibo User" kakeibo

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=kakeibo:kakeibo app/ ./app/
COPY --chown=kakeibo:kakeibo migrations/ ./migrations/
COPY --chown=kakeibo:kakeibo scripts/ ./scripts/
COPY --chown=kakeibo:kakeibo main.py config.py pytest.ini ./
COPY --chown=kakeibo:kakeibo docker/ ./docker/

RUN mkdir -p /app/data/uploads /app/data/backups /app/data/logs && \
    chown -R kakeibo:kakeibo /app /app/data

USER kakeibo

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD ["bash", "/app/docker/healthcheck.sh"]

ENTRYPOINT ["bash", "/app/docker/entrypoint.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "main:app"]
