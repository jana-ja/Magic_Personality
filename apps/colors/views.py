"""Views der Colors-App: das Fünfeck (Task 1.5, 1.6, 1.7)."""

from dataclasses import dataclass

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from . import content, pentagon, selection
from .models import Color


def index(request, code=""):
    """
    Das Fünfeck mit der durch `code` beschriebenen Auswahl (Task 1.6,
    FR-C4 bis FR-C7) und den dazu passenden Inhalten (Task 1.7,
    PRD §5.2).

    `code == ""` ist die leere Auswahl unter `/colors/` — ein eigenes
    URL-Pattern, weil `<str:code>` mindestens ein Zeichen verlangt und
    "leer" ohnehin ein eigener, nicht umleitbarer Zustand ist (kein
    "kanonischer" Code, den man daraus ableiten könnte).
    """
    if code:
        selected_colors = selection.parse_url_code(code)
        if selected_colors is None:
            raise Http404("Not a valid color combination.")

        canonical = selection.canonical_url_code(selected_colors)
        if code != canonical:
            # Falsche Reihenfolge und/oder Groß-/Kleinschreibung
            # (Roadmap 1.6: "/colors/uw/" -> "/colors/wu/").
            return redirect(_url_for(canonical), permanent=True)
    else:
        selected_colors = set()

    return render(request, "colors/index.html", pentagon_context(selected_colors))


def _url_for(url_code):
    """Die URL für eine (bereits kanonische) Auswahl-URL-Form."""
    if not url_code:
        return reverse("colors:index")
    return reverse("colors:combination", kwargs={"code": url_code})


@dataclass(frozen=True)
class VertexLink:
    """
    Eine Fünfeck-Ecke plus das, was Task 1.6/1.7 dazu brauchen: wohin
    ein Klick führt (Toggle dieser Farbe, FR-C4), ob sie aktuell
    ausgewählt ist (FR-C6) und ihre fertigen Textzeilen (Name, plus
    Ziel/Mittel bei 0 Farben — `pentagon.Vertex.label_lines()`).
    Eigene Klasse statt eines zweiten Dicts, weil Django-Templates
    keinen Attributzugriff mit einem Variablen-Schlüssel können
    (`dict.varname` sucht den *Namen* "varname", nicht dessen Wert) —
    jede Ecke trägt ihre Verlinkung und ihre Zeilen deshalb direkt
    bei sich.
    """

    vertex: pentagon.Vertex
    toggle_url: str
    is_selected: bool
    #: [(Text, Schriftgröße, y)], siehe pentagon.Vertex.label_lines().
    label_lines: list


def pentagon_context(selected_colors=frozenset()):
    """
    Kontext für den Fünfeck-Baustein samt Info-Box (Task 1.5 bis 1.7).
    Eigene Funktion (statt direkt in `index()`), damit spätere Views
    sie übernehmen können, ohne Geometrie, Auswahl-Verlinkung oder
    Inhalte erneut aufzubauen.
    """
    selected_colors = set(selected_colors)
    selection_content = content.selection_content(selected_colors)

    vertices = pentagon.vertices(Color.objects.all())
    vertices_by_code = {vertex.code: vertex for vertex in vertices}
    vertex_links = [
        VertexLink(
            vertex=vertex,
            toggle_url=_url_for(
                selection.canonical_url_code(selection.toggled(selected_colors, vertex.code))
            ),
            is_selected=vertex.code in selected_colors,
            label_lines=vertex.label_lines(selection_content["vertex_extra"].get(vertex.code, ())),
        )
        for vertex in vertices
    ]
    theme_labels = pentagon.theme_labels(selection_content["theme_labels"], vertices_by_code)
    pole_labels = pentagon.pole_labels(selection_content["pole_labels"], vertices_by_code)

    return {
        "vertex_links": vertex_links,
        "outline_points": pentagon.outline_points(vertices),
        "star_points": pentagon.star_points(vertices),
        "view_box": pentagon.view_box(
            vertices, selection_content["vertex_extra"], theme_labels, pole_labels
        ),
        "theme_labels": theme_labels,
        "pole_labels": pole_labels,
        # Ob überhaupt eine Farbe gewählt ist. Bei 0 Farben ist keine
        # Ecke "zurückgenommen" (FR-C6 trifft dann auf nichts zu, siehe
        # PRD §5.2) — die Info-Box selbst ist unabhängig davon immer da
        # (Task 1.7: reservierter Bereich, verhindert Layout-Sprünge
        # beim Umschalten der ersten Farbe).
        "has_selection": bool(selected_colors),
        "reset_url": reverse("colors:index"),
        "box": selection_content["box"],
        "trait_groups": selection_content["trait_groups"],
    }
