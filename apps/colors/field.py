"""
Farbwahl als Formularfeld: Kontext für `colors/_color_field.html`
(Task 4.6, FR-P13, D-74; seit Task 5.3 hier statt in `apps.social`, weil auch
der Beitragseditor es benutzt und `posts` nicht von `social` abhängen soll,
D-78).
"""

from dataclasses import dataclass

from . import pentagon
from .models import Color


@dataclass(frozen=True)
class FieldVertex:
    """Eine Ecke des Fünfecks als Formularfeld (Task 4.6): die Geometrie aus
    `apps.colors.pentagon` plus, ob die Farbe gerade angekreuzt ist."""

    vertex: pentagon.Vertex
    is_selected: bool


def color_field_context(selected_codes):
    """
    Kontext für `colors/_color_field.html`: dieselbe Geometrie wie das
    Fünfeck in den Color Infos und in der Farbsuche (`pentagon.vertices()`,
    `outline_points()`, `star_points()`, `view_box()`, D-27/D-66) — hier
    ohne Linienbeschriftungen und ohne Links, die Ecken sind Kästchen.
    """
    vertices = pentagon.vertices(Color.objects.all())
    return {
        "field_vertices": [
            FieldVertex(vertex=vertex, is_selected=vertex.code in selected_codes)
            for vertex in vertices
        ],
        "field_outline_points": pentagon.outline_points(vertices),
        "field_star_points": pentagon.star_points(vertices),
        "field_view_box": pentagon.view_box(vertices),
        "field_name_size": pentagon.NAME_SIZE,
        "field_has_selection": bool(selected_codes),
    }
