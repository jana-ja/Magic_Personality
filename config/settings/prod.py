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
from .base import env

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
