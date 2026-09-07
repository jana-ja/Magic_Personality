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


def test_custom_user_model_is_active():
    """D-26: eigenes User-Modell, gesetzt vor der ersten Migration."""
    assert settings.AUTH_USER_MODEL == "accounts.User"


def test_argon2_is_the_active_password_hasher():
    """
    FR-U2: Argon2 muss der *erste* Hasher sein — nur der erste wird für
    neue Passwörter verwendet, die übrigen dienen nur der Prüfung
    vorhandener Hashes mit älteren Verfahren.
    """
    assert settings.PASSWORD_HASHERS[0] == "django.contrib.auth.hashers.Argon2PasswordHasher"


def test_locale_middleware_is_active():
    """NFR-4/D-15: i18n-fähig ab v0.1, auch wenn v1 nur Englisch ausliefert."""
    assert "django.middleware.locale.LocaleMiddleware" in settings.MIDDLEWARE


def test_locale_paths_point_at_the_project_locale_directory():
    from pathlib import Path

    assert Path(settings.BASE_DIR, "locale") in [Path(p) for p in settings.LOCALE_PATHS]
