"""
Datenmigration (Task 1.1): legt die fünf Farben und alle 31
Farbkombinationen strukturell an.

Bewusst noch ohne Inhalt — Namen, Ziel/Mittel, Eigenschaften und
Perspektiven kommen mit dem Seed-Mechanismus aus Task 1.3 und der
eigentlichen Content-Erfassung aus Task 1.4. Hier geht es nur darum,
dass jede der 31 Kombinationen als Zeile existiert, bevor irgendeine
Selektion im Fünfeck ins Leere läuft (FR-C11).

Die Codes werden aus itertools.combinations über "WUBRG" erzeugt statt
von Hand aufgelistet — das erzeugt sie automatisch in kanonischer
Reihenfolge (dieselbe Prüfung wie apps.colors.utils.is_canonical) und
lässt sich gegen die Anzahl (31) und die Sortierung testen.
"""

from itertools import combinations

from django.db import migrations

WUBRG = "WUBRG"

COLORS = [
    {"code": "W", "name": "White", "hex": "#F8F6D8", "wheel_position": 0},
    {"code": "U", "name": "Blue", "hex": "#0E68AB", "wheel_position": 1},
    {"code": "B", "name": "Black", "hex": "#150B00", "wheel_position": 2},
    {"code": "R", "name": "Red", "hex": "#D3202A", "wheel_position": 3},
    {"code": "G", "name": "Green", "hex": "#00733E", "wheel_position": 4},
]

ALL_COMBINATION_CODES = [
    "".join(combo) for size in range(1, len(WUBRG) + 1) for combo in combinations(WUBRG, size)
]


def seed_colors_and_combinations(apps, schema_editor):
    Color = apps.get_model("colors", "Color")
    ColorCombination = apps.get_model("colors", "ColorCombination")

    for color in COLORS:
        Color.objects.create(**color)

    for code in ALL_COMBINATION_CODES:
        ColorCombination.objects.create(code=code, locale="en")


def remove_colors_and_combinations(apps, schema_editor):
    Color = apps.get_model("colors", "Color")
    ColorCombination = apps.get_model("colors", "ColorCombination")
    # Sicher als blunt "alles löschen": Content wird künftig per
    # seed_content-Kommando (Task 1.3) in genau diesen Zeilen
    # aktualisiert, nicht per weiterer Migration neu angelegt.
    ColorCombination.objects.all().delete()
    Color.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("colors", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_colors_and_combinations, remove_colors_and_combinations),
    ]
