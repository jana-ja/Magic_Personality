"""
Content-Entitäten für Color Infos (Task 1.1, PRD §6.1).

Eine einzige Entität für Farbkombinationen jeder Größe (D-02) statt
einer Tabelle je Größe — Felder ohne erfassten Inhalt bleiben bei
3er- bis 5er-Kombinationen einfach leer, das ist der Normalfall, kein
Fehler (Task 1.4 füllt die Einzelfarben und Zweierkombinationen).

`Color` trägt bewusst keine `locale`-Spalte: es gibt nur fünf feste
Zeilen, ihre Namen sind UI-Text (ARCHITECTURE.md §8), keine
mehrsprachige Content-Zeile wie bei den übrigen Modellen hier.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .utils import is_canonical


class Color(models.Model):
    class Code(models.TextChoices):
        WHITE = "W", _("White")
        BLUE = "U", _("Blue")
        BLACK = "B", _("Black")
        RED = "R", _("Red")
        GREEN = "G", _("Green")

    code = models.CharField(max_length=1, choices=Code.choices, unique=True)
    name = models.CharField(max_length=50)
    # Relativer Pfad unter static/ zum Mana-Symbol. Bleibt leer, bis
    # Task 1.5 die tatsächlichen Symbol-Dateien einbindet.
    symbol = models.CharField(max_length=100, blank=True)
    hex = models.CharField(max_length=7)
    # 0..4, im Uhrzeigersinn ab White (FR-C1).
    wheel_position = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = ["wheel_position"]

    def __str__(self):
        return self.name


class ColorCombination(models.Model):
    """
    Alle 31 Kombinationen (n = 1..5), vollständig vorangelegt (D-02).
    `code` ist die kanonisch WUBRG-sortierte Buchstabenfolge und
    zugleich die spätere URL (D-27, FR-C7) — z. B. "W", "WU", "WUBRG".
    """

    code = models.CharField(max_length=5, db_index=True)
    locale = models.CharField(max_length=10, default="en")

    name = models.CharField(max_length=100, blank=True)
    goal = models.TextField(blank=True)
    means = models.TextField(blank=True)
    guiding_question = models.TextField(blank=True)
    archetype = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["code", "locale"], name="unique_combination_code_per_locale"
            ),
        ]
        ordering = ["locale", "code"]

    def __str__(self):
        return f"{self.code} ({self.locale})"

    @property
    def size(self):
        """Anzahl der Farben in dieser Kombination (1 bis 5)."""
        return len(self.code)

    @property
    def color_codes(self):
        """Die einzelnen Farbcodes dieser Kombination, z. B. ["W", "U"]."""
        return list(self.code)

    def clean(self):
        if not 1 <= len(self.code) <= 5:
            raise ValidationError({"code": "code must contain between 1 and 5 colors."})
        if not is_canonical(self.code):
            raise ValidationError({"code": "code must be in canonical WUBRG order."})


class Trait(models.Model):
    """
    Eine Eigenschaft. `type` beschreibt die allgemeine gesellschaftliche
    Sicht, nicht die Sicht einer bestimmten Farbe — inhaltliche
    Überschneidungen sind ausdrücklich erlaubt (PRD §6.1), z. B.
    "Starrsinn" als Schwäche und "Beharrlichkeit" als Stärke.
    """

    class TraitType(models.TextChoices):
        STRENGTH = "STRENGTH", _("Strength")
        WEAKNESS = "WEAKNESS", _("Weakness")
        NEUTRAL = "NEUTRAL", _("Neutral")

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TraitType.choices)
    locale = models.CharField(max_length=10, default="en")

    class Meta:
        ordering = ["locale", "name"]

    def __str__(self):
        return self.name


class CombinationTrait(models.Model):
    """
    Zuordnung Eigenschaft <-> Kombination. Ersetzt "center / leaning
    left / leaning right": gespeichert wird, wohin eine Eigenschaft
    tendiert, nicht auf welcher Bildschirmseite sie liegt — links/
    rechts ergibt sich beim Rendern aus der Position im Fünfeck
    (PRD §6.1, D-03).

    Bei Einzelfarben zeigt `leaning_toward` auf einen der beiden
    Nachbarn oder ist leer (center). Bei allen Mehrfarb-Kombinationen
    ist es immer leer — das wird hier strukturell erzwungen; *welcher*
    Nachbar gültig ist, prüft erst Task 1.2 (Farbrad-Logik).

    Trägt bewusst keine eigene locale-Spalte (anders als Perspective):
    reiner Junction-Table ohne eigenen Textinhalt, die Sprache ergibt
    sich aus combination und trait — deren Übereinstimmung wird hier
    geprüft.
    """

    combination = models.ForeignKey(
        ColorCombination, on_delete=models.CASCADE, related_name="combination_traits"
    )
    trait = models.ForeignKey(Trait, on_delete=models.CASCADE, related_name="trait_combinations")
    leaning_toward = models.CharField(max_length=1, choices=Color.Code.choices, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["combination", "trait"], name="unique_trait_per_combination"
            ),
        ]

    def __str__(self):
        return f"{self.trait} @ {self.combination}"

    def clean(self):
        if self.combination_id and self.trait_id and self.combination.locale != self.trait.locale:
            raise ValidationError("combination and trait must share the same locale.")
        if self.leaning_toward and self.combination_id and len(self.combination.code) != 1:
            raise ValidationError(
                {"leaning_toward": "leaning_toward is only valid for single-color combinations."}
            )


class Perspective(models.Model):
    """
    Sichtweise innerhalb eines Feindpaares. Drei Zeilen je Feindpaar:
    `from_color` = eine der beiden Farben (deren eigene Sicht auf die
    andere) oder leer (die neutrale, gesellschaftliche Sicht auf das
    Paar). Dieselben Zeilen bedienen sowohl die Einzelfarb-Ansicht
    (FR-C8) als auch die Paar-Ansicht — der Content existiert nur
    einmal (PRD §6.1, D-05).
    """

    combination = models.ForeignKey(
        ColorCombination, on_delete=models.CASCADE, related_name="perspectives"
    )
    from_color = models.CharField(max_length=1, choices=Color.Code.choices, blank=True)
    text = models.TextField()
    locale = models.CharField(max_length=10, default="en")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["combination", "from_color"],
                name="unique_perspective_per_combination_and_viewpoint",
            ),
        ]

    def __str__(self):
        viewpoint = self.from_color or "neutral"
        return f"{self.combination} — {viewpoint}"

    def clean(self):
        if self.combination_id and len(self.combination.code) != 2:
            raise ValidationError({"combination": "Perspective requires a two-color combination."})
        if self.from_color and self.combination_id and self.from_color not in self.combination.code:
            raise ValidationError(
                {"from_color": "from_color must be one of the combination's own colors."}
            )
        if self.combination_id and self.locale != self.combination.locale:
            raise ValidationError({"locale": "locale must match the combination's own locale."})
