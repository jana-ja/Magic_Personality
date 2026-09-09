"""
Tests für das eigenständige mobile Layout (Task 1.10, NFR-3, D-14).

Was pytest direkt prüfen kann: dass Eigenschaften strukturell nie
innerhalb der Fünfeck-SVG liegen (gilt unabhängig vom Viewport — das
Fünfeck rendert für jede Bildschirmgröße dieselbe Markup-Struktur,
nur CSS ordnet sie anders an) und dass die Stapel-Regeln für schmale
Bildschirme tatsächlich im Stylesheet stehen.

Das eigentliche Rendering bei 375px — kein horizontales Scrollen,
ausreichend große Trefferflächen — ist Sache des Browsers und im
echten Browser verifiziert (wie schon bei den Tasks 1.7 bis 1.9):

- 0 Farben, eine Einzelfarbe, ein Ally-Paar, ein Enemy-Paar (mit allen
  drei Perspektiven), eine Dreier- und die Fünffarbkombination liefern
  bei 375px Viewportbreite alle `document.documentElement.scrollWidth
  === window.innerWidth === 375` — kein horizontales Scrollen in
  keinem Selektionszustand.
- Die Fünfeck-Ecken selbst messen bei 375px zwischen ~77 und 116px
  Kantenlänge (Symbol + Name), weit über der gängigen 44px-Empfehlung
  für Trefferflächen. Der sichtbare Mana-Kreis ist mit ~39px kleiner,
  aber der (bei fehlender Selektion unsichtbare, `opacity: 0`, aber
  nicht `pointer-events: none` gesetzte) Halo-Kreis dahinter deckt
  bereits ~77px ab — per `elementFromPoint` und einem echten Klick am
  Rand dieses Kreises bestätigt, außerhalb des sichtbaren Symbols.
"""

import re

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("seeded_content")]


def test_properties_are_never_rendered_inside_the_pentagon_svg(gated_client):
    """
    NFR-3: "Eigenschaften werden mobil nicht am Fünfeck verortet." Gilt
    strukturell für jede Bildschirmgröße — Eigenschaften liegen immer
    in der separaten Trait-Row unterhalb, nie im SVG selbst; CSS
    ordnet für schmale Bildschirme nur die Reihenfolge der Blöcke neu.
    """
    html = gated_client.get(reverse("colors:combination", kwargs={"code": "w"})).content.decode()

    svg_start = html.index("<svg")
    svg_end = html.index("</svg>") + len("</svg>")
    svg_markup = html[svg_start:svg_end]

    assert "trait-chip" not in svg_markup
    assert "trait-box" not in svg_markup

    # Die Trait-Row muss existieren — und zwar erst nach dem SVG.
    trait_row_start = html.index('class="trait-row')
    assert trait_row_start > svg_end


@pytest.mark.parametrize("code", ["", "w", "wu", "wb", "wub", "wubrg"])
def test_properties_stay_outside_the_svg_across_every_selection_size(gated_client, code):
    """Dieselbe Prüfung wie oben, über alle in PRD §5.2 unterschiedenen Fälle hinweg."""
    url = reverse("colors:combination", kwargs={"code": code}) if code else reverse("colors:index")
    html = gated_client.get(url).content.decode()

    svg_markup = html[html.index("<svg") : html.index("</svg>")]
    assert "trait-chip" not in svg_markup
    assert "trait-box" not in svg_markup


def test_base_css_stacks_pentagon_and_info_box_below_the_mobile_breakpoint():
    """
    NFR-3: "Fünfeck oben, alle Informationen als zusammenhängender
    Block darunter." Die Dokumentreihenfolge legt "Fünfeck oben" schon
    fest (templates/colors/index.html); diese Regel macht daraus per
    flex-direction: column auch das gestapelte, eigenständige
    Mobil-Layout statt einer nur verkleinerten Nebeneinander-Ansicht.
    """
    css = (settings.BASE_DIR / "static" / "css" / "base.css").read_text(encoding="utf-8")

    # .color-layout muss die *erste* Regel innerhalb ihres eigenen
    # Mobil-Media-Blocks sein — base.css hat mehrere solcher Blöcke
    # (einen je Komponente), ein bloßes "kommt irgendwann danach"
    # würde auch von einem ganz anderen Block aus erfüllt.
    assert re.search(
        r"@media \(max-width: 47\.9375rem\)\s*\{\s*\.color-layout\s*\{"
        r"[^}]*flex-direction:\s*column",
        css,
    )


def test_base_css_stacks_the_trait_row_below_the_mobile_breakpoint():
    css = (settings.BASE_DIR / "static" / "css" / "base.css").read_text(encoding="utf-8")

    assert re.search(
        r"@media \(max-width: 47\.9375rem\)\s*\{\s*\.trait-row\s*\{[^}]*flex-direction:\s*column",
        css,
    )
