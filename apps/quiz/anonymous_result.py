"""
Anonymes Testergebnis im Browser zwischenspeichern (Task 2.11, FR-T15/
FR-T16, D-18).

Kein serverseitiger Zustand für Nicht-Angemeldete (D-18) — stattdessen
ein von Django signiertes Token, das der Browser in `localStorage`
hält (`static/js/quiz_claim.js`) und nach Login/Registrierung an
`/quiz/results/claim/` zurückschickt. Dieselbe Technik wie das
Gate-Cookie (`apps.core.gate`, Task 0.5): `django.core.signing`
verhindert Manipulation über die Signatur, `max_age` verhindert das
Einlösen veralteter Daten (beides: Roadmap 2.11, "serverseitig
abgewiesen, nicht übernommen").
"""

from django.conf import settings
from django.core import signing

from apps.colors.models import Color


def sign(*, questionnaire_version, scores):
    return signing.dumps(
        {"questionnaire_version": questionnaire_version, "scores": scores},
        salt=settings.QUIZ_ANONYMOUS_RESULT_SALT,
    )


def unsign(token):
    """
    Gibt `(questionnaire_version, scores)` zurück, oder `None`, wenn
    das Token fehlt, manipuliert, abgelaufen oder anderweitig
    ungültig ist.
    """
    try:
        payload = signing.loads(
            token,
            salt=settings.QUIZ_ANONYMOUS_RESULT_SALT,
            max_age=settings.QUIZ_ANONYMOUS_RESULT_MAX_AGE,
        )
    except signing.BadSignature:
        return None

    if not isinstance(payload, dict):
        return None

    version = payload.get("questionnaire_version")
    scores = payload.get("scores")
    if not isinstance(version, int):
        return None
    if not _is_valid_scores(scores):
        return None
    return version, scores


def _is_valid_scores(scores):
    if not isinstance(scores, dict):
        return False
    expected_codes = {code for code, _label in Color.Code.choices}
    if set(scores.keys()) != expected_codes:
        return False
    return all(isinstance(value, int) and value >= 0 for value in scores.values())
