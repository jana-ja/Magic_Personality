"""
Anzeigenamen der Farbverknüpfung eines Beitrags (Task 5.4, FR-B5).

`Post.colors` ist nur der kanonische Code (D-78); die Beitragsseite und
später die Listen und das Grid (Task 5.5, 5.6) zeigen den Namen der
Kombination. Die Namen liegen je Sprache in `ColorCombination` — eine
Abfrage für alle Codes einer Seite, nicht je Beitrag.
"""

from django.urls import reverse

from apps.colors.content import LOCALE
from apps.colors.models import Color, ColorCombination


def combination_labels(codes):
    """
    `{code: Anzeigename}` für die übergebenen kanonischen Codes (leere und
    doppelte werden ignoriert). Hat eine Kombination noch keinen Namen
    (FR-C11: fehlender Inhalt ist kein Fehler), stehen die Farbnamen
    stattdessen da: „White · Green".
    """
    codes = {code for code in codes if code}
    if not codes:
        return {}
    names = dict(
        ColorCombination.objects.filter(locale=LOCALE, code__in=codes).values_list("code", "name")
    )
    color_names = None
    labels = {}
    for code in codes:
        label = names.get(code, "")
        if not label:
            if color_names is None:
                color_names = dict(Color.objects.values_list("code", "name"))
            label = " · ".join(color_names[color] for color in code)
        labels[code] = label
    return labels


def combination_url(code):
    """Die Color-Infos-Seite zu einem kanonischen Code."""
    return reverse("colors:combination", kwargs={"code": code.lower()})
