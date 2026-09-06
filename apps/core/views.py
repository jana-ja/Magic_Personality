"""
Views der Core-App.

Das Invite-Gate (Task 0.5) kommt später dazu — hier steht bisher nur
der Healthcheck aus Task 0.3.
"""

from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.views.decorators.http import require_GET


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
