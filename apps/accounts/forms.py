"""Formulare der Accounts-App: Registrierung (Task 2.2)."""

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import Profile, User


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
        if Profile.objects.filter(nickname__iexact=nickname).exists():
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
