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
#: als Vielfaches davon oder in denselben Einheiten formuliert. 44 statt
#: ursprünglich 34 (Task 1.5) — Task 1.7 bringt zehn weitere
#: Linienbeschriftungen dazu, die bei der kleineren Größe mit den
#: Pol-Wörtern kollidierten (zu wenig Abstand zwischen Kanten-Pill und
#: Diagonalen-Pol nahe der Fünfeck-Mitte).
VERTEX_RADIUS = 44
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

#: Schriftgröße und Zeilenabstand zusätzlicher Textzeilen unter/über
#: dem Namen — bislang nur Ziel und Mittel bei 0 Farben (Task 1.7,
#: PRD §5.2). Kleiner als NAME_SIZE, sonst dieselben Einheiten.
EXTRA_LINE_SIZE = 5
EXTRA_LINE_GAP = 1.2

#: Farbe des Halos, der eine Auswahl hervorhebt (Task 1.6, FR-C6).
#: Meist Color.hex selbst — mit einer Ausnahme: Weiß' eigener Hex-Wert
#: (#F8F6D8) ist ein blasses Creme und als weicher Farbfleck auf dem
#: Seitenhintergrund praktisch nicht zu erkennen. Gleiche Farbfamilie,
#: kräftiger gesättigt — ein reiner Darstellungs-Kompromiss für genau
#: diese eine Stelle, keine neue Wahrheit über die Farbe selbst (die
#: bleibt unverändert in Color.hex).
HALO_OVERRIDES = {"W": "#F4C430"}


def halo_color(code, hex_value):
    return HALO_OVERRIDES.get(code, hex_value)


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
    #: Scheibe mit (Task 1.5) — sondern der Rohwert, aus dem `halo`
    #: sich ableitet (Task 1.6/1.7).
    hex: str
    #: Farbe des Selektions-Halos (FR-C6) — siehe `halo_color()`.
    #: Meist gleich `hex`, außer bei Weiß.
    halo: str
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
        """(min_x, min_y, max_x, max_y) für Scheibe und Name allein."""
        return self.bounds_with(())

    def label_lines(self, extra_lines=()):
        """
        [(Text, Schriftgröße, y)] für Namen plus optionale weitere
        Zeilen (Ziel/Mittel bei 0 Farben, Task 1.7) — gestapelt in
        derselben Richtung wie der Name selbst: bei "auto" nach oben
        wachsend, bei "hanging" nach unten, bei "middle" um den
        Ankerpunkt zentriert. `x` ist für jede Zeile `self.label_x`
        (`text-anchor` im Template übernimmt die waagerechte
        Ausrichtung), deshalb hier nicht Teil des Tupels.
        """
        lines = (self.name, *extra_lines)
        count = len(lines)
        result = []
        for index, text in enumerate(lines):
            size = NAME_SIZE if index == 0 else EXTRA_LINE_SIZE
            step = size + EXTRA_LINE_GAP
            if self.baseline == "auto":
                y = self.label_y - (count - 1 - index) * step
            elif self.baseline == "hanging":
                y = self.label_y + step * index + size * 0.8
            else:
                y = self.label_y + (index - (count - 1) / 2) * step + size * 0.32
            result.append((text, size, y))
        return result

    def bounds_with(self, extra_lines):
        """(min_x, min_y, max_x, max_y) für Scheibe, Name und die
        angegebenen weiteren Zeilen zusammen (siehe `label_lines`)."""
        lines = self.label_lines(extra_lines)
        max_width = max(len(text) * size * NAME_CHAR_WIDTH for text, size, _ in lines)
        left = {"start": 0.0, "middle": -max_width / 2, "end": -max_width}[self.text_anchor]
        top = min(y - size for _, size, y in lines)
        bottom = max(y for _, _, y in lines)
        return (
            min(self.x - SYMBOL_RADIUS, self.label_x + left),
            min(self.y - SYMBOL_RADIUS, top),
            max(self.x + SYMBOL_RADIUS, self.label_x + left + max_width),
            max(self.y + SYMBOL_RADIUS, bottom),
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
                halo=halo_color(color.code, color.hex),
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


def _label_bounds(label):
    """(min_x, min_y, max_x, max_y) eines ThemeLabel/PoleLabel-Pills."""
    left = label.x + label.rect_x
    top = label.y + label.rect_y
    return (left, top, left + label.width, top + label.height)


def view_box(vertices_to_fit, extra_lines=None, theme_labels=(), pole_labels=()):
    """
    Der viewBox-String, der alle Ecken samt Namen (und optional
    weiteren Zeilen je Ecke, Task 1.7 — siehe `Vertex.label_lines`)
    sowie alle Linienbeschriftungen umschließt.

    Nicht fest eingetragen, sondern aus den gezeichneten Elementen
    berechnet: Ein längerer Farbname (andere Sprache, Task 1.3/D-15)
    vergrößert das Fenster, statt am Rand abgeschnitten zu werden.

    `extra_lines`: optional {Farbcode: (Zeile, Zeile, …)}.
    `theme_labels`/`pole_labels`: die Listen aus den gleichnamigen
    Funktionen oben — bei einer vollen 0-Farben-Beschriftung reichen
    die Vertex-Ränder allein nicht immer aus (z. B. ein nach außen
    geschobener Ally-Pill an einer kurzen Kante).
    """
    extra_lines = extra_lines or {}
    boxes = [vertex.bounds_with(extra_lines.get(vertex.code, ())) for vertex in vertices_to_fit]
    boxes += [_label_bounds(label) for label in theme_labels]
    boxes += [_label_bounds(label) for label in pole_labels]
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


#: Wie weit der Namen-Pill einer Zweierlinie von der Fünfeck-Mitte weg
#: geschoben wird (Vielfaches des Mittelpunkt-Vektors) — reine
#: Lesbarkeit, hält den Pill von den Diagonalen dahinter frei.
THEME_LABEL_OUTWARD = 1.2
#: Wie weit ein Pol-Wort entlang einer Feind-Diagonale vom
#: zugehörigen Vertex weg zur Mitte hin wandert (Anteil der
#: Kantenlänge). Bewusst klein: näher am eigenen Vertex hält mehr
#: Abstand zu den Ally-Theme-Pills nahe der Mitte der Nachbarkanten.
POLE_LABEL_INSET = 0.22

#: Schriftgrößen der Linienbeschriftungen (Task 1.7, D-37) — kleiner
#: als NAME_SIZE, sonst dieselben Einheiten und dieselbe grobe
#: Zeichenbreiten-Schätzung (NAME_CHAR_WIDTH) wie bei Vertex-Namen:
#: ein `<rect>` als Pill-Hintergrund hinter dem `<text>` braucht in
#: SVG eine explizite Breite, "wächst" anders als HTML nicht von
#: selbst mit dem Text mit.
THEME_LABEL_SIZE = 4.2
POLE_LABEL_SIZE = 3.6
LABEL_PAD_X = 2.4


def _label_width(text, size):
    return len(text) * size * NAME_CHAR_WIDTH + LABEL_PAD_X * 2


@dataclass(frozen=True)
class ThemeLabel:
    """
    Das eine Wort auf der Linie zwischen zwei Farben (D-37): bei einer
    Ally-Kante das gemeinsame Anliegen, bei einer selektierten
    Enemy-Diagonale deren eigenes Thema.
    """

    pair: str
    text: str
    x: float
    y: float
    width: float
    size: float = THEME_LABEL_SIZE

    @property
    def rect_x(self):
        return -self.width / 2

    @property
    def rect_y(self):
        return -(self.size * 0.72)

    @property
    def height(self):
        return self.size * 1.44


@dataclass(frozen=True)
class PoleLabel:
    """Ein Wort an einem Ende einer Feind-Diagonale (D-37)."""

    pair: str
    color: str
    term: str
    x: float
    y: float
    width: float
    size: float = POLE_LABEL_SIZE

    @property
    def rect_x(self):
        return -self.width / 2

    @property
    def rect_y(self):
        return -(self.size * 0.72)

    @property
    def height(self):
        return self.size * 1.44


def theme_labels(pairs, vertices_by_code):
    """
    `pairs`: `[(Paar-Code, Text)]`, wie `content.selection_content()`
    sie liefert. Baut daraus `[ThemeLabel]` mit fertigen Koordinaten —
    Geometrie (hier) bleibt getrennt von der Frage, welche Linie
    überhaupt ein Label bekommt (content.py).
    """
    result = []
    for pair, text in pairs:
        vertex_a, vertex_b = vertices_by_code[pair[0]], vertices_by_code[pair[1]]
        mx = (vertex_a.x + vertex_b.x) / 2
        my = (vertex_a.y + vertex_b.y) / 2
        result.append(
            ThemeLabel(
                pair=pair,
                text=text,
                x=CENTER[0] + (mx - CENTER[0]) * THEME_LABEL_OUTWARD,
                y=CENTER[1] + (my - CENTER[1]) * THEME_LABEL_OUTWARD,
                width=_label_width(text, THEME_LABEL_SIZE),
            )
        )
    return result


def pole_labels(poles, vertices_by_code):
    """
    `poles`: `[(Paar-Code, Farbcode, Wort)]`, wie
    `content.selection_content()` sie liefert. Das Wort sitzt näher an
    der Farbe, zu der es gehört, als am anderen Ende der Diagonale.
    """
    result = []
    for pair, color, term in poles:
        other = pair[1] if color == pair[0] else pair[0]
        from_vertex = vertices_by_code[color]
        toward_vertex = vertices_by_code[other]
        result.append(
            PoleLabel(
                pair=pair,
                color=color,
                term=term,
                x=from_vertex.x + (toward_vertex.x - from_vertex.x) * POLE_LABEL_INSET,
                y=from_vertex.y + (toward_vertex.y - from_vertex.y) * POLE_LABEL_INSET,
                width=_label_width(term, POLE_LABEL_SIZE),
            )
        )
    return result
