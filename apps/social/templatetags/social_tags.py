"""
Template-Tags der Social-App (Task 4.8, FR-P15, D-73).
"""

from django import template

from apps.accounts import avatar
from apps.colors.models import Color

register = template.Library()

SIZES = ("small", "medium")


def _hex_by_code(context):
    """
    Die fünf Farbwerte einmal laden, nicht je Karte. Der Zwischenspeicher hängt an
    der Anfrage: `render_context` gilt nur je Template, und eine Karte, die selbst
    per `{% include %}` eingebunden ist (Beitragskarten, Task 5.6), bekäme sonst
    jedes Mal einen frischen und lüde die Werte je Karte neu. Ohne Anfrage im
    Kontext (Rendern außerhalb eines Views) gilt der Zwischenspeicher je Template.
    """
    request = context.get("request")
    if request is not None:
        cached = getattr(request, "_author_card_hex", None)
        if cached is None:
            cached = request._author_card_hex = dict(Color.objects.values_list("code", "hex"))
        return cached
    cached = context.render_context.get("author_card_hex")
    if cached is None:
        cached = dict(Color.objects.values_list("code", "hex"))
        context.render_context["author_card_hex"] = cached
    return cached


@register.inclusion_tag("social/_author_card.html", takes_context=True)
def author_card(context, profile, size="medium"):
    """
    Die Autorenkarte: Profilbild, Nickname (Link auf das Profil) und
    Kombinationsname als Chip. Braucht **nur ein Profil** — keine
    Sonderfälle je Einsatzort —, damit Beiträge und Kommentare sie später
    ohne Änderung einbinden können (`{% author_card comment.author %}`).

    `size`: `"small"` (Vorschauen, Anfragen) oder `"medium"` (Listen).

    Die Zuordnung wird über `profile.color_assignments.all()` gelesen und
    nutzt damit einen Prefetch (`color_assignments__combination`), wenn der
    Aufrufer eine Liste vorbereitet hat — ohne Prefetch kostet die Karte eine
    Abfrage mehr, sie bleibt korrekt. Mit Prefetch fragt eine Liste von Karten
    je Karte gar nichts mehr ab.
    """
    if size not in SIZES:
        raise ValueError(f"Unknown author card size: {size!r}")
    hex_by_code = _hex_by_code(context)

    assignment = next(iter(profile.color_assignments.all()), None)
    return {
        "profile": profile,
        "size": size,
        "combination": assignment.combination if assignment else None,
        **avatar.avatar_context(assignment, hex_by_code),
    }
