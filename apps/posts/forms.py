"""Formulare der Posts-App: Beitrag schreiben und bearbeiten (Task 5.3, FR-B1 bis FR-B4),
Melden (Task 5.7, FR-B10) und Kommentieren (Task 6.2, FR-B13, FR-B15)."""

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.colors.models import Color
from apps.colors.utils import canonical_code

from .models import BODY_MAX_LENGTH, COMMENT_MAX_LENGTH, TITLE_MAX_LENGTH, Post, Report


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


class ReportForm(forms.Form):
    """Der optionale Grund einer Meldung (FR-B10): höchstens 500 Zeichen."""

    reason = forms.CharField(
        label=_("Why are you reporting this? (optional)"),
        required=False,
        max_length=Report.MAX_REASON_LENGTH,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean_reason(self):
        # Browser schicken CRLF; gespeichert wird LF, gezählt nach dem Normalisieren.
        return self.cleaned_data["reason"].replace("\r\n", "\n").replace("\r", "\n")


class CommentForm(forms.Form):
    """
    Text eines Kommentars (FR-B13): Klartext, höchstens 2000 Zeichen, Pflicht
    (anders als beim Feedback gibt es hier kein „oder" — ein Kommentar ohne
    Text wäre nichts).

    `reply_to` trägt, falls gesetzt, die **Nummer** des Kommentars, auf den
    geantwortet wird — dieselbe Zahl, die in der Adresse steht (`?reply=3`)
    und die Person sieht, nicht die interne ID. Der View löst sie zu einer
    `Comment`-Instanz auf; ob der Bezug überhaupt gültig ist (derselbe
    Beitrag, keine Hülle), prüft `apps.posts.comments.create_comment()`
    (FR-B15) — das Feld selbst ist nur eine Zahl.
    """

    body = forms.CharField(
        label=_("Comment"),
        strip=False,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": COMMENT_MAX_LENGTH}),
    )
    # Kein `min_value`: eine unsinnige Zahl (0, negativ, erfunden) soll nicht
    # das ganze Formular ablehnen, sondern beim Auflösen im View einfach
    # keinen Treffer ergeben (wie bei `?colors=`, Task 5.6) — „kein Bezug"
    # statt eines für die Person unsichtbaren Formularfehlers.
    reply_to = forms.IntegerField(required=False, widget=forms.HiddenInput)

    def clean_body(self):
        body = self.cleaned_data["body"].replace("\r\n", "\n").replace("\r", "\n").strip("\n")
        if not body.strip():
            raise forms.ValidationError(self.fields["body"].error_messages["required"], "required")
        if len(body) > COMMENT_MAX_LENGTH:
            raise forms.ValidationError(
                _("Please keep the comment to %(max)d characters or fewer."),
                "max_length",
                params={"max": COMMENT_MAX_LENGTH},
            )
        return body
