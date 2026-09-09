"""
Tests für Tastatur und Barrierefreiheit (Task 1.9, FR-C5, FR-C8,
NFR-5, NFR-6).

Was pytest direkt prüfen kann: die serverseitig gerenderten Bausteine
— role/aria-pressed auf jeder Ecke, die Live-Region-Auszeichnung, dass
main.js eingebunden ist und seine Kernfunktionen enthält. Tastendrücke,
Fokusreihenfolge und tatsächliche Live-Region-Ansagen sind Verhalten
einer Client-Bibliothek und im echten Browser verifiziert (wie schon
bei Task 1.8) — siehe die Verifikation im Commit zu diesem Task.
"""

import re

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_every_vertex_has_role_button_and_aria_pressed(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    # Bei 0 Farben ist aria-pressed="false" für alle fünf (FR-C6 greift
    # erst, wenn überhaupt etwas selektiert ist — die ARIA-Semantik
    # gilt aber unabhängig davon immer).
    assert html.count('role="button"') == 6  # 5 Ecken + Reset-Link
    assert html.count('aria-pressed="false"') == 5


def test_aria_pressed_reflects_the_actual_selection(gated_client):
    html = gated_client.get(reverse("colors:combination", kwargs={"code": "w"})).content.decode()

    vertex_pattern = re.compile(r'data-color="([^"]+)"[^>]*aria-pressed="([^"]+)"')
    pressed_by_color = dict(vertex_pattern.findall(html))

    assert pressed_by_color == {"W": "true", "U": "false", "B": "false", "R": "false", "G": "false"}


def test_the_reset_link_has_a_stable_id_and_role_button(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    assert re.search(r'<a id="reset-selection"[^>]*role="button"', html)


def test_the_live_region_exists_outside_the_swapped_panel(gated_client):
    """
    NFR-5: Änderungen werden über eine Live-Region angesagt. Sie muss
    *vor* #colors-panel im HTML stehen (also außerhalb davon), sonst
    würde sie bei jedem HTMX-Swap durch eine neue, leere Instanz
    ersetzt statt bestehen zu bleiben.
    """
    html = gated_client.get(reverse("colors:index")).content.decode()

    live_region_start = html.index('id="colors-live-region"')
    panel_start = html.index('id="colors-panel"')

    assert live_region_start < panel_start
    live_region_tag = html[live_region_start : html.index(">", live_region_start)]
    assert 'aria-live="polite"' in live_region_tag
    assert "visually-hidden" in live_region_tag
    assert 'data-empty-text="No colors selected.' in live_region_tag


def test_base_template_includes_main_js_with_keyboard_and_live_region_logic(rf):
    """
    Reine Präsenzprüfung analog zu apps/core/tests/test_templates.py —
    das eigentliche Tastatur-/Ansageverhalten ist im echten Browser
    verifiziert.
    """
    main_js = (settings.BASE_DIR / "static" / "js" / "main.js").read_text(encoding="utf-8")

    assert "WUBRG" in main_js
    assert '"Escape"' in main_js
    assert "htmx:afterSwap" in main_js
    assert "aria-pressed" in main_js


def test_own_javascript_stays_within_the_roadmap_budget():
    """Roadmap 1.9: 'Eigenes JavaScript bleibt unter etwa 150 Zeilen'."""
    main_js_path = settings.BASE_DIR / "static" / "js" / "main.js"
    line_count = len(main_js_path.read_text(encoding="utf-8").splitlines())

    assert line_count < 150
