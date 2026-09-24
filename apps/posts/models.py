"""
Beiträge (Task 5.1, FR-B1, FR-B2, FR-B8, FR-B9, D-78), Meldungen (Task 5.7/6.5,
FR-B10, D-81), Kommentare (Task 6.1, FR-B14, FR-B15, D-79), der Stand des
Zählers neuer Kommentare (Task 6.6, FR-B20, D-79) und die Pinnwand
(Task 7.1, FR-B21, FR-B23/FR-B24, D-82).

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
from django.db.models import Exists, OuterRef, Q
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual
from django.utils.translation import gettext_lazy as _

TITLE_MAX_LENGTH = 120
BODY_MAX_LENGTH = 10_000
# Klartext (D-80), deutlich kürzer als ein Beitrag (Task 6.1, FR-B13).
COMMENT_MAX_LENGTH = 2000

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
    Meldung eines Beitrags oder eines Kommentars (Task 5.7/6.5, FR-B10,
    FR-B18, D-81). Sichtbar nur für die Projektinhaberin im Django-Admin; es
    gibt kein automatisches Ausblenden.

    Genau eines von `post`/`comment` ist gesetzt (Check-Constraint — die
    Views legen nie beide oder keines an, das hier ist die Absicherung in
    der Datenbank). Einmal je Person und Ziel (zwei partielle
    Unique-Constraints, je eine für `post` und `comment` — eine einzelne
    über beide Spalten hinweg würde zwei Meldungen derselben Person
    zulassen, solange nur jeweils die andere Spalte `NULL` ist). Die Grenze
    aus FR-B11/FR-B18 zählt **beide** zusammen: `profile.reports.all()`
    kennt keine Unterscheidung nach Ziel.

    Die Meldung verschwindet mit dem gemeldeten Eintrag (Kaskade) und mit
    dem Account der meldenden Person (D-81). Wird ein Kommentar zur Hülle
    gemacht (Task 6.3/6.5), bleibt seine Zeile bestehen — die Meldung dazu
    bleibt deshalb ebenfalls bestehen, bis die Projektinhaberin sie im
    Admin als bearbeitet markiert.
    """

    MAX_REASON_LENGTH = 500

    reporter = models.ForeignKey(
        "accounts.Profile", on_delete=models.CASCADE, related_name="reports"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    comment = models.ForeignKey(
        "Comment", on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    reason = models.CharField(max_length=MAX_REASON_LENGTH, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Gesetzt, sobald die Projektinhaberin die Meldung im Admin als bearbeitet markiert.
    handled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(post__isnull=False, comment__isnull=True)
                    | Q(post__isnull=True, comment__isnull=False)
                ),
                name="report_exactly_one_of_post_or_comment",
            ),
            models.UniqueConstraint(
                fields=["reporter", "post"],
                condition=Q(post__isnull=False),
                name="report_once_per_person_and_post",
            ),
            models.UniqueConstraint(
                fields=["reporter", "comment"],
                condition=Q(comment__isnull=False),
                name="report_once_per_person_and_comment",
            ),
        ]

    def __str__(self):
        return f"{self.reporter} → {self.post or self.comment}"

    @property
    def is_open(self):
        return self.handled_at is None

    @property
    def target(self):
        """Das gemeldete Ding, gleich welcher Art (immer genau eines gesetzt)."""
        return self.post or self.comment


class CommentQuerySet(models.QuerySet):
    def for_post(self, post):
        """
        Die Kommentare eines Beitrags für die Anzeige (Task 6.2, FR-B13, D-79):
        älteste zuerst (`Meta.ordering`), ohne Hüllen ohne Antworten — sie
        tragen nichts mehr bei, sobald niemand mehr auf sie verweist.

        `Exists()` statt eines `annotate(Count(...))`: fragt nur „gibt es
        mindestens eine Antwort", ohne für jeden Kommentar alle seine
        Antworten zu zählen.
        """
        has_a_reply = self.model.objects.filter(reply_to=OuterRef("pk"))
        return (
            self.filter(post=post)
            .annotate(has_reply=Exists(has_a_reply))
            .exclude(deleted_at__isnull=False, has_reply=False)
        )


class Comment(models.Model):
    """
    Kommentar unter einem Beitrag (Task 6.1, FR-B13 bis FR-B16, D-79). **Flach**
    (kein Baum): `reply_to` verweist höchstens auf einen Kommentar desselben
    Beitrags, eine Antwort auf eine Antwort verweist auf diese, nicht
    verschachtelt.

    `number` ist die Nummer **je Beitrag** (`#1`, `#2`, …, `unique (post,
    number)`), vergeben von `apps.posts.comments.create_comment()` atomar aus
    `Post.comment_seq` — nie hier direkt zuweisen. Sie wird **nie neu
    vergeben**, auch wenn der Kommentar später zur Hülle wird (s. u.).

    **Löschen** (Task 6.3) setzt `deleted_at` und leert `body`/`author` — die
    Zeile selbst bleibt (**Hülle**), damit Nummern und `reply_to`-Verweise
    anderer Kommentare stabil bleiben; es gibt bewusst keine
    `Comment.objects.delete()`-Stelle im Anwendungscode. Deshalb ist `author`
    nullbar und **nicht** kaskadierend mit `Profile` verknüpft
    (`on_delete=PROTECT`, anders als bei `Post.author`/`Report.reporter`,
    D-78): Löscht jemand den eigenen Account, muss der Löschvorgang jeden
    eigenen Kommentar **zuerst** zur Hülle machen (Task 6.3) — vergisst er
    das, bricht `PROTECT` den Vorgang, statt eine Zeile mit Autor, aber ohne
    zugehöriges Profil zu hinterlassen. `test_account_deletion.py`s Wächter
    (Task 5.9) nennt genau dieses Feld als bewusste Ausnahme von der sonst
    durchgängigen Kaskade.

    Kommentare sind **nicht bearbeitbar**: bei Verweisen bliebe sonst unklar,
    worauf sich eine Antwort einmal bezogen hat (anders als bei `Post`, D-72).

    **Anzeige** (Task 6.2): `objects.for_post(post)` ist der Weg, auf dem eine
    Seite Kommentare liest — er lässt Hüllen ohne Antworten aus (D-79: „Eine
    Hülle wird nur angezeigt, wenn auf sie geantwortet wurde"). Eine Hülle mit
    Antworten bleibt drin, damit deren „↪ #n"-Verweise ein Ziel behalten.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    # None: entweder eine Hülle (deleted_at gesetzt), oder — künftig denkbar,
    # heute nicht vorgesehen — ein Kommentar ohne zurechenbare Person.
    author = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="comments",
    )
    number = models.PositiveIntegerField()
    # Klartext (D-80), nicht Markdown: kürzer, weniger Angriffsfläche. Leer nur
    # bei einer Hülle — die Datenbank erzwingt das nicht (dafür bräuchte es
    # einen Constraint mit deleted_at), `apps.posts.comments` erzwingt es.
    body = models.TextField(blank=True, validators=[MaxLengthValidator(COMMENT_MAX_LENGTH)])
    reply_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = CommentQuerySet.as_manager()

    class Meta:
        ordering = ["number"]
        indexes = [
            # Profil-Tab „Comments" (Task 6.4).
            models.Index(fields=["author", "-created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["post", "number"], name="comment_unique_number_per_post"
            ),
            models.CheckConstraint(
                condition=LessThanOrEqual(Length("body"), COMMENT_MAX_LENGTH),
                name="comment_body_max_length",
            ),
        ]

    def __str__(self):
        return f"#{self.number} on {self.post}"

    @property
    def is_tombstone(self):
        return self.deleted_at is not None


class PostSeen(models.Model):
    """
    Der Stand des Zählers neuer Kommentare (Task 6.6, FR-B20, D-79):
    `last_seen_number` ist die höchste Kommentar-Nummer dieses Beitrags, die
    `profile` schon gesehen hat — technisch derselbe Wert wie
    `Post.comment_seq` zum Zeitpunkt des letzten Aufrufs, nicht live daran
    gekoppelt (`apps.posts.seen.mark_seen()` schreibt ihn fest).

    Es gibt nur eine Zeile je Person und Beitrag — auch wenn beide Gründe
    aus FR-B20 zutreffen (Autorin/Autor **und** eigener Kommentar
    darunter), reicht ein gemeinsamer Stand: „neu" bemisst sich ohnehin an
    derselben Zahl. Eine Zeile entsteht nur für Personen mit einem der
    beiden Gründe (`mark_seen()` prüft das) — für alle anderen gäbe es nie
    eine „neu"-Markierung, eine Zeile wäre also Verschwendung.
    """

    profile = models.ForeignKey(
        "accounts.Profile", on_delete=models.CASCADE, related_name="post_seen"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="seen_by")
    last_seen_number = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "post"], name="post_seen_once_per_person_and_post"
            ),
        ]

    def __str__(self):
        return f"{self.profile} @ {self.post} (#{self.last_seen_number})"


class Pin(models.Model):
    """
    Ein Eintrag der Pinnwand (Task 7.1, FR-B21, FR-B23/FR-B24, D-82): reiner
    Verweis auf einen Beitrag oder Kommentar, **eigene wie fremde** — anders
    als bei `Report` muss niemand zustimmen, die Inhalte sind ohnehin für
    alle Angemeldeten sichtbar (FR-B24). Kopiert nichts; verschwindet mit dem
    Original (Kaskade) oder — sobald ein Kommentar zur Hülle wird, ohne dass
    die Zeile selbst verschwindet (D-79) — aus der Anzeige (Task 7.3, FR-B23).

    Genau eines von `post`/`comment` ist gesetzt, einmal je Person und Ziel —
    dieselbe Konstruktion wie bei `Report` (Check-Constraint plus zwei
    partielle Unique-Constraints statt einer einzigen über beide Spalten
    hinweg, die sonst zwei Pins derselben Person zuließe, solange nur je eine
    Spalte `NULL` bleibt).
    """

    profile = models.ForeignKey("accounts.Profile", on_delete=models.CASCADE, related_name="pins")
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True, blank=True, related_name="pins"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="pins"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(post__isnull=False, comment__isnull=True)
                    | Q(post__isnull=True, comment__isnull=False)
                ),
                name="pin_exactly_one_of_post_or_comment",
            ),
            models.UniqueConstraint(
                fields=["profile", "post"],
                condition=Q(post__isnull=False),
                name="pin_once_per_person_and_post",
            ),
            models.UniqueConstraint(
                fields=["profile", "comment"],
                condition=Q(comment__isnull=False),
                name="pin_once_per_person_and_comment",
            ),
        ]

    def __str__(self):
        return f"{self.profile} → {self.post or self.comment}"

    @property
    def target(self):
        """Das gepinnte Ding (immer genau eines gesetzt) — wie `Report.target`."""
        return self.post or self.comment
