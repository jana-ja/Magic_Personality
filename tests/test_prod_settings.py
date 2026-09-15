"""
Tests für config/settings/prod.py (Task 1.12, D-52).

Der reguläre Testlauf verwendet durchgehend config.settings.dev
(pyproject.toml, DJANGO_SETTINGS_MODULE) — Djangos Settings lassen
sich pro Prozess nur einmal konfigurieren, ein echter Wechsel auf
config.settings.prod mitten im Testlauf würde also entweder
fehlschlagen oder globalen Zustand (INSTALLED_APPS, MIDDLEWARE) für
alle anderen Tests verändern.

`runpy.run_module()` führt das Modul stattdessen in einem eigenen,
isolierten Namensraum aus — echter Code, echte Berechnung, aber ohne
Djangos aktive Konfiguration anzufassen. Die dafür nötigen
Pflicht-Umgebungsvariablen (SECRET_KEY, DATABASE_URL, INVITE_CODE)
kommen aus config/settings/base.py.
"""

import runpy

import pytest

REQUIRED_ENV = {
    "SECRET_KEY": "test-secret-key-not-for-real-use-1234567890",
    "DATABASE_URL": "postgres://u:p@localhost:5432/d",
    "INVITE_CODE": "test-invite-code",
}


@pytest.fixture
def prod_settings(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("ALLOWED_HOSTS", "example.com,www.example.com")

    def _load(**extra_env):
        for key, value in extra_env.items():
            monkeypatch.setenv(key, value)
        return runpy.run_module("config.settings.prod", run_name="__test_prod_settings__")

    return _load


def test_csrf_trusted_origins_are_derived_from_allowed_hosts(prod_settings):
    """
    Ohne das lehnt Django jedes POST-Formular (Gate, später Login) über
    HTTPS als "unsicher" ab — der Origin-Header wird gegen genau diese
    Liste geprüft, ALLOWED_HOSTS allein reicht Django seit Version 4
    nicht mehr.
    """
    settings = prod_settings()

    assert settings["CSRF_TRUSTED_ORIGINS"] == ["https://example.com", "https://www.example.com"]


def test_secure_proxy_ssl_header_trusts_caddys_forwarded_proto(prod_settings):
    """
    Ohne das hält Django jede Anfrage für unverschlüsselt, weil Caddy
    TLS terminiert und nur noch per HTTP an "web" weiterreicht —
    SECURE_SSL_REDIRECT liefe sonst in eine Endlosschleife.
    """
    settings = prod_settings()

    assert settings["SECURE_PROXY_SSL_HEADER"] == ("HTTP_X_FORWARDED_PROTO", "https")


def test_hsts_is_enabled_with_a_conservative_default(prod_settings):
    """
    `manage.py check --deploy` warnte vor D-52 vor komplett fehlendem
    HSTS (security.W004) — jetzt gesetzt, aber bewusst niedrig, weil
    ein Browser HSTS über die volle Dauer nicht zurücknehmen lässt.
    """
    settings = prod_settings()

    assert settings["SECURE_HSTS_SECONDS"] > 0


def test_hsts_seconds_is_configurable_via_env(prod_settings):
    settings = prod_settings(SECURE_HSTS_SECONDS="86400")

    assert settings["SECURE_HSTS_SECONDS"] == 86400


def test_healthz_is_exempt_from_the_ssl_redirect(prod_settings):
    """
    compose.yaml prüft "web" per Healthcheck über reines HTTP direkt im
    Container — nie über Caddy, also nie mit X-Forwarded-Proto. Ohne
    diese Ausnahme leitet SECURE_SSL_REDIRECT auch diese interne
    Anfrage auf https:// um, was am eigenen, unverschlüsselten
    Gunicorn-Socket mit einem SSL-Handshake-Fehler scheitert (lokal
    nachgestellt: siehe D-52 in docs/DECISIONS.md — ohne diese Zeile
    blieb "web" unter compose.prod.yaml dauerhaft "unhealthy").
    """
    settings = prod_settings()

    assert settings["SECURE_REDIRECT_EXEMPT"] == [r"^healthz$"]
