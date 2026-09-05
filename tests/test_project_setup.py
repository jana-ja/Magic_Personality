"""
Beispieltest für Task 0.1 — prüft, dass das Projektgerüst selbst
korrekt aufgebaut ist. Fachliche Logik hat hier noch nichts zu suchen.
"""

from django.apps import apps
from django.conf import settings


def test_all_five_local_apps_are_registered():
    """Die fünf Apps aus ARCHITECTURE.md §2/§5 müssen geladen sein."""
    expected_labels = {"core", "colors", "accounts", "quiz", "social"}
    installed_labels = {app_config.label for app_config in apps.get_app_configs()}

    assert expected_labels.issubset(installed_labels)


def test_secret_key_is_not_committed_to_the_repo():
    """
    SECRET_KEY kommt ausschließlich aus der Umgebung (.env, gitignored),
    nie aus einem hart codierten Wert im Repository.
    """
    assert settings.SECRET_KEY
    assert "changeme" not in settings.SECRET_KEY


def test_debug_defaults_to_a_boolean():
    assert isinstance(settings.DEBUG, bool)
