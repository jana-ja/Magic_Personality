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
    # WhiteNoise (nur in Produktion, siehe config/settings/prod.py) wird
    # hier bewusst nicht eingetragen: sonst bräuchte auch die lokale
    # Entwicklung ohne Docker das Paket, das in requirements/prod.txt
    # liegt.
    "django.contrib.sessions.middleware.SessionMiddleware",
    # NFR-4/D-15: i18n-fähig ab v0.1, auch wenn v1 nur Englisch
    # ausliefert. Muss laut Django-Doku nach SessionMiddleware (braucht
    # ggf. die Session) und vor CommonMiddleware stehen.
    "django.middleware.locale.LocaleMiddleware",
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
                # Stellt u. a. LANGUAGE_CODE im Template bereit (siehe
                # templates/base.html, <html lang="...">).
                "django.template.context_processors.i18n",
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


# Nutzermodell ------------------------------------------------------------
# Eigenes User-Modell (Task 0.2, D-26) — muss gesetzt sein, bevor die
# erste Migration erzeugt wird. Django lässt das später nicht mehr
# ohne Weiteres austauschen.

AUTH_USER_MODEL = "accounts.User"


# Passwörter ----------------------------------------------------------------
# Argon2 zuerst aktiv (FR-U2). Die übrigen Hasher bleiben als Fallback
# gelistet, wie von Django empfohlen — sie werden für neue Passwörter
# nicht mehr verwendet, können aber vorhandene Hashes noch prüfen.

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

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
# Projektweite Sprachkataloge statt app-eigener locale/-Verzeichnisse,
# damit alle Übersetzungen an einer Stelle liegen.

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]


# Statische Dateien -----------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
