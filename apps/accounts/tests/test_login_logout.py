"""
Tests für Login und Logout (Task 2.2, FR-U4 bis FR-U7).
"""

import pytest
from django.conf import settings

from apps.accounts.models import Profile, User

pytestmark = pytest.mark.django_db

LOGIN_URL = "/accounts/login/"
LOGOUT_URL = "/accounts/logout/"


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


def test_login_page_is_reachable(gated_client):
    assert gated_client.get(LOGIN_URL).status_code == 200


def test_correct_credentials_log_the_user_in(gated_client, user):
    response = gated_client.post(
        LOGIN_URL,
        {"username": "alex@example.com", "password": "a-long-enough-password"},
        follow=True,
    )

    assert response.wsgi_request.user == user


def test_wrong_password_does_not_log_in(gated_client, user):
    response = gated_client.post(
        LOGIN_URL, {"username": "alex@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 200
    assert not response.wsgi_request.user.is_authenticated


def test_logout_ends_the_session(gated_client, user):
    gated_client.force_login(user)
    assert gated_client.get("/colors/").wsgi_request.user.is_authenticated

    gated_client.post(LOGOUT_URL)

    response = gated_client.get("/colors/")
    assert not response.wsgi_request.user.is_authenticated


def test_logout_rejects_get_requests(gated_client):
    """Djangos LogoutView ist seit Django 5 POST-only (CSRF-Schutz)."""
    response = gated_client.get(LOGOUT_URL)

    assert response.status_code == 405


# Rate Limiting über django-axes (FR-U6, ARCHITECTURE.md §7) -------------


def test_login_locks_out_after_the_axes_failure_limit(gated_client, user):
    for _ in range(settings.AXES_FAILURE_LIMIT):
        gated_client.post(LOGIN_URL, {"username": "alex@example.com", "password": "wrong-password"})

    response = gated_client.post(
        LOGIN_URL, {"username": "alex@example.com", "password": "a-long-enough-password"}
    )

    assert response.status_code == 429
    assert not response.wsgi_request.user.is_authenticated
