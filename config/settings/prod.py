"""
Produktion.

DEBUG steht fest auf False, ALLOWED_HOSTS hat bewusst keinen Default —
ein fehlender Wert lässt die Anwendung beim Start fehlschlagen statt
unbemerkt mit offenem Host-Header zu laufen.

Weitere produktionsspezifische Härtung (HSTS, sichere Cookies) kommt
zusammen mit dem Invite-Gate in Task 0.5 und dem CI-Deploy-Check
`manage.py check --deploy` in Task 0.6.
"""

from .base import *  # noqa: F401,F403
from .base import MIDDLEWARE, env

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Default True, weil ein echter Produktionsserver hinter Caddy TLS
# terminiert (Task 1.12). Das lokale Docker Compose aus Task 0.3 hat
# noch keinen Reverse Proxy und läuft nur über HTTP — dort wird diese
# Variable bewusst auf False gesetzt, sonst entstünde eine
# Redirect-Schleife (https:// wird nie erreicht).
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)


# Statische Dateien --------------------------------------------------------
# WhiteNoise übernimmt das Ausliefern (ARCHITECTURE.md §3) — bewusst nur
# hier und nicht in base.py, damit lokale Entwicklung ohne Docker das
# Paket aus requirements/prod.txt nicht braucht.

MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
