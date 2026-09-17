"""
manage.py seed_questionnaire — idempotenter Import einer Fragebogen-
Version aus seeds/questionnaire_v<version>.json (Task 2.6, D-28,
ARCHITECTURE.md §9).

Anders als `seed_content` (Task 1.3) muss dieser Command eine zweite
Regel durchsetzen, die das Modell allein nicht abbilden kann (FR-T6):
Fragen einer bereits **veröffentlichten** Version dürfen sich nicht
mehr ändern. Solange eine Version noch nicht veröffentlicht ist, bleibt
sie frei bearbeitbar — genau der Zustand, in dem Task 2.7 die 20 echten
Fragen erarbeitet, bevor sie freigegeben werden.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.quiz.models import AnswerOption, Question, Questionnaire

ALLOWED_TOP_LEVEL_KEYS = {"version", "locale", "published", "questions"}
ALLOWED_QUESTION_KEYS = {"position", "dimension", "text", "answers"}
ALLOWED_ANSWER_KEYS = {"color", "text"}


class Command(BaseCommand):
    help = (
        "Spielt eine Fragebogen-Version aus seeds/questionnaire_v<version>.json "
        "idempotent ein; veröffentlichte Versionen sind unveränderlich (FR-T6)."
    )

    def add_arguments(self, parser):
        # Nicht "--version"/dest="version": das kollidiert mit Djangos
        # eigener eingebauter Option gleichen Namens ("Show program's
        # version number and exit") — auch der `dest` muss sich
        # unterscheiden, sonst lehnt call_command() in Tests ab.
        parser.add_argument(
            "--questionnaire-version",
            dest="questionnaire_version",
            required=True,
            type=int,
            help="z. B. 1",
        )
        parser.add_argument("--locale", required=True, help='z. B. "en"')
        parser.add_argument(
            "--path",
            help=(
                "Pfad zur Seed-Datei. Default: "
                "seeds/questionnaire_v<version>.json. Vor allem für Tests."
            ),
        )

    def handle(self, *args, **options):
        version = options["questionnaire_version"]
        locale = options["locale"]
        path = (
            Path(options["path"])
            if options["path"]
            else Path(settings.BASE_DIR) / "seeds" / f"questionnaire_v{version}.json"
        )

        if not path.exists():
            raise CommandError(f"Seed-Datei nicht gefunden: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"{path} ist kein gültiges JSON: {exc}") from exc

        self._check_unknown_keys(data, ALLOWED_TOP_LEVEL_KEYS, "top level")

        if data.get("version") != version:
            raise CommandError(
                f"--version={version!r} passt nicht zum 'version'-Feld in der Datei "
                f"({data.get('version')!r})."
            )
        file_locale = data.get("locale")
        if file_locale != locale:
            raise CommandError(
                f"--locale={locale!r} passt nicht zum 'locale'-Feld in der Datei "
                f"({file_locale!r})."
            )

        questions = data.get("questions", [])
        publish_requested = bool(data.get("published", False))

        with transaction.atomic():
            questionnaire, _ = Questionnaire.objects.get_or_create(
                version=version, defaults={"question_count": 0}
            )
            # Vor jeder Änderung einfrieren, ob die Version bereits
            # veröffentlicht *war* — genau dieser Zustand entscheidet,
            # ob der folgende Import Änderungen vornehmen darf.
            was_published = questionnaire.is_published

            if was_published and not publish_requested:
                raise CommandError(
                    f"Version {version} ist bereits veröffentlicht und kann nicht "
                    "zurückgezogen werden. Änderungen brauchen eine neue Version (FR-T6)."
                )

            questions_written = 0
            answers_written = 0
            for question_entry in questions:
                answers_written += self._seed_question(
                    questionnaire, question_entry, locale, was_published
                )
                questions_written += 1

            questionnaire.question_count = len(questions)
            questionnaire.full_clean()
            questionnaire.save()

            if publish_requested and not was_published:
                questionnaire.published_at = timezone.now()
                questionnaire.save(update_fields=["published_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"v{version} ({locale}): {questions_written} Fragen, "
                f"{answers_written} Antworten verarbeitet."
                + (" Soeben veröffentlicht." if publish_requested and not was_published else "")
            )
        )

    def _seed_question(self, questionnaire, question_entry, locale, was_published):
        self._check_unknown_keys(question_entry, ALLOWED_QUESTION_KEYS, "question")

        position = question_entry.get("position")
        dimension = question_entry.get("dimension")
        text = question_entry.get("text")
        if not position or not dimension or not text:
            raise CommandError("Eine Frage braucht 'position', 'dimension' und 'text'.")
        where = f"question #{position}"

        existing = Question.objects.filter(
            questionnaire=questionnaire, position=position, locale=locale
        ).first()
        intended = {"text": text, "dimension": dimension}

        if was_published:
            self._reject_change(existing, intended, where)
            question = existing
        else:
            question, _ = Question.objects.update_or_create(
                questionnaire=questionnaire,
                position=position,
                locale=locale,
                defaults=intended,
            )
            self._full_clean_or_raise(question, where)

        answers_written = 0
        for answer_entry in question_entry.get("answers", []):
            self._seed_answer(question, answer_entry, was_published, where)
            answers_written += 1
        return answers_written

    def _seed_answer(self, question, answer_entry, was_published, where):
        self._check_unknown_keys(answer_entry, ALLOWED_ANSWER_KEYS, f"answer in {where}")

        color = answer_entry.get("color")
        text = answer_entry.get("text")
        if not color or not text:
            raise CommandError(f"Eine Antwort in {where} braucht 'color' und 'text'.")
        answer_where = f"answer {color!r} in {where}"

        if was_published:
            existing = AnswerOption.objects.filter(question=question, color=color).first()
            self._reject_change(existing, {"text": text}, answer_where)
            return

        answer, _ = AnswerOption.objects.update_or_create(
            question=question,
            color=color,
            defaults={"text": text, "locale": question.locale},
        )
        self._full_clean_or_raise(answer, answer_where)

    @staticmethod
    def _reject_change(existing, intended, where):
        """
        Bei einer bereits veröffentlichten Version (FR-T6): die Zeile
        muss existieren und in genau den geprüften Feldern mit der
        Datei übereinstimmen. Jede Abweichung — auch eine neu
        hinzugekommene Zeile (`existing is None`) — bricht ab, statt
        die geschützte Version stillschweigend zu verändern.
        """
        if existing is None:
            raise CommandError(
                f"{where} ist neu, die Version aber bereits veröffentlicht. "
                "Änderungen an einer veröffentlichten Version brauchen eine neue "
                "Versionsnummer (FR-T6)."
            )
        for field, value in intended.items():
            if getattr(existing, field) != value:
                raise CommandError(
                    f"{where}: Feld '{field}' weicht von der veröffentlichten Version ab. "
                    "Änderungen an einer veröffentlichten Version brauchen eine neue "
                    "Versionsnummer (FR-T6)."
                )

    @staticmethod
    def _check_unknown_keys(data, allowed, where):
        unknown = set(data.keys()) - allowed
        if unknown:
            raise CommandError(f"Unbekannte Felder in {where}: {sorted(unknown)}")

    @staticmethod
    def _full_clean_or_raise(instance, where):
        try:
            instance.full_clean()
        except ValidationError as exc:
            raise CommandError(f"Ungültige Daten für {where}: {exc.message_dict}") from exc
