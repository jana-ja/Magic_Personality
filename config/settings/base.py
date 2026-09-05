"""
Gemeinsame Einstellungen für alle Umgebungen.

Konfiguration kommt ausschließlich über Umgebungsvariablen (D-Entscheidung
aus ARCHITECTURE.md §11.1) — es liegen keine Secrets im Repository.
Lokal kann eine `.env`-Datei im Projektwurzelverzeichnis diese Variablen
setzen; siehe `.env.example`. In Docker/Produktion kommen echte
Umgebungsvariablen und eine `.env`-Datei wird nicht benötigt.
"""

from pathlib import Path

import environ

# apps/, config/, docs/ usw. liegen direkt im Projektwurzelverzeichnis.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])


# Anwendungen -----------------------------------------------------------
# Reihenfolge der eigenen Apps wie in ARCHITECTURE.md §2/§5.

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.colors",
    "apps.accounts",
    "apps.quiz",
    "apps.social",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Datenbank ---------------------------------------------------------------
# PostgreSQL laut ARCHITECTURE.md §3. Ausschließlich über DATABASE_URL
# angebunden (ARCHITECTURE.md §12) — der Wechsel auf eine verwaltete
# Instanz beim Cloud-Umzug ist damit eine Variablenänderung.

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Passwörter ----------------------------------------------------------------
# Der Argon2-Hasher (FR-U2) wird in Task 0.2 zusammen mit dem eigenen
# User-Modell aktiviert.

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},  # FR-U3
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalisierung -----------------------------------------------------
# UI ist zunächst nur Englisch, aber i18n-fähig ab v0.1 (NFR-4, D-15).
# LocaleMiddleware und Sprachkataloge kommen mit Task 0.4.

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True


# Statische Dateien -----------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
