"""
Eigenes User-Modell (Task 0.2, D-26).

Nur Zugangsdaten — kein Nickname, keine Bio, kein Profilbild. Das ist
Absicht (D-22): Profildarstellung gehört in `Profile`, das erst mit
Task 2.1 entsteht und optional auf einen User verweist. Das hält den
Weg zu fremd angelegten Profilen offen, ohne hier Aufwand zu erzeugen.

`PermissionsMixin` bleibt bewusst Teil des Modells, obwohl v1 kein
Rechtekonzept kennt — es trägt das spätere Kuratoren-Konzept (PRD §8.2)
ohne weitere Migration.
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Ersetzt Djangos Standard-Manager, der einen `username` erwartet.
    `use_in_migrations = True`, damit `createsuperuser` und Migrationen
    denselben Manager sehen (Django-Konvention für Custom-User-Modelle).
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    FR-U1/FR-U2: E-Mail und Passwort, E-Mail eindeutig und zugleich
    Anmeldefeld. Bewusst kein `username`-Feld.
    """

    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.email


class Profile(models.Model):
    """
    Darstellung einer Person (Task 2.1, FR-P1, D-22). Bewusst getrennt
    von `User`: `user` ist optional (`OneToOneField(null=True)`), damit
    fremd angelegte Profile ohne Account möglich bleiben (PRD §8.1) —
    in v1 hat jedes Profil genau einen User, erzeugt bei der
    Registrierung (Task 2.2).
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="profile"
    )
    nickname = models.CharField(_("nickname"), max_length=50)
    bio = models.TextField(_("bio"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # FR-P2: global eindeutig, Groß-/Kleinschreibung egal. Als
            # DB-Constraint statt nur als Anwendungsprüfung, damit zwei
            # gleichzeitige Registrierungen (Task 2.2) nicht doppelt
            # durchkommen können.
            models.UniqueConstraint(Lower("nickname"), name="unique_profile_nickname_ci"),
        ]

    def __str__(self):
        return self.nickname


class ColorAssignment(models.Model):
    """
    Die Farben einer Person (Task 2.1, FR-P4/FR-P5). Eigene Entität
    statt Spalten am Profil (D-22): `author_profile` hält fest, wer
    die Einschätzung abgegeben hat — in v1 immer `author_profile ==
    profile`, aber das Schema erlaubt später fremde Einschätzungen
    (PRD §8.1) ohne Umbau.

    `combination` verweist auf eine der 31 `ColorCombination`-Zeilen
    (D-27) statt Farben einzeln zu verknüpfen — die Farben einer
    Person *sind* eine dieser Kombinationen, keine zweite Darstellung
    im System.

    PRD §6.2: "es existiert höchstens ein Datensatz je Profil" — daher
    der Unique-Constraint auf `profile` allein, obwohl das Feld selbst
    ein `ForeignKey` bleibt (nicht `OneToOneField`), damit sich das
    später lockern lässt, ohne die Spalte auszutauschen.
    """

    class Source(models.TextChoices):
        SELF_MANUAL = "SELF_MANUAL", _("Self-assessed, manually chosen")
        SELF_TEST = "SELF_TEST", _("Self-assessed, from a test result")

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="color_assignments")
    author_profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="authored_color_assignments"
    )
    combination = models.ForeignKey(
        "colors.ColorCombination", on_delete=models.PROTECT, related_name="color_assignments"
    )
    source = models.CharField(_("source"), max_length=20, choices=Source.choices)
    # FR-P5/D-07: nur gesetzt, wenn source == SELF_TEST; Grundlage für
    # eine spätere Kennzeichnung "durch Test bestätigt". `SET_NULL`
    # statt `PROTECT`/`CASCADE`: das Löschen des referenzierten
    # Testergebnisses (FR-P8) leert nur die Referenz, die Farben
    # selbst bleiben bestehen.
    test_result = models.ForeignKey(
        "quiz.TestResult",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="color_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile"], name="unique_color_assignment_per_profile"),
        ]

    def __str__(self):
        return f"{self.profile} -> {self.combination}"
