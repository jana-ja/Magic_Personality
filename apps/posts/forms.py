"""Formular zum Schreiben und Bearbeiten eines Beitrags (Task 5.3, FR-B1 bis FR-B4)."""

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.colors.models import Color
from apps.colors.utils import canonical_code

from .models import BODY_MAX_LENGTH, TITLE_MAX_LENGTH, Post


class PostForm(forms.Form):
    """
    Titel, Text (Markdown) und optional eine Farbkombination (FR-B2).

    `colors` sind fünf Kontrollkästchen; das Fünfeck im Editor ist wie bei den
    Profilfarben nur eine Bedienhilfe darüber (`colors/_color_field.html`,
    D-74). Keines gewählt heißt „allgemeiner Beitrag". Die Autorin bzw. der
    Autor steht **nicht** im Formular: `save()` bekommt sie vom View, ein
    abgeschicktes `author` gäbe es nirgends zu missbrauchen.

    Für die Bearbeitung `post=` übergeben: das Formular startet mit den
    Werten des Beitrags, und `save()` fasst nur an, was sich tatsächlich
    geändert hat (wie D-72) — ein unverändert abgeschicktes Formular lässt
    `edited_at` in Ruhe.
    """

    title = forms.CharField(label=_("Title"), max_length=TITLE_MAX_LENGTH)
    body = forms.CharField(
        label=_("Text"),
        # Kein `strip`: eingerückter Code am Anfang bliebe sonst nicht erhalten.
        # Die Längenprüfung steht in `clean_body`, nach der Normalisierung der
        # Zeilenenden (Browser schicken CRLF, gespeichert wird LF).
        strip=False,
        widget=forms.Textarea(attrs={"rows": 10, "maxlength": BODY_MAX_LENGTH}),
    )
    colors = forms.MultipleChoiceField(
        label=_("Colors"),
        required=False,
        choices=Color.Code.choices,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, post=None, **kwargs):
        self.post = post
        if post is not None:
            kwargs.setdefault(
                "initial",
                {"title": post.title, "body": post.body, "colors": list(post.colors)},
            )
        super().__init__(*args, **kwargs)

    def clean_body(self):
        body = self.cleaned_data["body"].replace("\r\n", "\n").replace("\r", "\n").strip("\n")
        if not body.strip():
            raise forms.ValidationError(self.fields["body"].error_messages["required"], "required")
        if len(body) > BODY_MAX_LENGTH:
            raise forms.ValidationError(
                _("Please keep the text to %(max)d characters or fewer."),
                "max_length",
                params={"max": BODY_MAX_LENGTH},
            )
        return body

    def clean_colors(self):
        return canonical_code(self.cleaned_data["colors"])

    def save(self, author=None):
        """Nur nach erfolgreichem `is_valid()` aufrufen. Neu: `author` angeben."""
        data = self.cleaned_data
        if self.post is None:
            return Post.objects.create(
                author=author, title=data["title"], body=data["body"], colors=data["colors"]
            )

        fields = ("title", "body", "colors")
        changed = [name for name in fields if getattr(self.post, name) != data[name]]
        if changed:
            for name in changed:
                setattr(self.post, name, data[name])
            self.post.edited_at = timezone.now()
            self.post.save(update_fields=[*changed, "edited_at"])
        return self.post
