"""
Tests für die Inhalte je Selektionsgröße auf der echten Seite
(Task 1.7, PRD §5.2). apps/colors/tests/test_content.py prüft die
Geschäftslogik in `content.py` isoliert; hier geht es um das
Zusammenspiel — landet das auch wirklich im ausgelieferten HTML.
"""

import pytest
from django.urls import reverse

from apps.colors.models import ColorCombination

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("seeded_content")]


# 0 Farben ----------------------------------------------------------------


def test_zero_colors_shows_goal_and_means_at_every_vertex(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    for text in ("peace", "order", "perfection", "knowledge", "harmony", "acceptance"):
        assert f">{text}</text>" in html, text


def test_zero_colors_shows_the_reserved_placeholder_box(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    assert "Select 1" in html
    assert "info-box__title" not in html


def test_zero_colors_labels_ally_edges_and_neutral_enemy_poles(gated_client):
    html = gated_client.get(reverse("colors:index")).content.decode()

    for text in ("Design", "Community", "Progress", "Independence", "Authenticity"):
        assert f">{text}</text>" in html, text
    # Neutrale Sicht (from_color="") — nicht die eigene Sicht einer
    # Farbe wie "Good"/"Evil", die erst bei 1 selektierten Farbe zeigt.
    for term in ("Group", "Individual", "Structure", "Flexibility"):
        assert f">{term}</text>" in html, term


# 1 Farbe -------------------------------------------------------------------


def test_one_color_box_shows_allies_and_enemies_not_archetypes(gated_client):
    html = gated_client.get("/colors/w/").content.decode()

    assert "Allies" in html
    assert "Enemies" in html
    assert "Green" in html and "Blue" in html
    assert "Black" in html and "Red" in html
    # D-42: die "Archetypen der vier Zweierkombinationen" aus dem
    # ursprünglichen PRD-Entwurf sind bewusst durch die Allies/Enemies-
    # Liste ersetzt — kein Archetyp-Text mehr auf dieser Seite.
    assert "Architect" not in html


def test_one_color_trait_row_has_three_columns(gated_client):
    html = gated_client.get("/colors/w/").content.decode()

    assert "← Green" in html
    assert "Blue →" in html
    assert ">Center<" in html
    assert "Sense of Duty" in html
    assert "Systematic Planning" in html
    assert "Devotion to Community" in html


def test_one_color_trait_type_is_not_color_only(gated_client):
    """NFR-6: Strength/Weakness/Neutral über Text, nicht nur Farbe."""
    html = gated_client.get("/colors/w/").content.decode()

    assert "Strength" in html
    assert "Weakness" in html
    assert "Neutral" in html
    assert "trait-chip--strength" in html
    assert "trait-chip--weakness" in html
    assert "trait-chip--neutral" in html


def test_white_halo_uses_the_override_not_its_own_pale_hex(gated_client):
    html = gated_client.get("/colors/w/").content.decode()

    assert "--halo: #F4C430;" in html
    assert "--halo: #F8F6D8;" not in html


# 2 Farben, Ally --------------------------------------------------------


def test_ally_pair_box_shows_common_enemy_and_conflict(gated_client):
    html = gated_client.get("/colors/wu/").content.decode()

    assert "Azorius" in html
    assert "The Architect" in html
    assert "Common enemy" in html
    assert "Red" in html
    assert "Neighbour ally conflict" in html
    assert "Take it vs Leave it" in html
    assert "Ally" in html


def test_ally_pair_trait_row_is_a_single_box(gated_client):
    html = gated_client.get("/colors/wu/").content.decode()

    assert "Design Mindset" in html
    assert "trait-row--single" in html
    assert "← " not in html  # keine Links/Rechts-Spalten bei einem Paar


def test_ally_pair_theme_appears_on_all_three_visible_edges(gated_client):
    html = gated_client.get("/colors/wu/").content.decode()

    for text in ("Design", "Community", "Progress"):
        assert f">{text}</text>" in html, text


# 2 Farben, Enemy -------------------------------------------------------


def test_enemy_pair_box_shows_relation_archetype_and_all_perspectives(gated_client):
    html = gated_client.get("/colors/wb/").content.decode()

    assert "Enemy" in html
    assert "Orzhov" in html
    assert "The Insider" in html
    assert "defected on everyone else" in html  # White's Sicht
    assert "coercing" in html  # Black's Sicht
    assert "owed the sacrifice" in html  # neutrale Sicht
    assert "trait-box" not in html  # keine Eigenschaften bei Enemy


def test_enemy_pair_theme_labels_its_own_diagonal(gated_client):
    html = gated_client.get("/colors/wb/").content.decode()

    assert ">Tribalism</text>" in html


# 3-5 Farben --------------------------------------------------------------


def test_larger_combination_shows_only_its_name(gated_client):
    html = gated_client.get("/colors/wub/").content.decode()

    assert "Esper" in html
    assert "trait-box" not in html
    assert "Common enemy" not in html


def test_a_combination_without_content_renders_200_not_an_error(gated_client):
    """Roadmap 1.7: 'eine 3er-Kombination ohne Content rendert fehlerfrei'."""
    ColorCombination.objects.filter(code="WUB", locale="en").update(name="")

    response = gated_client.get("/colors/wub/")

    assert response.status_code == 200
    assert "info-box__title" not in response.content.decode()
