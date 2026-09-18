"""
Tests für `LANGUAGES` (D-69).

v1 liefert nur Englisch aus (ARCHITECTURE.md §8) — `LocaleMiddleware`
ist trotzdem aktiv (Task 0.4, D-15) und würde ohne die Einschränkung
auf `LANGUAGES = [("en", ...)]` den Accept-Language-Header auswerten.
Eigene Texte fallen dann zwar mangels deutschem Katalog unter
`locale/` auf Englisch zurück — aber Wörter, die zufällig mit einem
von Django selbst mitgelieferten Text übereinstimmen ("Search",
"Log out"), wurden trotzdem auf Deutsch angezeigt, weil Djangos
Katalogsuche alle Apps zusammenfasst, nicht nur unsere eigene.
"""

import pytest
from django.conf import settings

from apps.accounts.models import Profile, User
from apps.core import gate

pytestmark = pytest.mark.django_db


@pytest.fixture
def gate_cookie(client):
    client.cookies[settings.GATE_COOKIE_NAME] = gate.sign_gate_cookie()
    return client


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


def test_a_german_browser_still_gets_the_english_page(gate_cookie):
    response = gate_cookie.get("/colors/", HTTP_ACCEPT_LANGUAGE="de-DE,de;q=0.9,en;q=0.8")

    html = response.content.decode()
    assert '<html lang="en">' in html


def test_django_builtin_translations_do_not_leak_through_for_matching_strings(gate_cookie, user):
    """
    Regression: "Search" (Hauptnavigation) und "Log out" trafen
    zufällig denselben Wortlaut wie in Django selbst mitgelieferte
    Auth-/Admin-Texte — deren eingebaute deutsche Übersetzung ("Suchen",
    "Abmelden") schlug durch, obwohl das Projekt selbst gar kein
    Deutsch ausliefert. Beide Texte erscheinen nur für Angemeldete
    (Search: D-68, Log out: D-55) — daher hier eingeloggt.
    """
    gate_cookie.force_login(user)

    response = gate_cookie.get("/colors/", HTTP_ACCEPT_LANGUAGE="de-DE,de;q=0.9,en;q=0.8")

    html = response.content.decode()
    assert "Search" in html
    assert "Log out" in html
    assert "Suchen" not in html
    assert "Abmelden" not in html
