"""
Schreibzugriffe auf die Profilfarben (`ColorAssignment`), die von mehreren
Stellen gebraucht werden: Übernahme eines Testergebnisses (Ergebnisseite,
Historie, Farbformular im Profil) — eine Stelle statt drei Kopien (FR-P5).
"""

from apps.colors.content import LOCALE
from apps.colors.models import ColorCombination

from .models import ColorAssignment


def adopt_test_result(test_result):
    """
    FR-T14/FR-P5/D-07: setzt `source = SELF_TEST` und die Testreferenz und
    macht die Kombination des Ergebnisses zu den Profilfarben.

    Nicht `evaluate_combination(test_result.scores)` neu berechnen: die
    Auswertungsregel oder `result_threshold` könnten sich seither geändert
    haben — `result_colors` ist das Ergebnis, das zum Testzeitpunkt
    tatsächlich angezeigt wurde (D-61).
    """
    combination = ColorCombination.objects.get(code=test_result.result_colors, locale=LOCALE)
    assignment, _created = ColorAssignment.objects.update_or_create(
        profile=test_result.profile,
        defaults={
            "author_profile": test_result.profile,
            "combination": combination,
            "source": ColorAssignment.Source.SELF_TEST,
            "test_result": test_result,
        },
    )
    return assignment
