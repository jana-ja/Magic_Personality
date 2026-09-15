"""
Produktion.

DEBUG steht fest auf False, ALLOWED_HOSTS hat bewusst keinen Default —
ein fehlender Wert lässt die Anwendung beim Start fehlschlagen statt
unbemerkt mit offenem Host-Header zu laufen.
"""

from .base import *  # noqa: F401,F403
from .base import MIDDLEWARE, env

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Ohne das hält Django jedes POST-Formular (Gate, später Login) für
# unsicher: Same-Origin wird bei HTTPS über den Origin-Header geprüft,
# und Django kennt "https://" nur über ALLOWED_HOSTS hinaus, wenn es
# hier explizit steht (Django >= 4.0, CSRF_TRUSTED_ORIGINS braucht
# vollständige Origins samt Schema, kein bloßer Hostname).
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

# Default True, weil ein echter Produktionsserver hinter Caddy TLS
# terminiert (Task 1.12). Das lokale Docker Compose aus Task 0.3 hat
# noch keinen Reverse Proxy und läuft nur über HTTP — dort wird diese
# Variable bewusst auf False gesetzt, sonst entstünde eine
# Redirect-Schleife (https:// wird nie erreicht).
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)

# Der Healthcheck in compose.yaml läuft *innerhalb* des "web"-Containers
# gegen "localhost:8000" — nie über Caddy, also nie mit
# X-Forwarded-Proto. Ohne diese Ausnahme leitet SECURE_SSL_REDIRECT
# auch diese interne Anfrage auf https:// um, was am eigenen,
# unverschlüsselten Gunicorn-Socket mit einem SSL-Handshake-Fehler
# scheitert (lokal nachgestellt: `docker compose -f compose.yaml -f
# compose.prod.yaml up` ließ den Healthcheck endlos fehlschlagen, bis
# diese Zeile dazukam). Betrifft nur den Redirect-Zwang, nicht die
# Erreichbarkeit von außen — Caddy erzwingt HTTPS an der eigenen Kante
# ohnehin schon (automatic HTTP->HTTPS redirect).
SECURE_REDIRECT_EXEMPT = [r"^healthz$"]

# Caddy terminiert TLS und leitet an "web" nur noch per HTTP im
# internen Compose-Netzwerk weiter (D-52) — ohne diese Zeile hält
# Django jede Anfrage für unverschlüsselt (request.is_secure() wäre
# immer False), SECURE_SSL_REDIRECT würde also in eine Endlosschleife
# laufen (https:// wird von Caddy schon terminiert, aber Django leitet
# trotzdem wieder auf https:// weiter). Caddys reverse_proxy setzt
# X-Forwarded-Proto von sich aus bei jeder Anfrage; sicher zu
# vertrauen, weil "web" laut compose.prod.yaml keinen Host-Port
# veröffentlicht und deshalb nur über Caddy erreichbar ist.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Bewusst niedrig angesetzt (1 Stunde statt der oft empfohlenen ein bis
# zwei Jahre): HSTS lässt sich im Browser-Cache nicht zurücknehmen, ein
# Fehler im frischen Caddy/TLS-Aufbau würde also für die volle Dauer
# aussperren. Nach ein paar Tagen unauffälligem Betrieb anheben (siehe
# docs/DEPLOYMENT.md) — kein Include-Subdomains/Preload, solange es nur
# die eine Domain gibt.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


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
