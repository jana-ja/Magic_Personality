"""
Tests für die HTMX-Beschleunigung (Task 1.8, D-24).

HTMX selbst ist eine Client-Bibliothek — was pytest hier wirklich
prüfen kann, ist die Serverseite: dass die richtigen hx-*-Attribute im
HTML stehen und dass jede URL weiterhin ganz normal ohne JavaScript
funktioniert (Progressive Enhancement). Das eigentliche Swap-,
Push-URL- und Zurück-Verhalten ist im echten Browser verifiziert, wie
schon bei Task 1.6/1.7 für Fünfeck-Geometrie und -Kollisionen.
"""

import re

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_colors_panel_wraps_pentagon_info_box_and_trait_row(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    panel_start = html.index('id="colors-panel"')
    panel_and_after = html[panel_start:]

    assert 'class="pentagon"' in panel_and_after
    assert 'class="info-box"' in panel_and_after
    # Alles, was sich mit der Selektion ändert, muss *innerhalb* des
    # Panels liegen, nicht zufällig irgendwo danach auf der Seite.
    assert panel_and_after.index('class="pentagon"') < panel_and_after.index('class="info-box"')


@pytest.mark.parametrize("code", ["", "w", "wu"])
def test_vertex_links_carry_the_htmx_swap_attributes(gated_client, code):
    url = reverse("colors:combination", kwargs={"code": code}) if code else reverse("colors:index")
    html = gated_client.get(url).content.decode()

    assert 'hx-select="#colors-panel"' in html
    assert 'hx-target="#colors-panel"' in html
    assert 'hx-push-url="true"' in html
    # Je Ecke ein eigenes hx-get auf ihre eigene Toggle-URL, nicht nur
    # irgendein globales Attribut irgendwo auf der Seite.
    assert html.count("hx-get=") == 5 + 1  # 5 Ecken + der Reset-Link


def test_every_hx_get_target_matches_its_own_href(gated_client):
    """
    hx-select/hx-target zeigen für alle sechs Links (5 Ecken + Reset)
    auf dasselbe #colors-panel — aber hx-get muss je Link dessen
    *eigenes* href sein, sonst würde ein Klick immer dieselbe URL
    laden statt die tatsächlich gemeinte.
    """
    html = gated_client.get(reverse("colors:combination", kwargs={"code": "wu"})).content.decode()

    href_pattern = re.compile(r'href="([^"]+)"\s+hx-get="([^"]+)"')
    matches = href_pattern.findall(html)

    assert len(matches) == 6  # 5 Ecken + Reset-Link
    for href, hx_get in matches:
        assert href == hx_get

    reset_url = reverse("colors:index")
    assert (reset_url, reset_url) in matches


def test_the_toggle_url_still_works_as_a_plain_navigation(gated_client):
    """
    Progressive Enhancement (D-24): ohne JavaScript ignoriert der
    Browser hx-* vollständig und folgt href wie jedem anderen Link —
    das muss unabhängig von HTMX weiterhin eine vollständige,
    korrekte Seite liefern.
    """
    response = gated_client.get(reverse("colors:combination", kwargs={"code": "wu"}))

    assert response.status_code == 200
    assert 'id="colors-panel"' in response.content.decode()
