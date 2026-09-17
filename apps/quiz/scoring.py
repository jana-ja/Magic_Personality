"""
Punkte-Zählung aus abgegebenen Antworten (Task 2.8, FR-T5).

Reine Zählung — wandelt die je Frage gewählte `AnswerOption` einer
Abgabe in Punkte je Farbe um. Die eigentliche Auswertungsregel (welche
Farben am Ende das Ergebnis bilden, FR-T10 bis FR-T12) steht bewusst
NICHT hier: das ist Task 2.9, ein eigener, von der reinen Zählung
unabhängiger Schritt.
"""

from apps.colors.models import Color


def tally(chosen_answers):
    """
    `chosen_answers`: die je Frage gewählte `AnswerOption`-Instanz
    (z. B. `form.cleaned_data.values()`). Gibt für alle fünf Farben
    einen Eintrag zurück, auch wenn eine Farbe nie gewählt wurde
    (Punktzahl 0) — ARCHITECTURE.md §6.4: `{"W": 5, "U": 3, ...}`.
    """
    scores = dict.fromkeys((code for code, _label in Color.Code.choices), 0)
    for answer in chosen_answers:
        scores[answer.color] += 1
    return scores
