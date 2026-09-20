"""
Tests für das Feedback zum Test (Task 4.11, FR-T18, D-75).

Nutzt `published_questionnaire` (conftest.py). Das Formular ist ohne
Login benutzbar und speichert nichts, was auf eine Person zeigt.
"""

import pytest
from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models import Profile, User
from apps.core.models import FeedbackAttempt
from apps.quiz.models import Feedback, Questionnaire

pytestmark = pytest.mark.django_db

FEEDBACK_URL = "/feedback/"
HTMX = {"HTTP_HX_REQUEST": "true"}


def _post(client, data, **extra):
    return client.post(FEEDBACK_URL, data, **extra)


# Erreichbarkeit ------------------------------------------------------------


def test_feedback_page_is_available_without_login(gated_client):
    response = gated_client.get(FEEDBACK_URL)

    assert response.status_code == 200
    html = response.content.decode()
    assert 'name="rating"' in html
    assert 'name="message"' in html
    assert "not linked to your account" in html


def test_feedback_page_is_available_with_login(gated_client):
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    gated_client.force_login(user)

    assert gated_client.get(FEEDBACK_URL).status_code == 200


def test_feedback_urls_without_gate_cookie_redirect_to_the_gate(client):
    for path in (FEEDBACK_URL, "/feedback/thanks/"):
        response = client.get(path)

        assert response.status_code == 302
        assert response.url.startswith("/gate/")


def test_every_page_links_to_feedback_from_the_footer(gated_client):
    html = gated_client.get("/colors/").content.decode()

    assert 'href="/feedback/"' in html


def test_result_page_embeds_the_form_with_the_questionnaire_version(
    gated_client, published_questionnaire
):
    questions = list(published_questionnaire.questions.all())
    data = {f"question_{q.pk}": q.answer_options.first().pk for q in questions}

    html = gated_client.post("/quiz/", data).content.decode()

    assert 'name="rating"' in html
    assert f'name="questionnaire_version" value="{published_questionnaire.version}"' in html
    assert f'hx-post="{FEEDBACK_URL}"' in html


def test_the_result_page_after_claiming_a_saved_result_also_has_the_working_form(
    gated_client, published_questionnaire
):
    """Regression: `claim_anonymous_result` rendert dieselbe Ergebnisseite, gab dem
    Feedback-Bereich aber kein Formular mit — es erschien nur der Rahmen ohne
    Felder und ohne Beschriftungen."""
    from apps.accounts.models import Profile, User
    from apps.quiz import anonymous_result

    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    token = anonymous_result.sign(
        questionnaire_version=published_questionnaire.version,
        scores={"W": 3, "U": 1, "B": 1, "R": 1, "G": 1},
    )
    gated_client.force_login(user)

    html = gated_client.post("/quiz/results/claim/", {"token": token}).content.decode()

    assert 'name="rating"' in html
    assert 'name="message"' in html
    assert f'name="questionnaire_version" value="{published_questionnaire.version}"' in html
    assert "How well does your result fit you?" in html


# Speichern -----------------------------------------------------------------


def test_rating_alone_is_enough(gated_client):
    response = _post(gated_client, {"rating": "4"})

    assert response.status_code == 302
    assert response.url == "/feedback/thanks/"
    feedback = Feedback.objects.get()
    assert feedback.rating == 4
    assert feedback.message == ""


def test_message_alone_is_enough_and_is_trimmed(gated_client):
    _post(gated_client, {"message": "  Too many questions.  "})

    feedback = Feedback.objects.get()
    assert feedback.rating is None
    assert feedback.message == "Too many questions."


def test_feedback_stores_nothing_that_points_to_a_person(gated_client):
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    gated_client.force_login(user)

    _post(gated_client, {"rating": "5", "message": "Nice."})

    field_names = {field.name for field in Feedback._meta.get_fields()}
    assert field_names == {"id", "rating", "message", "questionnaire_version", "created_at"}


def test_thanks_page_shows_the_thanks(gated_client):
    html = gated_client.get("/feedback/thanks/").content.decode()

    assert "Thank you" in html
    assert 'name="rating"' not in html


# Ungültige Eingaben --------------------------------------------------------


def test_empty_submission_is_rejected(gated_client):
    response = _post(gated_client, {"rating": "", "message": "   "})

    assert response.status_code == 200
    assert "Please choose a rating or write a message." in response.content.decode()
    assert Feedback.objects.count() == 0


@pytest.mark.parametrize("rating", ["0", "6", "-1", "abc"])
def test_rating_outside_one_to_five_is_rejected(gated_client, rating):
    response = _post(gated_client, {"rating": rating, "message": "x"})

    assert response.status_code == 200
    assert Feedback.objects.count() == 0


def test_too_long_message_is_rejected(gated_client):
    response = _post(gated_client, {"message": "x" * (Feedback.MAX_MESSAGE_LENGTH + 1)})

    assert response.status_code == 200
    assert Feedback.objects.count() == 0


def test_message_at_the_limit_is_accepted(gated_client):
    _post(gated_client, {"message": "x" * Feedback.MAX_MESSAGE_LENGTH})

    assert Feedback.objects.count() == 1


def test_a_rejected_message_is_shown_again_escaped(gated_client):
    response = _post(gated_client, {"rating": "9", "message": "<script>alert(1)</script>"})

    html = response.content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_get_only_and_post_only_methods(gated_client):
    assert gated_client.put(FEEDBACK_URL).status_code == 405


# Fragebogen-Version ---------------------------------------------------------


def test_published_questionnaire_version_is_kept(gated_client, published_questionnaire):
    _post(gated_client, {"rating": "3", "questionnaire_version": published_questionnaire.version})

    assert Feedback.objects.get().questionnaire_version == published_questionnaire.version


def test_unknown_or_unpublished_version_becomes_no_answer(gated_client, published_questionnaire):
    Questionnaire.objects.create(version=7, question_count=1)  # nie veröffentlicht

    for version in ("999", "7"):
        _post(gated_client, {"rating": "3", "questionnaire_version": version})

    assert list(Feedback.objects.values_list("questionnaire_version", flat=True)) == [None, None]


def test_garbage_version_is_rejected_like_any_other_bad_field(gated_client):
    response = _post(gated_client, {"rating": "3", "questionnaire_version": "abc"})

    assert response.status_code == 200
    assert Feedback.objects.count() == 0


# HTMX ----------------------------------------------------------------------


def test_htmx_success_returns_only_the_thanks_fragment(gated_client):
    response = _post(gated_client, {"rating": "5"}, **HTMX)

    assert response.status_code == 200
    html = response.content.decode()
    assert "Thank you" in html
    assert "<html" not in html
    assert Feedback.objects.count() == 1


def test_htmx_error_returns_only_the_form_fragment_with_the_message(gated_client):
    response = _post(gated_client, {"rating": "", "message": ""}, **HTMX)

    assert response.status_code == 200
    html = response.content.decode()
    assert "<html" not in html
    assert 'name="rating"' in html
    assert "Please choose a rating or write a message." in html
    assert Feedback.objects.count() == 0


# Rate Limit ------------------------------------------------------------------


def _use_up_the_limit(client):
    for _attempt in range(settings.FEEDBACK_RATE_LIMIT_MAX_ATTEMPTS):
        assert _post(client, {"rating": "3"}).status_code == 302


def test_submissions_beyond_the_limit_are_refused_and_not_stored(gated_client):
    _use_up_the_limit(gated_client)

    response = _post(gated_client, {"rating": "3"})

    assert response.status_code == 429
    assert "Too many attempts" in response.content.decode()
    assert Feedback.objects.count() == settings.FEEDBACK_RATE_LIMIT_MAX_ATTEMPTS


def test_rate_limit_message_reaches_the_person_with_htmx(gated_client):
    """HTMX tauscht 4xx nicht aus — die Meldung muss trotzdem sichtbar sein."""
    _use_up_the_limit(gated_client)

    response = _post(gated_client, {"rating": "3"}, **HTMX)

    assert response.status_code == 200
    assert "Too many attempts" in response.content.decode()
    assert Feedback.objects.count() == settings.FEEDBACK_RATE_LIMIT_MAX_ATTEMPTS


def test_rejected_submissions_count_too(gated_client):
    for _attempt in range(3):
        _post(gated_client, {"rating": ""})

    assert FeedbackAttempt.objects.count() == 3


def test_old_attempts_do_not_count(gated_client):
    _use_up_the_limit(gated_client)
    long_ago = timezone.now() - timezone.timedelta(
        seconds=settings.FEEDBACK_RATE_LIMIT_WINDOW_SECONDS + 60
    )
    FeedbackAttempt.objects.update(created_at=long_ago)

    assert _post(gated_client, {"rating": "3"}).status_code == 302


def test_get_requests_are_not_counted(gated_client):
    for _attempt in range(settings.FEEDBACK_RATE_LIMIT_MAX_ATTEMPTS + 2):
        gated_client.get(FEEDBACK_URL)

    assert FeedbackAttempt.objects.count() == 0


# Datenbank-Regeln ----------------------------------------------------------


@pytest.mark.parametrize("rating", [0, 6])
def test_database_refuses_a_rating_outside_one_to_five(rating):
    with pytest.raises(IntegrityError):
        Feedback.objects.create(rating=rating, message="x")


def test_database_refuses_feedback_without_rating_and_message():
    with pytest.raises(IntegrityError):
        Feedback.objects.create(rating=None, message="")
