# syntax=docker/dockerfile:1
#
# Produktions-Image (ARCHITECTURE.md §3, §11). Dasselbe Image läuft
# lokal über compose.yaml (Task 0.3) und später auf dem Server
# (Task 1.12) — es gibt kein separates "Dev-Image".

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .

# collectstatic braucht gültige Settings, aber weder eine echte
# Datenbank noch ein echtes Secret — DATABASES wird nur geparst, nie
# verbunden (siehe config/settings/base.py). Die folgenden Werte sind
# reine Platzhalter für diesen Build-Schritt; zur Laufzeit
# überschreiben die echten Umgebungsvariablen aus compose.yaml bzw.
# dem Server sie vollständig.
RUN SECRET_KEY=build-time-placeholder-not-a-real-secret \
    ALLOWED_HOSTS=build-time-placeholder \
    DATABASE_URL=postgres://build:build@build-time-placeholder:5432/build \
    SECURE_SSL_REDIRECT=False \
    python manage.py collectstatic --noinput

# Ohne Root laufen lassen.
RUN groupadd --system app \
    && useradd --system --gid app --no-create-home app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
