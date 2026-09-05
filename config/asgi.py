"""
ASGI-Konfiguration. Aktuell ungenutzt (kein Django Channels, keine
WebSockets im Scope) — vorhanden, weil Django sie standardmäßig
erzeugt und einzelne Tools (z. B. manche Deployment-Checks) danach
suchen.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()
