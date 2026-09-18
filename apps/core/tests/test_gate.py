"""
Tests für die Zugangssperre (Task 0.5, FR-A1 bis FR-A4, D-09).

Der wichtigste Fall steht zuerst: ohne Cookie ist wirklich jede URL
gesperrt, auch eine, die gar nicht existiert (genau das verlangt die
Definition of Done in docs/ROADMAP.md).
"""

import pytest
from django.conf import settings
from django.core import signing

from apps.core.models import GateAttempt

pytestmark = pytest.mark.django_db

GATE_URL = "/gate/"


# Ohne Cookie ist alles gesperrt ------------------------------------------


def test_unknown_path_without_cookie_redirects_to_the_gate(client):
    response = client.get("/this-path-does-not-exist/")

    assert response.status_code == 302
    assert response.url.startswith(GATE_URL)


@pytest.mark.parametrize(
    "path",
    ["/u/someone/", "/search/", "/search/colors/", "/friends/1/accept/"],
)
def test_social_urls_without_cookie_redirect_to_the_gate(client, path):
    """
    Task 3.6/Release-Durchsicht v1.0: die Middleware kennt keine
    Ausnahmen für die mit M3 neu hinzugekommenen Pfade (apps.social)
    — schon `test_unknown_path_without_cookie_redirects_to_the_gate`
    belegt das strukturell (die Middleware unterscheidet nicht nach
    Pfad), dieser Test hält es zusätzlich für die tatsächlichen
    v1.0-URLs ausdrücklich fest, statt es nur aus der allgemeinen
    Regel zu folgern.
    """
    response = client.get(path)

    assert response.status_code == 302
    assert response.url.startswith(GATE_URL)


def test_admin_without_cookie_redirects_to_the_gate(client):
    """FR-A1: 'kein API-Endpunkt außer der Code-Eingabe' — auch /admin/ nicht."""
    response = client.get("/admin/")

    assert response.status_code == 302
    assert response.url.startswith(GATE_URL)


def test_redirect_preserves_the_originally_requested_path(client):
    response = client.get("/colors/wu/")

    assert response.url == f"{GATE_URL}?next=%2Fcolors%2Fwu%2F"


# Freigelistete Pfade bleiben erreichbar -----------------------------------


def test_healthz_is_exempt_from_the_gate(client):
    assert client.get("/healthz").status_code == 200


def test_robots_txt_is_exempt_and_disallows_everything(client):
    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert "Disallow: /" in response.content.decode()


def test_static_files_are_not_redirected_to_the_gate(client):
    response = client.get("/static/js/htmx.min.js")

    assert response.status_code != 302


def test_gate_page_itself_is_reachable_without_a_cookie(client):
    assert client.get(GATE_URL).status_code == 200


# noindex auf jeder Antwort (FR-A4) ----------------------------------------


def test_x_robots_tag_is_set_on_a_passed_through_response(client):
    assert client.get("/healthz").headers["X-Robots-Tag"] == "noindex"


def test_x_robots_tag_is_set_on_a_redirected_response(client):
    response = client.get("/this-path-does-not-exist/")

    assert response.headers["X-Robots-Tag"] == "noindex"


# Code-Eingabe --------------------------------------------------------------


def test_correct_code_sets_a_signed_httponly_cookie_and_redirects(client):
    response = client.post(GATE_URL, {"code": settings.INVITE_CODE, "next": "/healthz"})

    assert response.status_code == 302
    assert response.url == "/healthz"

    cookie = response.cookies[settings.GATE_COOKIE_NAME]
    assert cookie["httponly"]
    # Der Wert ist signiert, kein Klartext-Marker.
    signing.loads(cookie.value, salt=settings.GATE_COOKIE_SALT)


def test_logging_in_from_the_bare_root_path_reaches_color_infos(client):
    """
    Regression: "/" selbst hatte keine eigene Seite (config/urls.py).
    Wer die bloße Startadresse aufruft (kein "next", da noch nichts
    Bestimmtes angefragt wurde), landete nach dem Login wieder auf
    "/" — und bekam dort einen 404 statt der Farbseite.
    """
    response = client.post(GATE_URL, {"code": settings.INVITE_CODE, "next": "/"}, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[-1] == ("/colors/", 302)


def test_incorrect_code_shows_an_error_and_sets_no_cookie(client):
    response = client.post(GATE_URL, {"code": "wrong-code"})

    assert response.status_code == 200
    assert settings.GATE_COOKIE_NAME not in response.cookies
    assert "Incorrect invite code" in response.content.decode()


def test_a_valid_cookie_grants_access_to_a_previously_blocked_path(client):
    client.post(GATE_URL, {"code": settings.INVITE_CODE})

    response = client.get("/this-path-does-not-exist/")

    # 404, nicht mehr 302 zum Gate — der Pfad existiert schlicht nicht.
    assert response.status_code == 404


def test_a_tampered_cookie_is_rejected(client):
    client.cookies[settings.GATE_COOKIE_NAME] = "not-a-valid-signature"

    response = client.get("/admin/")

    assert response.status_code == 302
    assert response.url.startswith(GATE_URL)


def test_next_parameter_rejects_an_external_host_to_prevent_open_redirect(client):
    response = client.post(
        GATE_URL, {"code": settings.INVITE_CODE, "next": "https://evil.example/"}
    )

    assert response.status_code == 302
    assert response.url == "/"


# Rate Limiting ---------------------------------------------------------


def test_rate_limiting_blocks_after_too_many_attempts(client):
    for _ in range(settings.GATE_RATE_LIMIT_MAX_ATTEMPTS):
        client.post(GATE_URL, {"code": "wrong"})

    response = client.post(GATE_URL, {"code": "wrong"})

    assert response.status_code == 429


def test_rate_limiting_records_an_attempt_row_per_post(client):
    client.post(GATE_URL, {"code": "wrong"})

    assert GateAttempt.objects.count() == 1


def test_rate_limiting_does_not_block_get_requests(client):
    for _ in range(settings.GATE_RATE_LIMIT_MAX_ATTEMPTS + 5):
        client.get(GATE_URL)

    assert client.get(GATE_URL).status_code == 200
