"""Formulare der Accounts-App: Registrierung (Task 2.2), Profil (Task 2.4)."""

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.colors.content import LOCALE
from apps.colors.models import Color, ColorCombination
from apps.colors.utils import canonical_code

from .color_assignments import adopt_test_result
from .models import ColorAssignment, Profile, User


def _nickname_is_taken(nickname, *, exclude_profile=None):
    """FR-P2: global eindeutig, Groß-/Kleinschreibung egal (siehe auch
    Profile.Meta.constraints in models.py, der DB-seitige Teil davon)."""
    conflicts = Profile.objects.filter(nickname__iexact=nickname)
    if exclude_profile is not None:
        conflicts = conflicts.exclude(pk=exclude_profile.pk)
    return conflicts.exists()


def _validate_nickname_characters(nickname):
    """
    Der Nickname steht in der Adresse des Profils (`/u/<nickname>/`,
    Task 4.1): ein "/" ließe sich dort nicht abbilden und würde jede Seite
    mit dem Namen im Kopfbereich zum Absturz bringen; ein Name nur aus
    Punkten ("." oder "..") würde vom Browser als Pfadangabe aufgelöst.
    """
    if "/" in nickname or set(nickname) == {"."}:
        raise ValidationError(_("The nickname can't contain a slash or consist only of dots."))


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
        _validate_nickname_characters(nickname)
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


class NicknameForm(forms.Form):
    """
    Nickname ändern (Task 4.5, FR-P12, FR-P2). Eigenes Formular mit eigenem
    Endpunkt: speichert ausschließlich den Nickname und fasst weder Bio noch
    Farben an.
    """

    nickname = forms.CharField(
        label=_("Nickname"), max_length=50, widget=forms.TextInput(attrs={"autofocus": True})
    )

    def __init__(self, *args, profile, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)

    def clean_nickname(self):
        nickname = self.cleaned_data["nickname"].strip()
        _validate_nickname_characters(nickname)
        if _nickname_is_taken(nickname, exclude_profile=self.profile):
            raise ValidationError(_("This nickname is already taken."))
        return nickname

    def save(self):
        self.profile.nickname = self.cleaned_data["nickname"]
        self.profile.full_clean()
        self.profile.save(update_fields=["nickname"])


class BioForm(forms.Form):
    """Bio ändern (Task 4.5, FR-P12). Speichert ausschließlich die Bio."""

    bio = forms.CharField(
        label=_("Bio"), required=False, widget=forms.Textarea(attrs={"autofocus": True})
    )

    def __init__(self, *args, profile, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)

    def save(self):
        self.profile.bio = self.cleaned_data["bio"]
        self.profile.full_clean()
        self.profile.save(update_fields=["bio"])


class ColorsForm(forms.Form):
    """
    Farben ändern (Task 4.6, FR-P4, FR-P5, FR-P13). Eine Auswahl aus
    zwei Wegen: ein Testergebnis der eigenen Historie (`choice` = dessen
    Primärschlüssel) oder die manuelle Wahl von 1 bis 5 Farben (`choice` =
    `"manual"`). Fehlt `choice`, gilt `"manual"` — so bleibt das alte
    Abschicken nur mit Farben gültig.

    `colors` sind fünf Kontrollkästchen; das Fünfeck im Profil ist nur eine
    Bedienhilfe darüber (templates/social/_color_field.html, Task 4.6) und
    schickt dieselben Felder ab.
    """

    MANUAL = "manual"

    choice = forms.CharField(required=False)
    colors = forms.MultipleChoiceField(
        label=_("Colors"),
        required=False,
        choices=Color.Code.choices,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, profile, **kwargs):
        self.profile = profile
        self.test_result = None
        super().__init__(*args, **kwargs)

    def clean_choice(self):
        choice = self.cleaned_data["choice"].strip() or self.MANUAL
        if choice == self.MANUAL:
            return choice
        # Nur Einträge der eigenen Historie: `profile.test_results` ist die
        # Grenze, ein fremder Primärschlüssel ist hier schlicht ungültig.
        if not choice.isdigit():
            raise ValidationError(_("Choose one of your test results or pick the colors yourself."))
        self.test_result = self.profile.test_results.filter(pk=int(choice)).first()
        if self.test_result is None:
            raise ValidationError(_("Choose one of your test results or pick the colors yourself."))
        return choice

    def save(self):
        if self.test_result is not None:
            adopt_test_result(self.test_result)
            return

        # Nur anfassen, was sich tatsächlich geändert hat (D-72): ein
        # unverändert abgeschicktes Formular darf die Testreferenz nicht
        # überschreiben (FR-P5).
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
