"""
Trägt die Pfade der Mana-Symbole in Color.symbol ein (Task 1.5, FR-C2).

Die Dateien liegen unter static/img/mana/ (siehe das README dort). Der
gespeicherte Pfad ist relativ zu static/ und damit direkt das Argument
für {% static %} — nicht der fertige URL-Pfad, der in Produktion durch
den Manifest-Storage von WhiteNoise ohnehin einen Hash bekommt.
"""

from django.db import migrations

SYMBOLS = {
    "W": "img/mana/w.svg",
    "U": "img/mana/u.svg",
    "B": "img/mana/b.svg",
    "R": "img/mana/r.svg",
    "G": "img/mana/g.svg",
}


def set_symbols(apps, schema_editor):
    Color = apps.get_model("colors", "Color")
    for code, path in SYMBOLS.items():
        Color.objects.filter(code=code).update(symbol=path)


def clear_symbols(apps, schema_editor):
    Color = apps.get_model("colors", "Color")
    Color.objects.filter(code__in=SYMBOLS).update(symbol="")


class Migration(migrations.Migration):
    dependencies = [("colors", "0004_colorcombination_theme_perspectivepole")]

    operations = [migrations.RunPython(set_symbols, clear_symbols)]
