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
