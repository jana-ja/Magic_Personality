"""Views der Colors-App: das Fünfeck (Task 1.5, FR-C1 bis FR-C3)."""

from django.shortcuts import render

from . import pentagon
from .models import Color


def index(request):
    """
    Das Fünfeck ohne Selektion.

    Task 1.5 zeichnet nur die Figur; Auswahl und Routing über
    /colors/<code>/ kommen mit Task 1.6, die Inhalte je
    Selektionsgröße mit Task 1.7. Das Fünfeck bleibt dabei in jedem
    Zustand sichtbar (FR-C3) — deshalb liegt es von Anfang an in einem
    eigenen Template-Baustein.
    """
    return render(request, "colors/index.html", pentagon_context())


def pentagon_context():
    """
    Kontext für den Fünfeck-Baustein. Eigene Funktion, damit spätere
    Views (Task 1.6) ihn übernehmen können, ohne die Geometrie erneut
    aufzubauen.
    """
    vertices = pentagon.vertices(Color.objects.all())
    return {
        "vertices": vertices,
        "outline_points": pentagon.outline_points(vertices),
        "star_points": pentagon.star_points(vertices),
        "view_box": pentagon.view_box(vertices),
        "name_size": pentagon.NAME_SIZE,
    }
