"""
Zugangssperre — Kernlogik (Task 0.5, D-09, FR-A1 bis FR-A4).

Von apps.core.middleware (prüft jede Anfrage) und apps.core.views
(setzt das Cookie nach korrektem Code) gemeinsam genutzt, damit beide
exakt dieselbe Definition von "gültig" verwenden.
"""

from django.conf import settings
from django.core import signing
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def is_exempt_path(path):
    """
    Pfade, die ohne gültiges Gate-Cookie erreichbar bleiben müssen.
    Genau die drei aus ARCHITECTURE.md §7: Gate-Seite, Healthcheck,
    statische Dateien — dazu robots.txt, das per Definition öffentlich
    abrufbar sein muss (FR-A4).

    `reverse("gate")` statt eines hart codierten Pfads, damit dieser
    nie von der tatsächlichen URL abweichen kann.
    """
    exempt_exact_paths = {reverse("gate"), "/healthz", "/robots.txt"}
    if path in exempt_exact_paths:
        return True
    static_prefix = "/" + settings.STATIC_URL.lstrip("/")
    return path.startswith(static_prefix)


def sign_gate_cookie():
    return signing.dumps({"granted": True}, salt=settings.GATE_COOKIE_SALT)


def gate_cookie_is_valid(request):
    raw_value = request.COOKIES.get(settings.GATE_COOKIE_NAME)
    if not raw_value:
        return False
    try:
        signing.loads(
            raw_value, salt=settings.GATE_COOKIE_SALT, max_age=settings.GATE_COOKIE_MAX_AGE
        )
    except signing.BadSignature:
        return False
    return True


def safe_next_url(request, candidate):
    """
    Nur ein lokales Ziel akzeptieren (kein Open Redirect über einen
    manipulierten `next`-Parameter) — dieselbe Prüfung, die Djangos
    eigener LoginView für seinen `next`-Parameter verwendet.
    """
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return "/"
