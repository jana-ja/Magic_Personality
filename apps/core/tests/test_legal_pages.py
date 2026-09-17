"""
Tests für About- und Datenschutzseite (Task 1.11, PRD §9).
"""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("url_name", ["about", "privacy"])
def test_page_is_behind_the_gate(client, url_name):
    """FR-A1 kennt keine Ausnahme — auch nicht für About/Privacy."""
    response = client.get(reverse(url_name))

    assert response.status_code == 302
    assert reverse("gate") in response["Location"]


@pytest.mark.parametrize("url_name", ["about", "privacy"])
def test_page_renders(gated_client, url_name):
    response = gated_client.get(reverse(url_name))

    assert response.status_code == 200


def test_about_page_has_a_contact_email(gated_client):
    html = gated_client.get(reverse("about")).content.decode()

    assert 'href="mailto:janajansen.dev@gmail.com"' in html


def test_privacy_page_covers_what_where_how_long_and_deletion(gated_client):
    """
    Task 2.14, PRD §9: "Kurze Datenschutzseite (welche Daten, wo, wie
    lange, wie löschbar)". The placeholder from Task 1.11 is replaced
    with real content now that accounts/profiles/test history exist.
    """
    html = gated_client.get(reverse("privacy")).content.decode()

    assert "placeholder" not in html
    # welche Daten
    assert "Argon2" in html
    assert "Test history" in html
    # wo
    assert "STRATO" in html
    # wie lange
    assert "14 days" in html
    # wie löschbar
    assert "Delete your entire account" in html
