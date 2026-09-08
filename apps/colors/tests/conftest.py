"""
Fixtures, die mehrere Test-Dateien in apps/colors/tests/ teilen.
"""

import pytest
from django.conf import settings
from django.core.management import call_command

SEED_PATH = settings.BASE_DIR / "seeds" / "colors_en.json"


@pytest.fixture
def seeded_content(db):
    """
    Spielt die echte seeds/colors_en.json ein (Task 1.4). Die
    31 `ColorCombination`-Zeilen entstehen bereits über die
    Datenmigration (Task 1.1); ihr eigentlicher Inhalt — Namen,
    Traits, Perspektiven, Themes — kommt aber nur über diesen
    Management-Command, nicht automatisch in einer frischen
    Testdatenbank. Jeder Test, der echten Content braucht (statt nur
    die 31 leeren Zeilen), hängt von dieser Fixture ab.
    """
    call_command("seed_content", locale="en", path=str(SEED_PATH))
