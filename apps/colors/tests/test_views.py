"""
Tests für die Fünfeck-Seite: die Figur selbst (Task 1.5, FR-C1 bis
FR-C3) und ihre Selektion über /colors/<code>/ (Task 1.6, FR-C4 bis
FR-C7). Die reine Auswahl-Logik (Parsing, Kanonisierung, Toggle) ist
separat in test_selection.py getestet — hier geht es um das
Zusammenspiel: Status Codes, Redirects, was tatsächlich im HTML landet.
"""

import itertools
import re

import pytest
from django.urls import reverse

from apps.colors.models import Color
from apps.colors.utils import CANONICAL_ORDER

pytestmark = pytest.mark.django_db

ALL_URL_CODES = [
    "".join(combo).lower()
    for size in range(1, 6)
    for combo in itertools.combinations(CANONICAL_ORDER, size)
]


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


# Task 1.6 · Selektion und Routing -------------------------------------


@pytest.mark.parametrize("code", ALL_URL_CODES)
def test_every_one_of_the_31_codes_returns_200(gated_client, code):
    """Roadmap 1.6: "Test: alle 31 Codes liefern Status 200"."""
    response = gated_client.get(f"/colors/{code}/")

    assert response.status_code == 200


def test_a_non_canonically_ordered_code_redirects_permanently(gated_client):
    """Roadmap 1.6: "/colors/uw/" -> "/colors/wu/", dauerhaft (301)."""
    response = gated_client.get("/colors/uw/")

    assert response.status_code == 301
    assert response["Location"] == "/colors/wu/"


def test_an_uppercase_code_redirects_to_the_lowercase_form(gated_client):
    response = gated_client.get("/colors/WU/")

    assert response.status_code == 301
    assert response["Location"] == "/colors/wu/"


def test_redirects_are_followed_to_a_200(gated_client):
    response = gated_client.get("/colors/uw/", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [("/colors/wu/", 301)]


@pytest.mark.parametrize("code", ["x", "wx", "ww", "wubrgw", "0", "wu-b"])
def test_an_invalid_code_returns_404(gated_client, code):
    """Roadmap 1.6: "Ungültige Codes ergeben 404" — falsche Buchstaben,
    doppelte Buchstaben, zu viele Zeichen oder Zeichen außerhalb WUBRG."""
    response = gated_client.get(f"/colors/{code}/")

    assert response.status_code == 404


def test_a_selected_color_is_highlighted_and_others_are_receded(gated_client):
    html = gated_client.get("/colors/w/").content.decode()

    assert 'data-color="W"' in html
    # Grobe, aber robuste Prüfung: der Link-Block der selektierten
    # Farbe trägt die --selected-Klasse, die der übrigen die
    # --unselected-Klasse. Exakte Reihenfolge der Attribute ist dabei
    # egal, deshalb wird im HTML-String gesucht statt geparst.
    assert "pentagon__vertex--selected" in html
    assert "pentagon__vertex--unselected" in html
    assert 'data-color="U"' in html


def test_no_color_is_marked_as_unselected_when_nothing_is_selected(gated_client):
    """
    FR-C6 unterscheidet "hervorgehoben" von "zurückgenommen" — bei
    0 Farben ist beides bedeutungslos (PRD §5.2: alle fünf werden
    gleich gezeigt).
    """
    html = gated_client.get(reverse("colors:index")).content.decode()

    assert "pentagon__vertex--selected" not in html
    assert "pentagon__vertex--unselected" not in html


def _vertex_links(html):
    """{code: href} für jede Fünfeck-Ecke, unabhängig von Attributreihenfolge/-umbruch."""
    return {
        match.group("code"): match.group("href")
        for match in re.finditer(r'data-color="(?P<code>[A-Z])"\s+href="(?P<href>[^"]*)"', html)
    }


def test_toggling_the_only_selected_color_links_back_to_the_index(gated_client):
    html = gated_client.get("/colors/w/").content.decode()

    # Der Link auf der weißen Ecke selbst schaltet Weiß wieder ab.
    assert _vertex_links(html)["W"] == "/colors/"


def test_toggling_an_unselected_color_adds_it_to_the_selection(gated_client):
    html = gated_client.get("/colors/w/").content.decode()

    assert _vertex_links(html)["U"] == "/colors/wu/"


def test_the_reset_link_leads_to_the_index(gated_client):
    html = gated_client.get("/colors/wu/").content.decode()

    assert f'href="{reverse("colors:index")}">Reset selection</a>' in html


def test_no_reset_link_when_nothing_is_selected(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    assert "pentagon-controls" not in html


def test_svg_coordinates_stay_machine_readable_under_a_non_english_locale(gated_client):
    """
    Regression: Django formatiert rohe Float-Werte im Template nach
    der aktiven Sprache — unter Deutsch wird "23.336" zu "23,336" und
    macht damit jedes numerische SVG-Attribut ungültig (das Fünfeck
    zeichnet sich falsch, ohne dass irgendein Fehler auftritt). Nicht
    theoretisch: Task 1.3/D-15 macht Deutsch real erreichbar, sobald
    eine zweite Seed-Datei existiert. `{% localize off %}` in
    _pentagon.html schützt genau davor.
    """
    gated_client.cookies["django_language"] = "de"
    html = gated_client.get(reverse("colors:index")).content.decode()

    assert re.search(r'[xy]="[^"]*,[^"]*"', html) is None
    assert 'viewBox="-70' in html
