"""Formular zum Ausfüllen des Fragebogens (Task 2.8, FR-T2, FR-T7 bis FR-T9)."""

from django import forms
from django.utils.translation import gettext_lazy as _


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
    Ein Pflichtfeld je Frage. `required=True` (Django-Default) erzwingt
    FR-T9 ("alle Fragen müssen beantwortet sein") serverseitig UND —
    über das native `required`-Attribut von `RadioSelect` — schon im
    Browser, ganz ohne eigenes JavaScript (`empty_label=None`: keine
    unbeantwortbare Leerauswahl).

    Bei einer unvollständigen Abgabe zeigt Django die bereits
    gewählten Antworten unverändert wieder an (`BoundField` liest aus
    den übermittelten POST-Daten) — "Antworten bleiben erhalten"
    (Roadmap 2.8) ist damit der Normalfall, nicht extra zu bauen.
    """

    def __init__(self, *args, questions, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            self.fields[self.field_name(question)] = AnswerChoiceField(
                queryset=question.answer_options.order_by("color"),
                label=question.text,
                widget=forms.RadioSelect,
                empty_label=None,
                error_messages={"required": _("Please choose an answer for every question.")},
            )

    @staticmethod
    def field_name(question):
        return f"question_{question.pk}"
