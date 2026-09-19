"""
Template-Tags der Social-App (Task 4.8, FR-P15, D-73).
"""

from django import template

from apps.accounts import avatar
from apps.colors.models import Color

register = template.Library()

SIZES = ("small", "medium")


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
    # Die fünf Farbwerte einmal je Template-Rendering laden, nicht je Karte.
    hex_by_code = context.render_context.get("author_card_hex")
    if hex_by_code is None:
        hex_by_code = dict(Color.objects.values_list("code", "hex"))
        context.render_context["author_card_hex"] = hex_by_code

    assignment = next(iter(profile.color_assignments.all()), None)
    return {
        "profile": profile,
        "size": size,
        "combination": assignment.combination if assignment else None,
        **avatar.avatar_context(assignment, hex_by_code),
    }
