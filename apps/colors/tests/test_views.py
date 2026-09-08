"""
Tests für die Fünfeck-Seite (Task 1.5, FR-C1 bis FR-C3).

Auswahl und Routing über /colors/<code>/ kommen mit Task 1.6; hier
geht es nur darum, dass die Figur überhaupt vollständig ausgeliefert
wird.
"""

import pytest
from django.urls import reverse

from apps.colors.models import Color

pytestmark = pytest.mark.django_db


def test_the_pentagon_page_is_behind_the_gate(client):
    """FR-A1 kennt keine Ausnahme — auch nicht für die Farbseite."""
    response = client.get(reverse("colors:index"))

    assert response.status_code == 302
    assert reverse("gate") in response["Location"]


def test_the_pentagon_page_renders(gated_client):
    response = gated_client.get(reverse("colors:index"))

    assert response.status_code == 200


def test_all_five_colors_appear_with_name_and_symbol(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    for color in Color.objects.all():
        assert f">{color.name}</text>" in html, color.name
        # Über {% static %} aufgelöst, nicht als roher Feldwert.
        assert f'href="/static/{color.symbol}"' in html, color.symbol


def test_the_figure_carries_both_the_outline_and_the_star(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    assert 'class="pentagon__outline"' in html
    assert 'class="pentagon__star"' in html


def test_the_svg_has_an_accessible_name(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    assert 'aria-labelledby="pentagon-title"' in html
    assert '<title id="pentagon-title">' in html


def test_no_template_comment_leaks_into_the_output(gated_client):
    """
    Django kennt `{# … #}` nur einzeilig; ein mehrzeiliger Kommentar
    landet sonst wörtlich im HTML. Genau das war beim ersten Entwurf
    dieses Templates der Fall.
    """
    html = gated_client.get(reverse("colors:index")).content.decode()

    assert "{#" not in html
    assert "Task 1.5" not in html


def test_the_footer_carries_the_fan_content_notice(gated_client):
    """PRD §9, D-12 — Bedingung für die Nutzung der Mana-Symbole."""
    html = gated_client.get(reverse("colors:index")).content.decode()

    assert "Fan Content Policy" in html
    assert "Wizards of the Coast" in html
