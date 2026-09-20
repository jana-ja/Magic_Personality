"""
Views der Quiz-App: Test durchführen (Task 2.8, FR-T7 bis FR-T9),
Ergebnis anzeigen und übernehmen (Task 2.10, FR-T13/FR-T14), Ergebnis
ohne Anmeldung (Task 2.11, FR-T15/FR-T16), Feedback (Task 4.11, FR-T18).
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.color_assignments import adopt_test_result
from apps.accounts.models import Profile
from apps.colors.content import LOCALE
from apps.core.models import FeedbackAttempt
from apps.core.rate_limit import client_ip, is_rate_limited, record_attempt

from . import anonymous_result
from .evaluation import evaluate_combination
from .forms import FeedbackForm, TakeTestForm
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
                "feedback_form": FeedbackForm(
                    initial={"questionnaire_version": questionnaire.version}
                ),
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
    adopt_test_result(test_result)
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
        # Ohne das Formular zeigte result.html ein leeres, unbenutzbares Feedback-Feld.
        "feedback_form": FeedbackForm(initial={"questionnaire_version": questionnaire_version}),
    }
    return render(request, "quiz/result.html", context)


@require_http_methods(["GET", "POST"])
def feedback(request):
    """
    Feedback zum Test (Task 4.11, FR-T18, D-75). Bewusst kein
    `@login_required` und kein Verweis auf den Account: auch wer den
    Test ohne Login gemacht hat, soll Feedback geben können (D-18),
    und anonym bleibt es ehrlicher.

    Zwei Wege zum selben Ergebnis: mit HTMX (Ergebnisseite) tauscht der
    Server nur den Formularbereich aus, denn die Ergebnisseite ist die
    Antwort auf ein POST und lässt sich nicht neu laden; ohne JavaScript
    ist es ein normales POST mit Weiterleitung auf die Dankeseite.

    Das Rate Limit steht hier statt im Decorator `rate_limit()`: dessen
    Klartext-429 würde HTMX nicht austauschen, die Person sähe nach dem
    Absenden schlicht nichts. Gezählt wird wie dort jede Absendung,
    auch die abgelehnte, damit das Zeitfenster weiterläuft.
    """
    is_htmx = request.headers.get("HX-Request") == "true"
    form = FeedbackForm(request.POST or None)
    status = 200

    if request.method == "POST":
        ip = client_ip(request)
        limited = is_rate_limited(
            FeedbackAttempt,
            ip,
            max_attempts=settings.FEEDBACK_RATE_LIMIT_MAX_ATTEMPTS,
            window_seconds=settings.FEEDBACK_RATE_LIMIT_WINDOW_SECONDS,
        )
        record_attempt(FeedbackAttempt, ip)
        if limited:
            form.add_error(None, _("Too many attempts. Please try again later."))
            # HTMX tauscht 4xx-Antworten nicht aus (siehe oben).
            status = 200 if is_htmx else 429
        elif form.is_valid():
            form.save()
            if is_htmx:
                return render(request, "quiz/_feedback_body.html", {"sent": True})
            return redirect("quiz:feedback_thanks")

    template = "quiz/_feedback_body.html" if is_htmx else "quiz/feedback.html"
    return render(request, template, {"form": form}, status=status)


def feedback_thanks(request):
    return render(request, "quiz/feedback.html", {"sent": True})
