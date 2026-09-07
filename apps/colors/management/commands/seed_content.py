"""
manage.py seed_content — idempotenter Import von Farb-Content aus
seeds/colors_<locale>.json (Task 1.3, D-28).

Format vollständig dokumentiert in seeds/README.md. Validiert über
dieselben Regeln, die die Modelle selbst in Tasks 1.1/1.2 bekommen
haben (full_clean()) — Content-Fehler landen als klare Fehlermeldung,
nie still in der Datenbank.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.colors.models import ColorCombination, CombinationTrait, Perspective, Trait
from apps.colors.utils import is_canonical

ALLOWED_TOP_LEVEL_KEYS = {"locale", "combinations"}
ALLOWED_COMBINATION_KEYS = {
    "code",
    "name",
    "goal",
    "means",
    "guiding_question",
    "archetype",
    "traits",
    "perspectives",
}
ALLOWED_TRAIT_KEYS = {"name", "description", "type", "leaning_toward"}
ALLOWED_PERSPECTIVE_KEYS = {"from_color", "text"}


class Command(BaseCommand):
    help = "Spielt Farb-Content aus seeds/colors_<locale>.json idempotent ein (seeds/README.md)."

    def add_arguments(self, parser):
        parser.add_argument("--locale", required=True, help='z. B. "en"')
        parser.add_argument(
            "--path",
            help="Pfad zur Seed-Datei. Default: seeds/colors_<locale>.json. Vor allem für Tests.",
        )

    def handle(self, *args, **options):
        locale = options["locale"]
        path = (
            Path(options["path"])
            if options["path"]
            else Path(settings.BASE_DIR) / "seeds" / f"colors_{locale}.json"
        )

        if not path.exists():
            raise CommandError(f"Seed-Datei nicht gefunden: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"{path} ist kein gültiges JSON: {exc}") from exc

        self._check_unknown_keys(data, ALLOWED_TOP_LEVEL_KEYS, "top level")

        file_locale = data.get("locale")
        if file_locale != locale:
            raise CommandError(
                f"--locale={locale!r} passt nicht zum 'locale'-Feld in der Datei ({file_locale!r})."
            )

        combinations_created = 0
        combinations_updated = 0
        traits_seen = 0
        perspectives_seen = 0

        with transaction.atomic():
            for entry in data.get("combinations", []):
                self._check_unknown_keys(entry, ALLOWED_COMBINATION_KEYS, "combination")

                code = entry.get("code")
                if not code:
                    raise CommandError("Eine Kombination ohne 'code' wurde gefunden.")
                if not is_canonical(code):
                    raise CommandError(f"Unbekannter oder ungültiger Farbcode: {code!r}")

                combination, created = ColorCombination.objects.update_or_create(
                    code=code,
                    locale=locale,
                    defaults={
                        "name": entry.get("name", ""),
                        "goal": entry.get("goal", ""),
                        "means": entry.get("means", ""),
                        "guiding_question": entry.get("guiding_question", ""),
                        "archetype": entry.get("archetype", ""),
                    },
                )
                self._full_clean_or_raise(combination, f"combination {code!r}")
                combinations_created += int(created)
                combinations_updated += int(not created)

                for trait_entry in entry.get("traits", []):
                    self._seed_trait(combination, code, trait_entry, locale)
                    traits_seen += 1

                for perspective_entry in entry.get("perspectives", []):
                    self._seed_perspective(combination, code, perspective_entry, locale)
                    perspectives_seen += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{locale}: {combinations_created} Kombinationen neu, "
                f"{combinations_updated} aktualisiert, {traits_seen} Eigenschaften, "
                f"{perspectives_seen} Perspektiven verarbeitet."
            )
        )

    def _seed_trait(self, combination, code, trait_entry, locale):
        self._check_unknown_keys(trait_entry, ALLOWED_TRAIT_KEYS, f"trait in combination {code!r}")

        name = trait_entry.get("name")
        trait_type = trait_entry.get("type")
        if not name or not trait_type:
            raise CommandError(f"Eigenschaft in Kombination {code!r} braucht 'name' und 'type'.")

        trait, _ = Trait.objects.update_or_create(
            name=name,
            locale=locale,
            defaults={"description": trait_entry.get("description", ""), "type": trait_type},
        )
        self._full_clean_or_raise(trait, f"trait {name!r} (combination {code!r})")

        combination_trait, _ = CombinationTrait.objects.update_or_create(
            combination=combination,
            trait=trait,
            defaults={"leaning_toward": trait_entry.get("leaning_toward") or ""},
        )
        self._full_clean_or_raise(combination_trait, f"trait {name!r} (combination {code!r})")

    def _seed_perspective(self, combination, code, perspective_entry, locale):
        self._check_unknown_keys(
            perspective_entry, ALLOWED_PERSPECTIVE_KEYS, f"perspective in combination {code!r}"
        )

        text = perspective_entry.get("text")
        if not text:
            raise CommandError(f"Perspective in Kombination {code!r} braucht 'text'.")
        from_color = perspective_entry.get("from_color") or ""

        perspective, _ = Perspective.objects.update_or_create(
            combination=combination,
            from_color=from_color,
            defaults={"text": text, "locale": locale},
        )
        self._full_clean_or_raise(
            perspective, f"perspective in combination {code!r} (from_color={from_color!r})"
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
