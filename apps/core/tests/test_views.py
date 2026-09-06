"""
Tests für /healthz (Task 0.3).

pytest-django legt für Tests mit dem `db`-Fixture eine Testdatenbank an
und wendet dabei alle Migrationen an — im Normalfall ist der Zustand
also "gesund", ohne dass hier irgendetwas eingerichtet werden muss.
Die Fehlerfälle (Datenbank weg, Migrationen ausstehend) werden über
gezielte Monkeypatches simuliert, nicht über eine echte kaputte
Datenbank.
"""

import pytest
from django.db import connections
from django.db.utils import OperationalError
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_healthz_returns_ok_when_database_and_migrations_are_fine(client):
    response = client.get(reverse("healthz"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_healthz_returns_503_when_the_database_is_unreachable(client, monkeypatch):
    def _simulate_outage(*args, **kwargs):
        raise OperationalError("simulated outage")

    monkeypatch.setattr(connections["default"], "ensure_connection", _simulate_outage)

    response = client.get(reverse("healthz"))

    assert response.status_code == 503
    assert response.json()["status"] == "error"


def test_healthz_returns_503_when_migrations_are_pending(client, monkeypatch):
    monkeypatch.setattr("apps.core.views._pending_migrations_exist", lambda connection: True)

    response = client.get(reverse("healthz"))

    assert response.status_code == 503
    assert response.json()["status"] == "error"


def test_healthz_only_accepts_get(client):
    response = client.post(reverse("healthz"))

    assert response.status_code == 405
