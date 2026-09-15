"""
Einfaches, datenbankgestütztes Rate Limiting.

Bewusst kein Redis (ARCHITECTURE.md §13 — bei 3–10 Nutzenden reine
Betriebslast): eine simple Zählung in Postgres reicht. django-axes
bleibt für Task 2.2 (Login) vorgesehen; hier ist der "eigene
Decorator für Registrierung und Invite-Gate" aus ARCHITECTURE.md §7 —
gedacht zur Wiederverwendung, sobald Task 2.2 die Registrierung baut.
"""

from functools import wraps

from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _


def client_ip(request):
    """
    Client-IP für Rate Limiting.

    In Produktion (D-51) veröffentlicht compose.prod.yaml für "web"
    bewusst keinen Host-Port — Caddy ist der einzige Weg hinein, jede
    Anfrage bei "web" ist also schon einmal durch Caddy gelaufen.
    REMOTE_ADDR ist deshalb dort immer Caddys eigene Container-IP,
    nicht die des Clients; die echte Client-IP steht in
    X-Forwarded-For, das Caddy bei jeder Anfrage um den soeben
    gesehenen Peer ERGÄNZT statt zu ersetzen. Deshalb zählt gezielt der
    LETZTE Eintrag der Liste: ein Client könnte selbst einen
    X-Forwarded-For-Header mitschicken und sich so eine andere IP
    vorschummeln, Caddys eigene Beobachtung hängt aber immer hinten an
    — vertrauenswürdig, weil "web" nie direkt erreichbar ist.

    Ohne Caddy davor (lokale Entwicklung, Tests) fehlt der Header
    komplett; REMOTE_ADDR bleibt dann die einzige und korrekte Quelle.
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.rsplit(",", 1)[-1].strip()
    return request.META.get("REMOTE_ADDR", "")


def is_rate_limited(model, ip_address, *, max_attempts, window_seconds):
    """
    True, wenn `ip_address` in den letzten `window_seconds` Sekunden
    bereits `max_attempts`-mal in `model` protokolliert wurde.

    `model` muss ein Feld `ip_address` und `created_at` haben (siehe
    apps.core.models.GateAttempt).
    """
    window_start = timezone.now() - timezone.timedelta(seconds=window_seconds)
    recent_attempts = model.objects.filter(
        ip_address=ip_address, created_at__gte=window_start
    ).count()
    return recent_attempts >= max_attempts


def record_attempt(model, ip_address):
    model.objects.create(ip_address=ip_address)


def rate_limit(model, *, max_attempts, window_seconds):
    """
    View-Decorator: blockiert POST-Anfragen mit HTTP 429, wenn die
    Client-IP das Limit in `model` bereits überschritten hat.
    Protokolliert jeden POST-Versuch — auch geblockte — damit das
    Zeitfenster korrekt weiterläuft.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.method == "POST":
                ip = client_ip(request)
                if is_rate_limited(
                    model, ip, max_attempts=max_attempts, window_seconds=window_seconds
                ):
                    return HttpResponse(
                        _("Too many attempts. Please try again later."),
                        status=429,
                        content_type="text/plain",
                    )
                record_attempt(model, ip)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
