"""
Tests für die Passwortänderung (Task 2.2, FR-U5).

Der wichtigste Fall ist wörtlich aus der Definition of Done in
docs/ROADMAP.md: nach einer Passwortänderung ist eine zweite,
bestehende Session ungültig. Djangos eigener Session-Auth-Hash-
Mechanismus erledigt das automatisch (ARCHITECTURE.md §7) — dieser
Test belegt nur, dass die Standardeinstellung tatsächlich greift.
"""

import pytest
from django.conf import settings
from django.test import Client

from apps.accounts.models import Profile, User
from apps.core import gate

pytestmark = pytest.mark.django_db

PASSWORD_CHANGE_URL = "/accounts/password/change/"

OLD_PASSWORD = "the-original-password"
NEW_PASSWORD = "a-brand-new-password"


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password=OLD_PASSWORD)
    Profile.objects.create(user=user, nickname="alex")
    return user


def _gated_client():
    client = Client()
    client.cookies[settings.GATE_COOKIE_NAME] = gate.sign_gate_cookie()
    return client


def test_password_change_requires_login(gated_client):
    response = gated_client.get(PASSWORD_CHANGE_URL)

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


def test_changing_the_password_invalidates_a_second_session(user):
    session_a = _gated_client()
    session_b = _gated_client()
    session_a.force_login(user)
    session_b.force_login(user)

    session_a.post(
        PASSWORD_CHANGE_URL,
        {
            "old_password": OLD_PASSWORD,
            "new_password1": NEW_PASSWORD,
            "new_password2": NEW_PASSWORD,
        },
    )

    response = session_b.get(PASSWORD_CHANGE_URL)
    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


def test_changing_the_password_keeps_the_current_session_valid(user):
    session_a = _gated_client()
    session_a.force_login(user)

    session_a.post(
        PASSWORD_CHANGE_URL,
        {
            "old_password": OLD_PASSWORD,
            "new_password1": NEW_PASSWORD,
            "new_password2": NEW_PASSWORD,
        },
    )

    response = session_a.get(PASSWORD_CHANGE_URL)
    assert response.status_code == 200


def test_the_new_password_can_be_used_to_log_in_again(user):
    session_a = _gated_client()
    session_a.force_login(user)
    session_a.post(
        PASSWORD_CHANGE_URL,
        {
            "old_password": OLD_PASSWORD,
            "new_password1": NEW_PASSWORD,
            "new_password2": NEW_PASSWORD,
        },
    )

    fresh_client = _gated_client()
    response = fresh_client.post(
        "/accounts/login/", {"username": "alex@example.com", "password": NEW_PASSWORD}, follow=True
    )

    assert response.wsgi_request.user == user
