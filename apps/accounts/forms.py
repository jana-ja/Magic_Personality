"""Formulare der Accounts-App: Registrierung (Task 2.2), Profil (Task 2.4)."""

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.colors.content import LOCALE
from apps.colors.models import Color, ColorCombination
from apps.colors.utils import canonical_code

from .models import ColorAssignment, Profile, User


def _nickname_is_taken(nickname, *, exclude_profile=None):
    """FR-P2: global eindeutig, Groß-/Kleinschreibung egal (siehe auch
    Profile.Meta.constraints in models.py, der DB-seitige Teil davon)."""
    conflicts = Profile.objects.filter(nickname__iexact=nickname)
    if exclude_profile is not None:
        conflicts = conflicts.exclude(pk=exclude_profile.pk)
    return conflicts.exists()


class RegistrationForm(forms.Form):
    """
    FR-U1/FR-U3: E-Mail, Passwort (Mindestlänge über
    AUTH_PASSWORD_VALIDATORS, config/settings/base.py) und der
    Nickname für das gemeinsam angelegte Profil (Task 2.1, FR-P1).
    """

    email = forms.EmailField(label=_("Email"), widget=forms.EmailInput(attrs={"autofocus": True}))
    nickname = forms.CharField(label=_("Nickname"), max_length=50)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(
        label=_("Password confirmation"), widget=forms.PasswordInput, strip=False
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("An account with this email address already exists."))
        return email

    def clean_nickname(self):
        nickname = self.cleaned_data["nickname"].strip()
        if _nickname_is_taken(nickname):
            raise ValidationError(_("This nickname is already taken."))
        return nickname

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", _("The two password fields didn’t match."))

        if password1:
            # UserAttributeSimilarityValidator vergleicht gegen die
            # E-Mail — dafür genügt eine unspeicherte Instanz, genau
            # wie Djangos eigenes UserCreationForm es macht.
            temp_user = User(email=cleaned_data.get("email", ""))
            try:
                validate_password(password1, user=temp_user)
            except ValidationError as error:
                self.add_error("password1", error)

        return cleaned_data

    def save(self):
        """Legt User und Profil gemeinsam an (Task 2.1/2.2, D-22)."""
        with transaction.atomic():
            user = User.objects.create_user(
                email=self.cleaned_data["email"], password=self.cleaned_data["password1"]
            )
            profile = Profile.objects.create(user=user, nickname=self.cleaned_data["nickname"])
        return user, profile


class ProfileForm(forms.Form):
    """
    Bearbeitung des eigenen Profils (Task 2.4, FR-P1, FR-P4). Farben
    sind hier bewusst fünf einzelne Kontrollkästchen (W/U/B/R/G) statt
    einer Fünfeck-Auswahl wie in `apps.colors`: dort steuert die
    Selektion die URL und damit den angezeigten Content (D-24), hier
    geht es nur darum, eine der 31 Kombinationen zu speichern — hierfür
    ein zweites Fünfeck nachzubauen wäre unnötiger Aufwand.
    """

    nickname = forms.CharField(label=_("Nickname"), max_length=50)
    bio = forms.CharField(label=_("Bio"), required=False, widget=forms.Textarea)
    colors = forms.MultipleChoiceField(
        label=_("Colors"),
        required=False,
        choices=Color.Code.choices,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, profile, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)

    def clean_nickname(self):
        nickname = self.cleaned_data["nickname"].strip()
        if _nickname_is_taken(nickname, exclude_profile=self.profile):
            raise ValidationError(_("This nickname is already taken."))
        return nickname

    def save(self):
        self.profile.nickname = self.cleaned_data["nickname"]
        self.profile.bio = self.cleaned_data["bio"]
        self.profile.full_clean()
        self.profile.save()

        # Nur anfassen, was sich tatsächlich geändert hat: Das Formular
        # schickt immer alle Felder mit. Ohne diesen Vergleich setzte jedes
        # Speichern (z. B. nur die Bio geändert) die Farben auf SELF_MANUAL
        # und löschte die Testreferenz (FR-P5) — Punkte in fremden Profilen
        # (D-70) verschwanden, ohne dass die Person die Farben angefasst hat.
        colors = canonical_code(self.cleaned_data["colors"])
        current = ColorAssignment.objects.filter(profile=self.profile).select_related("combination")
        current = current.first()
        current_code = current.combination.code if current else ""
        if colors == current_code:
            return

        if colors:
            # FR-P5/D-07: geänderte freie Wahl setzt source = SELF_MANUAL und
            # leert die Testreferenz — unabhängig davon, wovon die
            # bisherige Zuordnung (falls vorhanden) stammte.
            combination = ColorCombination.objects.get(code=colors, locale=LOCALE)
            ColorAssignment.objects.update_or_create(
                profile=self.profile,
                defaults={
                    "author_profile": self.profile,
                    "combination": combination,
                    "source": ColorAssignment.Source.SELF_MANUAL,
                    "test_result": None,
                },
            )
        else:
            ColorAssignment.objects.filter(profile=self.profile).delete()
