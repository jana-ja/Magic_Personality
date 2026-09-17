"""
Fragebogen-Datenmodell (Task 2.6, D-16).

`Questionnaire` trägt eine Versionsnummer (FR-T6); Fragen einer bereits
veröffentlichten Version werden nicht mehr verändert — Änderungen
erzeugen eine neue Version. Diese Regel wird bewusst nicht hier im
Modell erzwungen (ein einzelner Feld-Wert reicht nicht, um "unverändert"
von "identisch neu geschrieben" zu unterscheiden), sondern im
Seed-Command (Task 2.6), der als einziger Weg gilt, Fragen einzuspielen
(D-28) und deshalb der richtige Ort für diese Prüfung ist.

`TestResult` ist der Historieneintrag eines Testdurchlaufs (FR-T10 bis
FR-T17) und verweist auf `accounts.Profile` — nicht umgekehrt, obwohl
`accounts.ColorAssignment.test_result` seinerseits hierher zeigt (D-07):
beide Verweise sind unabhängig voneinander, keiner ist zirkulär.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.colors.models import Color


def default_choice_points():
    return [1]


class Questionnaire(models.Model):
    """Eine Fragebogen-Version (FR-T6). `question_count` ist die Sollzahl
    für Task 2.7s Balance-Test, nicht aus `questions` abgeleitet — sie
    steht bereits fest, bevor überhaupt eine Frage angelegt ist."""

    version = models.PositiveIntegerField(unique=True)
    question_count = models.PositiveSmallIntegerField()
    published_at = models.DateTimeField(null=True, blank=True)
    # D-65: Punkte je Rang einer Frage. `[1]` = eine Antwort wählen,
    # 1 Punkt (v1); `[2, 1]` = beste und zweitbeste Antwort wählen (v2).
    # Die Länge ist zugleich die Zahl der Auswahlen je Frage.
    choice_points = models.JSONField(default=default_choice_points)
    # FR-T11: `T` gehört zur Punkteskala einer Version, nicht global —
    # 30 Punkte in v1 und 45 in v2 brauchen verschiedene Werte (D-65).
    # Anders als die Fragen auch nach Veröffentlichung änderbar (R-4).
    result_threshold = models.PositiveSmallIntegerField(default=2)

    class Meta:
        ordering = ["version"]

    def __str__(self):
        return f"v{self.version}"

    @property
    def is_published(self):
        return self.published_at is not None

    def clean(self):
        points = self.choice_points
        if (
            not isinstance(points, list)
            or not points
            or not all(isinstance(value, int) and value > 0 for value in points)
            or points != sorted(points, reverse=True)
        ):
            raise ValidationError(
                {"choice_points": "must be a non-empty, descending list of positive integers."}
            )


class Question(models.Model):
    """Eine Frage einer Questionnaire-Version (FR-T1, FR-T2). `position`
    plus `locale` ist der natürliche Schlüssel, wie bei den
    Content-Modellen in `apps.colors` (ARCHITECTURE.md §8)."""

    class Dimension(models.TextChoices):
        # D-60: je Farbpaar genau eine Frage pro Dimension (FR-T3, FR-T4).
        ACTION = "ACTION", _("Action")
        MOTIVATION = "MOTIVATION", _("Motivation")
        PERCEPTION = "PERCEPTION", _("Perception")

    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name="questions"
    )
    position = models.PositiveSmallIntegerField()
    text = models.TextField()
    dimension = models.CharField(max_length=20, choices=Dimension.choices)
    locale = models.CharField(max_length=10, default="en")

    class Meta:
        ordering = ["questionnaire", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["questionnaire", "position", "locale"],
                name="unique_question_position_per_questionnaire_and_locale",
            ),
        ]

    def __str__(self):
        return f"{self.questionnaire} #{self.position} ({self.locale})"


class AnswerOption(models.Model):
    """Eine der zwei Antworten einer Frage (FR-T2, FR-T5). `color` ist die
    Farbe, die bei Auswahl einen Punkt bekommt — für Testende nicht
    erkennbar benannt (FR-T2), nur intern gespeichert."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answer_options")
    # Anzeigereihenfolge innerhalb der Frage, aus der Reihenfolge in der
    # Seed-Datei (D-65) — nie nach Farbe sortiert, sonst stünde dieselbe
    # Farbe immer an derselben Stelle.
    position = models.PositiveSmallIntegerField(default=0)
    text = models.TextField()
    color = models.CharField(max_length=1, choices=Color.Code.choices)
    locale = models.CharField(max_length=10, default="en")

    class Meta:
        ordering = ["question", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "color"], name="unique_answer_option_color_per_question"
            ),
        ]

    def __str__(self):
        return f"{self.color} @ {self.question}"

    def clean(self):
        if self.question_id and self.locale != self.question.locale:
            raise ValidationError({"locale": "locale must match the question's own locale."})


class TestResult(models.Model):
    """Historieneintrag eines Testdurchlaufs (FR-P6, FR-T13, FR-T17).
    `questionnaire_version` ist bewusst die Versionsnummer selbst, kein
    Fremdschlüssel auf `Questionnaire`: ein Historieneintrag muss auch
    dann noch interpretierbar bleiben, wenn die Fragebogen-Zeile jemals
    entfernt würde (FR-T6 nennt nur die Fragen als unveränderlich, nicht
    die Aufbewahrung alter Versionen als Garantie)."""

    # Der Modellname beginnt mit "Test" — ohne das hier würde pytest
    # beim Import in Testdateien versuchen, die Klasse selbst als
    # Testklasse einzusammeln, und mit einer Warnung abbrechen.
    __test__ = False

    profile = models.ForeignKey(
        "accounts.Profile", on_delete=models.CASCADE, related_name="test_results"
    )
    questionnaire_version = models.PositiveIntegerField()
    taken_at = models.DateTimeField(auto_now_add=True)
    # {"W": 5, "U": 3, "B": 4, "R": 4, "G": 4} (ARCHITECTURE.md §6.4)
    scores = models.JSONField()
    result_colors = models.CharField(max_length=5)

    class Meta:
        ordering = ["-taken_at"]

    def __str__(self):
        return f"{self.result_colors} ({self.taken_at:%Y-%m-%d})"

    @property
    def ordered_scores(self):
        """`(Farbcode, Punkte)` in WUBRG-Reihenfolge. PostgreSQL speichert
        `scores` als jsonb und sortiert die Schlüssel dabei selbst um
        (B, G, R, U, W) — die gespeicherte Reihenfolge taugt also nicht
        für die Anzeige."""
        return [(code, self.scores.get(code, 0)) for code, _label in Color.Code.choices]
