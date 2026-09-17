"""
Auswertungsregel (Task 2.9, FR-T10 bis FR-T12, D-17).

Reine Funktion auf einem bereits gezählten Punktestand (`scoring.tally()`,
Task 2.8) — kein Zugriff auf Request oder Formulare, wie
`apps/colors/pentagon.py`/`apps/accounts/avatar.py`.

Die Regel in Kurzform (FR-T11): Standard sind die drei höchsten
Farben. Zwei oder vier werden nur gewählt, wenn der Punktabstand an
genau dieser Grenze (`G(2)` bzw. `G(4)`) den Abstand an der
Dreier-Grenze (`G(3)`) um mindestens `T` übersteigt — sonst bleibt es
bei drei. Ein Punktgleichstand *an* der am Ende gewählten Grenze zählt
nicht als Schnitt: alle gleichauf liegenden Farben kommen mit ins
Ergebnis (FR-T12), auch wenn das über die ursprünglich ermittelte
Ergebnisgröße hinausgeht.

Zwei Randfälle, die FR-T11/FR-T12 nicht ausdrücklich regeln, hier
bewusst festgelegt (siehe D-59):
- Übersteuern `G(2)` und `G(4)` beide *und* sind exakt gleich groß,
  bleibt es beim Standardwert 3 — FR-T11.4 kennt nur "der größere
  Abstand gewinnt", keinen Sieger bei einem Gleichstand zwischen den
  Übersteuerungen selbst.
- `k` startet laut FR-T11 immer bei 2, 3 oder 4 und die
  Gleichstand-Erweiterung aus FR-T12 vergrößert `k` nur — ein
  Ergebnis mit nur einer Farbe ist über diese Regel rechnerisch nicht
  erreichbar, obwohl FR-T12 wörtlich "1 bis 5 Farben" nennt.
"""

from django.conf import settings

from apps.colors.content import LOCALE
from apps.colors.models import ColorCombination
from apps.colors.utils import canonical_code


def result_size(sorted_points, *, threshold=None):
    """
    `sorted_points`: die fünf Punktzahlen absteigend sortiert (FR-T10).
    Gibt `k` zurück — wie viele der höchsten Farben das Ergebnis bilden,
    *vor* der Gleichstand-Erweiterung aus FR-T12 (siehe `evaluate()`).
    """
    if threshold is None:
        threshold = settings.QUIZ_RESULT_THRESHOLD

    def gap(rank):
        # G(rank): Punktabstand zwischen Rang `rank` und `rank + 1`
        # (1-indexiert, FR-T10).
        return sorted_points[rank - 1] - sorted_points[rank]

    gap_2, gap_3, gap_4 = gap(2), gap(3), gap(4)
    take_two = gap_2 >= gap_3 + threshold
    take_four = gap_4 >= gap_3 + threshold

    if take_two and take_four:
        # FR-T11.4: "gewinnt der größere Abstand". Bei einem exakten
        # Gleichstand zwischen den beiden Übersteuerungen selbst nennt
        # die PRD keinen Sieger — der Standardwert bleibt dann bestehen,
        # statt eine der beiden Abweichungen willkürlich zu bevorzugen.
        if gap_2 > gap_4:
            return 2
        if gap_4 > gap_2:
            return 4
        return 3
    if take_two:
        return 2
    if take_four:
        return 4
    return 3


def evaluate(scores, *, threshold=None):
    """
    `scores`: `{"W": 5, "U": 3, ...}` (Ausgabe von `scoring.tally()`).
    Gibt die Menge der Farbcodes zurück, die das Ergebnis bilden — 1 bis
    5 Farben (FR-T12).
    """
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    points = [score for _code, score in ranked]

    k = result_size(points, threshold=threshold)

    # FR-T12: Gleichstand an der (jeweils aktuellen) Schnittgrenze
    # nimmt alle betroffenen Farben auf — nötigenfalls mehrfach
    # hintereinander (siehe "Gleichstand über alle fünf").
    while k < 5 and points[k - 1] == points[k]:
        k += 1

    return frozenset(code for code, _score in ranked[:k])


def evaluate_combination(scores, *, threshold=None):
    """
    Wie `evaluate()`, aber direkt auf die passende `ColorCombination`
    abgebildet (Roadmap 2.9: "Ergebnis wird auf eine der 31
    Kombinationen abgebildet", D-27) statt nur auf eine Farbmenge.
    """
    code = canonical_code(evaluate(scores, threshold=threshold))
    return ColorCombination.objects.get(code=code, locale=LOCALE)
