"""
Views der Quiz-App: Test durchführen (Task 2.8, FR-T7 bis FR-T9),
Ergebnis anzeigen und übernehmen (Task 2.10, FR-T13/FR-T14), Ergebnis
ohne Anmeldung (Task 2.11, FR-T15/FR-T16).
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.models import ColorAssignment, Profile
from apps.colors.content import LOCALE
from apps.colors.models import ColorCombination

from . import anonymous_result
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

    form_kwargs = {"questions": questions, "choice_points": questionnaire.choice_points}
    if request.method == "POST":
        form = TakeTestForm(request.POST, **form_kwargs)
        if form.is_valid():
            scores = tally(form.weighted_answers())
            combination = evaluate_combination(scores, threshold=questionnaire.result_threshold)

            # FR-T14: nur eingeloggt landet das Ergebnis automatisch in
            # der Historie. Ohne Login bewusst kein TestResult (D-18);
            # dieselbe Zurückhaltung gilt für einen Account ohne Profil
            # (z. B. ein per createsuperuser angelegter Admin).
            profile = (
                Profile.objects.filter(user=request.user).first()
                if request.user.is_authenticated
                else None
            )
            test_result = None
            token = None
            if profile is not None:
                test_result = TestResult.objects.create(
                    profile=profile,
                    questionnaire_version=questionnaire.version,
                    scores=scores,
                    result_colors=combination.code,
                )
            elif not request.user.is_authenticated:
                # FR-T15/D-18: kein serverseitiger Zustand für
                # Nicht-Angemeldete — stattdessen ein signiertes Token,
                # das der Browser selbst in localStorage hält
                # (static/js/quiz_claim.js) und nach Login/Registrierung
                # an claim_anonymous_result() zurückschickt.
                token = anonymous_result.sign(
                    questionnaire_version=questionnaire.version, scores=scores
                )

            context = {
                "combination": combination,
                "combination_url": reverse(
                    "colors:combination", kwargs={"code": combination.code.lower()}
                ),
                "scores": scores,
                "test_result": test_result,
                "anonymous_token": token,
            }
            return render(request, "quiz/result.html", context)
    else:
        form = TakeTestForm(**form_kwargs)

    return render(
        request,
        "quiz/take_test.html",
        {
            "form": form,
            "questions": _question_rows(form, questions),
            "ranked": len(questionnaire.choice_points) > 1,
        },
    )


def _question_rows(form, questions):
    """
    Für das Template: je Frage die Felder aller Ränge und — für die
    Matrix-Darstellung in v2 (D-65) — je Antwort eine Zeile mit den
    Radio-Buttons aller Ränge nebeneinander. Die Radio-Buttons eines
    Feldes kommen in derselben Reihenfolge wie `answer_options`
    (`AnswerOption.position`), deshalb lassen sie sich zeilenweise
    zusammenlegen.
    """
    ranks = len(form.choice_points)
    result = []
    for question in questions:
        fields = [form[TakeTestForm.field_name(question, rank)] for rank in range(ranks)]
        rows = [
            {"label": radios[0].choice_label, "radios": radios}
            for radios in zip(*(list(field) for field in fields), strict=True)
        ]
        errors = [error for field in fields for error in field.errors]
        result.append(
            {
                "question": question,
                "fields": fields,
                "rows": rows,
                "errors": list(dict.fromkeys(errors)),
            }
        )
    return result


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
    # Auswertungsregel oder `result_threshold` könnten sich seither
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
    return redirect(test_result.profile)


@login_required
@require_POST
def claim_anonymous_result(request):
    """
    FR-T16: ein im Browser zwischengespeichertes anonymes Ergebnis wird
    nach Login oder Registrierung wie ein frisches, eingeloggtes
    Ergebnis behandelt (FR-T14) — Historie plus Angebot zur Übernahme,
    über dieselbe Ergebnisseite wie `take_test()`. Fehlende,
    manipulierte oder abgelaufene Daten werden ohne Fehlermeldung
    verworfen (Roadmap 2.11) — `anonymous_result.unsign()` gibt dafür
    `None` zurück, es landet dann einfach niemand auf einer neuen Seite.
    """
    unsigned = anonymous_result.unsign(request.POST.get("token", ""))
    profile = Profile.objects.filter(user=request.user).first()
    if unsigned is None or profile is None:
        return redirect(settings.LOGIN_REDIRECT_URL)

    questionnaire_version, scores = unsigned
    # Das Token wird mit dem `T` seiner eigenen Version ausgewertet
    # (D-65) — auch wenn inzwischen eine neuere Version aktuell ist.
    questionnaire = Questionnaire.objects.filter(version=questionnaire_version).first()
    if questionnaire is None:
        return redirect(settings.LOGIN_REDIRECT_URL)
    combination = evaluate_combination(scores, threshold=questionnaire.result_threshold)
    test_result = TestResult.objects.create(
        profile=profile,
        questionnaire_version=questionnaire_version,
        scores=scores,
        result_colors=combination.code,
    )

    context = {
        "combination": combination,
        "combination_url": reverse("colors:combination", kwargs={"code": combination.code.lower()}),
        "scores": scores,
        "test_result": test_result,
        "anonymous_token": None,
    }
    return render(request, "quiz/result.html", context)
