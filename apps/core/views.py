"""Views der Core-App: Healthcheck (Task 0.3) und Zugangssperre (Task 0.5)."""

from django.conf import settings
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.db.utils import OperationalError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_http_methods

from . import gate as gate_logic
from .models import GateAttempt
from .rate_limit import rate_limit


def _pending_migrations_exist(connection) -> bool:
    """True, wenn für diese Verbindung noch nicht angewendete Migrationen existieren."""
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    return bool(plan)


@require_GET
def healthz(request):
    """
    Healthcheck für Docker Compose (Task 0.3) und später den
    Produktions-Reverse-Proxy (Task 1.12).

    Prüft zwei Dinge, die beide gegeben sein müssen, bevor ein
    Container als "gesund" gilt: die Datenbank ist erreichbar, und es
    stehen keine unangewendeten Migrationen aus (ARCHITECTURE.md §11.2
    — Migrationen laufen als eigener Deploy-Schritt vor dem Start, ein
    Container mit ausstehenden Migrationen lief auf einem alten Schema
    hoch).
    """
    connection = connections["default"]

    try:
        connection.ensure_connection()
    except OperationalError:
        return JsonResponse({"status": "error", "detail": "database unreachable"}, status=503)

    if _pending_migrations_exist(connection):
        return JsonResponse({"status": "error", "detail": "pending migrations"}, status=503)

    return JsonResponse({"status": "ok"})


@require_http_methods(["GET", "POST"])
@rate_limit(
    GateAttempt,
    max_attempts=settings.GATE_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=settings.GATE_RATE_LIMIT_WINDOW_SECONDS,
)
def gate(request):
    """
    Einzige Seite, die ohne Gate-Cookie erreichbar ist (FR-A1). Prüft
    den eingegebenen Code gegen settings.INVITE_CODE und setzt bei
    Erfolg das signierte, langlebige Cookie aus apps.core.gate.
    """
    next_url = gate_logic.safe_next_url(
        request, request.GET.get("next") or request.POST.get("next")
    )

    if gate_logic.gate_cookie_is_valid(request):
        return redirect(next_url)

    error = None

    if request.method == "POST":
        submitted_code = request.POST.get("code", "")
        if constant_time_compare(submitted_code, settings.INVITE_CODE):
            response = redirect(next_url)
            response.set_cookie(
                settings.GATE_COOKIE_NAME,
                gate_logic.sign_gate_cookie(),
                max_age=settings.GATE_COOKIE_MAX_AGE,
                httponly=True,
                secure=settings.SESSION_COOKIE_SECURE,
                samesite="Lax",
            )
            return response
        error = _("Incorrect invite code.")

    return render(request, "core/gate.html", {"error": error, "next": next_url})


def robots_txt(request):
    """FR-A4: die Anwendung wird für Suchmaschinen gesperrt."""
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")
