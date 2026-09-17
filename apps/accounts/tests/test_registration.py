"""
Tests für die Registrierung (Task 2.2, FR-U1 bis FR-U3, FR-U6).

Nutzt `gated_client` (siehe `conftest.py`): Registrierung liegt wie
jede andere Seite hinter der Zugangssperre aus Task 0.5 (FR-U1).
"""

import pytest
from django.conf import settings

from apps.accounts.models import Profile, User
from apps.core.models import RegistrationAttempt

pytestmark = pytest.mark.django_db

REGISTER_URL = "/accounts/register/"

VALID_DATA = {
    "email": "alex@example.com",
    "nickname": "alex",
    "password1": "a-long-enough-password",
    "password2": "a-long-enough-password",
}


def test_register_page_is_reachable(gated_client):
    assert gated_client.get(REGISTER_URL).status_code == 200


def test_registration_without_the_gate_cookie_redirects_to_the_gate(client):
    """FR-U1: Voraussetzung ist der Invite-Code — hier über die schon
    bestehende Zugangssperre, keine eigene Prüfung in der View."""
    response = client.get(REGISTER_URL)

    assert response.status_code == 302
    assert response.url.startswith("/gate/")


def test_valid_registration_creates_a_user_and_a_profile_together(gated_client):
    gated_client.post(REGISTER_URL, VALID_DATA)

    user = User.objects.get(email="alex@example.com")
    profile = Profile.objects.get(nickname="alex")
    assert profile.user == user


def test_valid_registration_logs_the_user_in(gated_client):
    response = gated_client.post(REGISTER_URL, VALID_DATA, follow=True)

    assert response.wsgi_request.user.is_authenticated
    assert response.wsgi_request.user.email == "alex@example.com"


def test_registration_rejects_a_password_shorter_than_ten_characters(gated_client):
    data = {**VALID_DATA, "password1": "short1234", "password2": "short1234"}

    response = gated_client.post(REGISTER_URL, data)

    assert response.status_code == 200
    assert not User.objects.filter(email="alex@example.com").exists()


def test_registration_rejects_mismatched_passwords(gated_client):
    data = {**VALID_DATA, "password2": "a-different-password"}

    response = gated_client.post(REGISTER_URL, data)

    assert response.status_code == 200
    assert not User.objects.filter(email="alex@example.com").exists()


def test_registration_rejects_a_duplicate_email(gated_client):
    User.objects.create_user(email="alex@example.com", password="an-existing-password")

    response = gated_client.post(REGISTER_URL, VALID_DATA)

    assert response.status_code == 200
    assert User.objects.filter(email="alex@example.com").count() == 1


def test_registration_rejects_a_duplicate_nickname_case_insensitively(gated_client):
    Profile.objects.create(nickname="Alex")

    response = gated_client.post(REGISTER_URL, VALID_DATA)

    assert response.status_code == 200
    assert not User.objects.filter(email="alex@example.com").exists()


# Rate Limiting (FR-U6) -------------------------------------------------


def test_registration_is_rate_limited(gated_client):
    for _ in range(settings.REGISTRATION_RATE_LIMIT_MAX_ATTEMPTS):
        gated_client.post(REGISTER_URL, {**VALID_DATA, "email": "someone-else@example.com"})

    response = gated_client.post(REGISTER_URL, {**VALID_DATA, "email": "yet-another@example.com"})

    assert response.status_code == 429


def test_registration_records_an_attempt_row_per_post(gated_client):
    gated_client.post(REGISTER_URL, VALID_DATA)

    assert RegistrationAttempt.objects.count() == 1
