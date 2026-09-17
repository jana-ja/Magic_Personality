"""
Views der Quiz-App: Test durchführen (Task 2.8, FR-T7 bis FR-T9),
Ergebnis anzeigen und übernehmen (Task 2.10, FR-T13/FR-T14).
"""

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.models import ColorAssignment, Profile
from apps.colors.content import LOCALE
from apps.colors.models import ColorCombination

from .evaluation import evaluate_combination
from .forms import TakeTestForm
from .models import Questionnaire, TestResult
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
            scores = tally(form.cleaned_data.values())
            combination = evaluate_combination(scores)

            # FR-T14: nur eingeloggt landet das Ergebnis automatisch in
            # der Historie. Ohne Login bewusst kein TestResult (D-18 —
            # Task 2.11 hält es stattdessen im localStorage); dieselbe
            # Zurückhaltung gilt für einen Account ohne Profil (z. B.
            # ein per createsuperuser angelegter Admin).
            profile = (
                Profile.objects.filter(user=request.user).first()
                if request.user.is_authenticated
                else None
            )
            test_result = None
            if profile is not None:
                test_result = TestResult.objects.create(
                    profile=profile,
                    questionnaire_version=questionnaire.version,
                    scores=scores,
                    result_colors=combination.code,
                )

            context = {
                "combination": combination,
                "combination_url": reverse(
                    "colors:combination", kwargs={"code": combination.code.lower()}
                ),
                "scores": scores,
                "test_result": test_result,
            }
            return render(request, "quiz/result.html", context)
    else:
        form = TakeTestForm(questions=questions)

    fields = [(question, form[TakeTestForm.field_name(question)]) for question in questions]
    return render(request, "quiz/take_test.html", {"form": form, "fields": fields})


@login_required
@require_POST
def adopt_result(request, pk):
    """
    FR-T14: die Übernahme ins Profil ist ein **Angebot**, kein
    automatischer Schritt — dieser eigene POST setzt
    `source = SELF_TEST` und die Testreferenz (FR-P5, D-07), erst
    wenn die Person das ausdrücklich anstößt.
    """
    test_result = get_object_or_404(TestResult, pk=pk, profile__user=request.user)
    # Nicht evaluate_combination(test_result.scores) neu berechnen: die
    # Auswertungsregel oder QUIZ_RESULT_THRESHOLD könnten sich seither
    # geändert haben — result_colors ist das Ergebnis, das zum
    # Testzeitpunkt tatsächlich angezeigt wurde (FR-T14 übernimmt
    # *dieses* Ergebnis, kein neu berechnetes).
    combination = ColorCombination.objects.get(code=test_result.result_colors, locale=LOCALE)

    ColorAssignment.objects.update_or_create(
        profile=test_result.profile,
        defaults={
            "author_profile": test_result.profile,
            "combination": combination,
            "source": ColorAssignment.Source.SELF_TEST,
            "test_result": test_result,
        },
    )
    return redirect("profile")
