"""
WSGI-Konfiguration für die Bereitstellung über Gunicorn (Task 0.3).

Der Produktions-Container setzt DJANGO_SETTINGS_MODULE explizit; der
Default hier greift nur, falls das vergessen wird — daher zeigt er auf
die strengere Produktionskonfiguration, nicht auf dev.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
