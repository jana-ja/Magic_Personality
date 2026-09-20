"""
Formulare der Quiz-App: Fragebogen (Task 2.8, FR-T2, FR-T7 bis FR-T9, D-65)
und Feedback (Task 4.11, FR-T18).
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Feedback, Questionnaire


class AnswerChoiceField(forms.ModelChoiceField):
    """
    Zeigt als Label nur den Antworttext, nie `AnswerOption.__str__`
    (das nennt den Farbcode, siehe apps/quiz/models.py) — FR-T2: die
    Zuordnung Antwort -> Farbe darf für Testende nicht offensichtlich
    benannt sein.
    """

    def label_from_instance(self, answer_option):
        return answer_option.text


class TakeTestForm(forms.Form):
    """
    Ein Pflichtfeld je Frage und Rang (D-65): `choice_points=[1]` (v1)
    ergibt ein Feld je Frage, `[2, 1]` (v2) zwei — "passt am besten"
    und "passt am zweitbesten". `required=True` (Django-Default)
    erzwingt FR-T9 ("alle Fragen müssen beantwortet sein") serverseitig
    UND — über das native `required`-Attribut von `RadioSelect` — schon
    im Browser, ganz ohne eigenes JavaScript (`empty_label=None`: keine
    unbeantwortbare Leerauswahl).

    Bei einer unvollständigen Abgabe zeigt Django die bereits
    gewählten Antworten unverändert wieder an (`BoundField` liest aus
    den übermittelten POST-Daten) — "Antworten bleiben erhalten"
    (Roadmap 2.8) ist damit der Normalfall, nicht extra zu bauen.
    """

    def __init__(self, *args, questions, choice_points, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = questions
        self.choice_points = choice_points
        for question in questions:
            for rank in range(len(choice_points)):
                self.fields[self.field_name(question, rank)] = AnswerChoiceField(
                    queryset=question.answer_options.all(),
                    label=question.text,
                    widget=forms.RadioSelect,
                    empty_label=None,
                    error_messages={"required": _("Please choose an answer for every question.")},
                )

    @staticmethod
    def field_name(question, rank=0):
        # Rang 0 behält den Namen aus v1, damit dessen Formular unverändert bleibt.
        return f"question_{question.pk}" if rank == 0 else f"question_{question.pk}_{rank + 1}"

    def clean(self):
        cleaned_data = super().clean()
        for question in self.questions:
            names = [self.field_name(question, rank) for rank in range(len(self.choice_points))]
            chosen = [cleaned_data[name] for name in names if name in cleaned_data]
            if len(chosen) != len({answer.pk for answer in chosen}):
                self.add_error(names[-1], _("Please choose a different answer for each place."))
        return cleaned_data

    def weighted_answers(self):
        """`(AnswerOption, Punkte)` je gewählter Antwort — Eingabe für
        `scoring.tally()`. Nur nach erfolgreichem `is_valid()` aufrufen."""
        return [
            (self.cleaned_data[self.field_name(question, rank)], points)
            for question in self.questions
            for rank, points in enumerate(self.choice_points)
        ]


class FeedbackForm(forms.Form):
    """
    Feedback zum Test (Task 4.11, FR-T18, D-75): eine optionale Bewertung
    von 1 bis 5 und ein optionaler Freitext — mindestens eines von beiden.

    `questionnaire_version` kommt als verstecktes Feld von der
    Ergebnisseite. Es ist Nutzereingabe wie alles andere: eine Nummer,
    die keine veröffentlichte Version ist, wird zu „keine Angabe" statt
    zu einem Fehler — wer es fälscht, verfälscht nur sein eigenes
    Feedback, und ein Fehler zu einem unsichtbaren Feld hülfe niemandem.
    """

    RATING_CHOICES = [(str(value), str(value)) for value in range(1, 6)]

    rating = forms.TypedChoiceField(
        label=_("How well does your result fit you?"),
        choices=RATING_CHOICES,
        coerce=int,
        empty_value=None,
        required=False,
        widget=forms.RadioSelect,
    )
    message = forms.CharField(
        label=_("Anything else you would like to tell us?"),
        max_length=Feedback.MAX_MESSAGE_LENGTH,
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    questionnaire_version = forms.IntegerField(
        min_value=1, required=False, widget=forms.HiddenInput
    )

    def clean_message(self):
        return self.cleaned_data["message"].strip()

    def clean_questionnaire_version(self):
        version = self.cleaned_data["questionnaire_version"]
        if version is None:
            return None
        published = Questionnaire.objects.filter(version=version, published_at__isnull=False)
        return version if published.exists() else None

    def clean(self):
        cleaned_data = super().clean()
        # Fehlt ein Feld schon wegen eines eigenen Fehlers (z. B. zu langer
        # Text), gibt es dazu bereits eine Meldung — nicht noch eine zweite.
        if not self.errors and not cleaned_data.get("rating") and not cleaned_data.get("message"):
            raise forms.ValidationError(_("Please choose a rating or write a message."))
        return cleaned_data

    def save(self):
        """Nur nach erfolgreichem `is_valid()` aufrufen."""
        return Feedback.objects.create(**self.cleaned_data)
