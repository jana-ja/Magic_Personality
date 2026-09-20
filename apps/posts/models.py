"""
Beiträge (Task 5.1, FR-B1, FR-B2, FR-B8, FR-B9, D-78) und Meldungen (Task 5.7,
FR-B10, D-81).

`Post.author` verweist auf `accounts.Profile`, nicht auf `accounts.User`
(D-78) — wie `Friendship` (D-22): die Autorenkarte braucht nur das
Profil, ein geänderter Nickname ändert nichts an Beiträgen.

`colors` ist der kanonische WUBRG-Code (D-27) statt eines Fremdschlüssels
auf `ColorCombination`, weil diese Zeilen je Sprache angelegt sind (D-15)
— der Code gilt für alle und ist genau das, wonach die Color Infos
filtern. Leer heißt „allgemeiner Beitrag". Die Regel „kanonisch" steht
als Validator (Formulare, `full_clean`) **und** als DB-Constraint: ein
unkanonischer Code (`GW` statt `WG`) fände im Grid nie seine
Kombination.

**Lesen geht ausschließlich durch `Post.objects.visible_to(profile)`**
(FR-B9, D-78). Views, Templates und Tags greifen nie direkt auf
`Post.objects` zu; nur so lässt sich „nur Freunde" später an einer
Stelle ergänzen (Test in Task 7.4).
"""

from django.core.validators import MaxLengthValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual
from django.utils.translation import gettext_lazy as _

TITLE_MAX_LENGTH = 120
BODY_MAX_LENGTH = 10_000

# Genau die kanonischen Codes: höchstens einmal je Farbe, in WUBRG-
# Reihenfolge, leer erlaubt. Dieselbe Regel wie `apps.colors.utils.is_canonical`,
# aber als Muster, damit auch die Datenbank sie prüfen kann.
CANONICAL_COLORS_PATTERN = r"^W?U?B?R?G?$"


class PostQuerySet(models.QuerySet):
    def visible_to(self, profile):
        """
        Die Beiträge, die `profile` sehen darf — die einzige Lesestelle
        (FR-B9). `None` (ein Gast) sieht nichts (FR-B8); die Views
        verlangen ohnehin eine Anmeldung, das hier ist der zweite Riegel.

        Heute ist alles `public`. Kommt „nur Freunde" (PRD §8.2), ändert
        sich genau diese Methode: `profile` steht deshalb schon in der
        Signatur.
        """
        if profile is None:
            return self.none()
        return self.filter(visibility=Post.Visibility.PUBLIC)


class Post(models.Model):
    class Visibility(models.TextChoices):
        # `friends` kommt erst mit dem Feature (PRD §8.2): das Feld soll nie
        # einen Wert erlauben, den nichts beachtet.
        PUBLIC = "public", _("Public")

    author = models.ForeignKey("accounts.Profile", on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    # Markdown (D-80); gespeichert wird nur die Quelle, gerendert beim Anzeigen.
    body = models.TextField(validators=[MaxLengthValidator(BODY_MAX_LENGTH)])
    colors = models.CharField(
        max_length=5,
        blank=True,
        validators=[
            RegexValidator(CANONICAL_COLORS_PATTERN, _("Colors must be in WUBRG order, once each."))
        ],
    )
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Nur bei tatsächlicher Änderung gesetzt (Task 5.3, wie D-72).
    edited_at = models.DateTimeField(null=True, blank=True)
    # Zähler für die Kommentarnummern (D-79, Task 6.1); hier nur angelegt,
    # damit v1.4 keine Änderung an dieser Tabelle mehr braucht.
    comment_seq = models.PositiveIntegerField(default=0)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [
            # Grid je Kombination (Task 5.6) und Profil-Tab (Task 5.5).
            models.Index(fields=["colors", "-created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(condition=~Q(title=""), name="post_title_not_empty"),
            models.CheckConstraint(
                condition=LessThanOrEqual(Length("body"), BODY_MAX_LENGTH),
                name="post_body_max_length",
            ),
            models.CheckConstraint(
                condition=Q(colors__regex=CANONICAL_COLORS_PATTERN),
                name="post_colors_canonical",
            ),
        ]

    def __str__(self):
        return self.title


class Report(models.Model):
    """
    Meldung eines Beitrags (Task 5.7, FR-B10, D-81). Sichtbar nur für die
    Projektinhaberin im Django-Admin; es gibt kein automatisches Ausblenden.

    Einmal je Person und Beitrag (Unique-Constraint). Die Meldung verschwindet
    mit dem gemeldeten Beitrag und mit dem Account der meldenden Person
    (Kaskade, D-81). Ab v1.4 kommt `comment` als Alternative zu `post` dazu
    (Task 6.5).
    """

    MAX_REASON_LENGTH = 500

    reporter = models.ForeignKey(
        "accounts.Profile", on_delete=models.CASCADE, related_name="reports"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reports")
    reason = models.CharField(max_length=MAX_REASON_LENGTH, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Gesetzt, sobald die Projektinhaberin die Meldung im Admin als bearbeitet markiert.
    handled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "post"], name="report_once_per_person_and_post"
            ),
        ]

    def __str__(self):
        return f"{self.reporter} → {self.post}"

    @property
    def is_open(self):
        return self.handled_at is None
