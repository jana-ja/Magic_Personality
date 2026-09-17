"""
Punkte-Zählung aus abgegebenen Antworten (Task 2.8, FR-T5, D-65).

Reine Zählung — wandelt die je Frage gewählten `AnswerOption`s einer
Abgabe in Punkte je Farbe um. Die eigentliche Auswertungsregel (welche
Farben am Ende das Ergebnis bilden, FR-T10 bis FR-T12) steht bewusst
NICHT hier: das ist Task 2.9, ein eigener, von der reinen Zählung
unabhängiger Schritt.
"""

from apps.colors.models import Color


def tally(weighted_answers):
    """
    `weighted_answers`: Paare aus gewählter `AnswerOption`-Instanz und
    ihren Punkten (z. B. `TakeTestForm.weighted_answers()`; in v1 immer
    1 Punkt, in v2 2 für die beste und 1 für die zweitbeste Antwort).
    Gibt für alle fünf Farben einen Eintrag zurück, auch wenn eine Farbe
    nie gewählt wurde (Punktzahl 0) — ARCHITECTURE.md §6.4:
    `{"W": 5, "U": 3, ...}`.
    """
    scores = dict.fromkeys((code for code, _label in Color.Code.choices), 0)
    for answer, points in weighted_answers:
        scores[answer.color] += points
    return scores
