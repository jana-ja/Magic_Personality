"""Views der Quiz-App: Test durchführen (Task 2.8, FR-T7 bis FR-T9)."""

from django.http import Http404
from django.shortcuts import render

from apps.colors.content import LOCALE

from .forms import TakeTestForm
from .models import Questionnaire
from .scoring import tally


def _current_questionnaire():
    """Die neueste veröffentlichte Version (FR-T6: ein Entwurf ist noch
    nicht zum Testen gedacht, siehe Task 2.6s Seed-Command)."""
    return Questionnaire.objects.filter(published_at__isnull=False).order_by("-version").first()


def take_test(request):
    """
    FR-T7/FR-T8: alle Fragen stehen auf einer einzigen Seite in einem
    einzigen Formular — kein mehrschrittiger Assistent mit Server-
    Zwischenstand. Freies Vor- und Zurückspringen ist dadurch der
    Normalfall (man scrollt einfach dorthin), nicht extra zu bauen.
    Bewusst kein `@login_required`: "auch ohne Login durchführbar"
    (Roadmap 2.8) — die Zugangssperre (Task 0.5) gilt unabhängig davon
    für jede URL dieser Anwendung.
    """
    questionnaire = _current_questionnaire()
    if questionnaire is None:
        raise Http404("No published questionnaire available yet.")

    questions = list(
        questionnaire.questions.filter(locale=LOCALE)
        .order_by("position")
        .prefetch_related("answer_options")
    )

    if request.method == "POST":
        form = TakeTestForm(request.POST, questions=questions)
        if form.is_valid():
            # Die eigentliche Auswertungsregel (FR-T10 bis FR-T12) ist
            # Task 2.9 — bis dahin zeigt diese Seite nur die rohen
            # Punkte je Farbe, ähnlich der Datenschutz-Platzhalterseite
            # aus Task 1.11.
            scores = tally(form.cleaned_data.values())
            return render(request, "quiz/result_placeholder.html", {"scores": scores})
    else:
        form = TakeTestForm(questions=questions)

    fields = [(question, form[TakeTestForm.field_name(question)]) for question in questions]
    return render(request, "quiz/take_test.html", {"form": form, "fields": fields})
