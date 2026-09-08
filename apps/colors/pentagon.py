"""
SVG-Layout des Fünfecks (Task 1.5, FR-C1 bis FR-C3).

Übersetzt die reine Radgeometrie aus `wheel.py` in fertige
Zeichenkoordinaten: wo die fünf Ecken liegen, wo Symbol und Name je
Ecke sitzen und wie die Linien zwischen ihnen verlaufen.

Alle Positionen leiten sich aus `wheel.wheel_coordinates()` ab — es
gibt hier keine einzeln eingetragene Ecke (Task 1.5). Die Konstanten
unten legen nur Maßstab und Abstände fest; die Richtung, in der die
Farben stehen, kommt vollständig aus `Color.wheel_position` und
`wheel.POSITION_COUNT`.

Bewusst Django-unabhängig bis auf die Farbobjekte, die hereingereicht
werden: `vertices()` liest von ihnen nur `code`, `name`, `symbol`,
`hex` und `wheel_position`.
"""

from dataclasses import dataclass

from . import wheel

#: Mitte -> Ecke. Legt allein den Maßstab fest; alles andere unten ist
#: als Vielfaches davon oder in denselben Einheiten formuliert.
VERTEX_RADIUS = 34
#: Radius der Mana-Scheibe. Die offiziellen Symbole bringen ihren
#: farbigen Kreis selbst mit (FR-C2), wir zeichnen keinen zweiten.
SYMBOL_RADIUS = 9
#: Abstand zwischen Scheibenrand und Farbname.
LABEL_GAP = 6
LABEL_RADIUS = VERTEX_RADIUS + SYMBOL_RADIUS + LABEL_GAP

#: Schriftgröße der Farbnamen, in SVG-Nutzereinheiten. Steht bewusst
#: hier und nicht im CSS: die Größe geht in die Berechnung der viewBox
#: ein, beide Werte dürfen nicht auseinanderlaufen.
NAME_SIZE = 7
#: Grobe Breite eines Zeichens als Vielfaches der Schriftgröße. Nur zur
#: Abschätzung, wie viel Platz ein Name braucht — echte Textmaße kennt
#: erst der Browser. PADDING fängt die Ungenauigkeit ab.
NAME_CHAR_WIDTH = 0.62
PADDING = 2

# Die Figur wird um den Ursprung herum aufgebaut; die viewBox ergibt
# sich danach aus dem, was tatsächlich gezeichnet wird (siehe
# `view_box`). Dadurch bleibt ein längerer Farbname in einer anderen
# Sprache im Bild, statt am Rand abgeschnitten zu werden.
CENTER = (0.0, 0.0)

# Ab welchem Anteil des Label-Radius ein Name als "klar seitlich" bzw.
# "klar ober-/unterhalb" der Mitte gilt. Als Anteil formuliert und
# nicht als absoluter Wert, damit ein anderer Maßstab die Ausrichtung
# nicht kippt: die obere Ecke bekommt einen zentrierten Namen darüber,
# die beiden seitlichen einen links bzw. rechts daneben, die beiden
# unteren einen zentrierten darunter.
SIDEWAYS_SHARE = 0.75
ABOVE_BELOW_SHARE = 0.5


@dataclass(frozen=True)
class Vertex:
    """Eine Ecke des Fünfecks, fertig zum Zeichnen."""

    code: str
    name: str
    #: Pfad relativ zu static/ — im Template durch {% static %} zu reichen.
    symbol: str
    #: Identitätsfarbe der Farbe (Color.hex). Nicht für die
    #: Kreisfüllung gedacht — die Mana-Symbole bringen ihre eigene
    #: Scheibe mit (Task 1.5) — sondern für die Hervorhebung der
    #: Selektion (Task 1.6, FR-C6): erster tatsächlicher Gebrauch
    #: dieses seit Task 1.1 unbenutzten Felds.
    hex: str
    x: float
    y: float
    label_x: float
    label_y: float
    #: SVG text-anchor: start | middle | end
    text_anchor: str
    #: SVG dominant-baseline: auto | middle | hanging
    baseline: str

    @property
    def symbol_x(self):
        return self.x - SYMBOL_RADIUS

    @property
    def symbol_y(self):
        return self.y - SYMBOL_RADIUS

    @property
    def symbol_size(self):
        return SYMBOL_RADIUS * 2

    @property
    def bounds(self):
        """(min_x, min_y, max_x, max_y) für Scheibe und Name zusammen."""
        name_width = len(self.name) * NAME_SIZE * NAME_CHAR_WIDTH
        left = {"start": 0.0, "middle": -name_width / 2, "end": -name_width}[self.text_anchor]
        top = {"auto": -NAME_SIZE, "middle": -NAME_SIZE / 2, "hanging": 0.0}[self.baseline]
        return (
            min(self.x - SYMBOL_RADIUS, self.label_x + left),
            min(self.y - SYMBOL_RADIUS, self.label_y + top),
            max(self.x + SYMBOL_RADIUS, self.label_x + left + name_width),
            max(self.y + SYMBOL_RADIUS, self.label_y + top + NAME_SIZE),
        )


def _text_anchor(offset_x):
    if offset_x > LABEL_RADIUS * SIDEWAYS_SHARE:
        return "start"
    if offset_x < -LABEL_RADIUS * SIDEWAYS_SHARE:
        return "end"
    return "middle"


def _baseline(offset_y):
    if offset_y > LABEL_RADIUS * ABOVE_BELOW_SHARE:
        return "hanging"
    if offset_y < -LABEL_RADIUS * ABOVE_BELOW_SHARE:
        return "auto"
    return "middle"


def vertices(colors):
    """
    Die Ecken zu `colors`, in derselben Reihenfolge wie übergeben.

    `Color.Meta.ordering` sortiert nach `wheel_position`, ein
    unverändertes Queryset kommt also bereits im Uhrzeigersinn ab
    White (FR-C1).
    """
    result = []
    for color in colors:
        x, y = wheel.wheel_coordinates(color.wheel_position, radius=VERTEX_RADIUS, center=CENTER)
        label_x, label_y = wheel.wheel_coordinates(
            color.wheel_position, radius=LABEL_RADIUS, center=CENTER
        )
        result.append(
            Vertex(
                code=color.code,
                name=color.name,
                symbol=color.symbol,
                hex=color.hex,
                x=x,
                y=y,
                label_x=label_x,
                label_y=label_y,
                text_anchor=_text_anchor(label_x - CENTER[0]),
                baseline=_baseline(label_y - CENTER[1]),
            )
        )
    return result


def _points(selected):
    return " ".join(f"{vertex.x:.3f},{vertex.y:.3f}" for vertex in selected)


def outline_points(vertices_in_wheel_order):
    """Die fünf Außenkanten — jede Ecke zu ihren beiden Nachbarn."""
    return _points(vertices_in_wheel_order)


def star_points(vertices_in_wheel_order):
    """
    Die fünf Diagonalen als Pentagramm. Jede Ecke wird mit der
    übernächsten verbunden; bei fünf Positionen sind das genau die
    Nicht-Nachbarn, also die Feindpaare (D-04).
    """
    count = len(vertices_in_wheel_order)
    order = [(index * 2) % count for index in range(count)]
    return _points([vertices_in_wheel_order[index] for index in order])


def view_box(vertices_to_fit):
    """
    Der viewBox-String, der alle Ecken samt Namen umschließt.

    Nicht fest eingetragen, sondern aus den gezeichneten Elementen
    berechnet: Ein längerer Farbname (andere Sprache, Task 1.3/D-15)
    vergrößert das Fenster, statt am Rand abgeschnitten zu werden.
    """
    boxes = [vertex.bounds for vertex in vertices_to_fit]
    min_y = min(box[1] for box in boxes) - PADDING
    max_y = max(box[3] for box in boxes) + PADDING

    # Waagerecht bewusst symmetrisch um die Mitte: "Green" ragt links
    # weiter hinaus als "Blue" rechts, ein knapp berechnetes Fenster
    # würde das Fünfeck deshalb sichtbar aus der Mitte schieben, sobald
    # das SVG auf der Seite zentriert steht. Senkrecht wäre dieselbe
    # Spiegelung nur toter Rand — die Figur ist nach oben spitz und
    # nach unten breit, das ist ihre Form, keine Schieflage.
    half_width = max(max(abs(box[0]) for box in boxes), max(abs(box[2]) for box in boxes)) + PADDING
    return f"{-half_width:.3f} {min_y:.3f} {half_width * 2:.3f} {max_y - min_y:.3f}"
