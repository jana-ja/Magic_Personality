"""
Inhalte je Selektionsgröße (Task 1.7, PRD §5.2, FR-C8, FR-C10, FR-C11).

Wertet die Datenbank für eine gegebene Farbauswahl aus — getrennt von
der reinen Geometrie (`pentagon.py`) und der reinen URL-Logik
(`selection.py`). `selection_content()` ist der einzige Einstiegspunkt,
den `apps/colors/views.py` braucht.

Farbcodes werden hier absichtlich zu fertigen Anzeige-Werten (Namen,
Texten) aufgelöst, nicht als rohe Buchstaben durchgereicht: Django-
Templates können nicht mit einem variablen Schlüssel in ein Dict
greifen (`dict.varname` sucht den *Namen* "varname", nicht dessen
Wert — dieselbe Falle wie bei den Toggle-Links in Task 1.6). Jede
Stelle, die im Template text braucht, bekommt hier schon den Text.
"""

from .models import Color, ColorCombination
from .utils import CANONICAL_ORDER, canonical_code

#: Ausgeliefert wird in v1 nur Englisch (ARCHITECTURE.md §8) — sobald
#: eine zweite Sprache real erreichbar ist, wird das hier zum
#: Parameter statt einer Konstante.
LOCALE = "en"

#: Die fünf Ally-Kanten bzw. fünf Enemy-Diagonalen als kanonische
#: 2-Buchstaben-Codes, aus derselben Reihenfolge abgeleitet wie
#: pentagon.star_points() seine Diagonalen bildet — nicht separat von
#: Hand eingetragen.
ALLY_PAIRS = [canonical_code(CANONICAL_ORDER[i] + CANONICAL_ORDER[(i + 1) % 5]) for i in range(5)]
ENEMY_PAIRS = [canonical_code(CANONICAL_ORDER[i] + CANONICAL_ORDER[(i + 2) % 5]) for i in range(5)]


def _neighbors(code):
    """
    (linker, rechter) Bildschirm-Nachbar im Uhrzeigersinn ab White
    (FR-C1) — U liegt rechts von W, G links, genauso wie das Fünfeck
    sie zeichnet (Task 1.5). "Rechts" ist die im Kürzel-Kreis
    WUBRG nächste Farbe, "links" die vorherige.
    """
    position = CANONICAL_ORDER.index(code)
    count = len(CANONICAL_ORDER)
    return CANONICAL_ORDER[(position - 1) % count], CANONICAL_ORDER[(position + 1) % count]


def _enemies(code):
    """Die beiden Feindfarben von `code` (D-04)."""
    left, right = _neighbors(code)
    return tuple(c for c in CANONICAL_ORDER if c not in (code, left, right))


def _names():
    """{Farbcode: Name}, eine Abfrage."""
    return dict(Color.objects.values_list("code", "name"))


def _combinations(codes):
    """
    {Kombinations-Code: ColorCombination}, eine Abfrage. Kein
    `in_bulk(field_name="code")` — `code` ist nur zusammen mit
    `locale` eindeutig (unique_together), Django verlangt für
    `in_bulk` aber ein für sich allein eindeutiges Feld.
    """
    return {
        combination.code: combination
        for combination in ColorCombination.objects.filter(locale=LOCALE, code__in=codes)
    }


def _trait_item(combination_trait):
    return {
        "name": combination_trait.trait.name,
        # Roh (für die CSS-Klasse — {{ type|lower }} im Template) und
        # übersetzt (für die sichtbare Kurzform) getrennt: NFR-6
        # verlangt eine textliche Unterscheidung neben der Farbe,
        # "type_label" ist genau dieser Text.
        "type": combination_trait.trait.type,
        "type_label": combination_trait.trait.get_type_display(),
        "description": combination_trait.trait.description,
    }


def selection_content(selected):
    """
    Alles, was Task 1.7 für die Fünfeck-Linien und die Info-Box braucht.

    `selected`: Menge von 0 bis 5 Farbcodes.

    Rückgabe (immer alle Schlüssel vorhanden, leer statt fehlend wenn
    nichts zu zeigen ist — FR-C11):
      - `vertex_extra`: {Farbcode: (goal, means)} nur bei 0 Farben,
        sonst `{}` — Ziel/Mittel stehen nur im leeren Zustand am
        Fünfeck (PRD §5.2).
      - `theme_labels`: [(Paar-Code, Text)] fürs Wort auf einer Linie.
      - `pole_labels`: [(Paar-Code, Farbcode, Wort)] für die Pol-Wörter
        an den Enden einer Feind-Diagonale.
      - `box`: dict mit `kind` ("none" | "single" | "ally" | "enemy" |
        "many") plus den zu diesem Zustand gehörenden Feldern.
      - `trait_groups`: dict mit `kind` ("single" | "one-box") plus
        den Eigenschaftslisten, oder `None` ohne Eigenschaften.
    """
    selected = sorted(selected, key=CANONICAL_ORDER.index)
    size = len(selected)

    if size == 0:
        return _content_for_none()
    if size == 1:
        return _content_for_one(selected[0])
    if size == 2:
        return _content_for_two(selected[0], selected[1])
    return _content_for_many(selected)


def _content_for_none():
    combos = _combinations(list(CANONICAL_ORDER))
    vertex_extra = {code: (combos[code].goal, combos[code].means) for code in CANONICAL_ORDER}

    pair_combos = _combinations(ALLY_PAIRS + ENEMY_PAIRS)
    theme_labels = [
        (pair, pair_combos[pair].theme) for pair in ALLY_PAIRS if pair_combos[pair].theme
    ]

    pole_labels = []
    for pair in ENEMY_PAIRS:
        perspective = pair_combos[pair].perspectives.filter(from_color="").first()
        if perspective:
            pole_labels += [(pair, pole.color, pole.term) for pole in perspective.poles.all()]

    return {
        "vertex_extra": vertex_extra,
        "theme_labels": theme_labels,
        "pole_labels": pole_labels,
        "box": {"kind": "none"},
        "trait_groups": None,
    }


def _content_for_one(code):
    names = _names()
    left, right = _neighbors(code)
    foes = _enemies(code)
    ally_pairs = [canonical_code(code + left), canonical_code(code + right)]
    enemy_pairs = [canonical_code(code + foe) for foe in foes]

    combo = _combinations([code])[code]
    ally_combos = _combinations(ally_pairs)
    enemy_combos = _combinations(enemy_pairs)

    theme_labels = [
        (pair, ally_combos[pair].theme) for pair in ally_pairs if ally_combos[pair].theme
    ]
    pole_labels = []
    for pair in enemy_pairs:
        perspective = enemy_combos[pair].perspectives.filter(from_color=code).first()
        if perspective:
            pole_labels += [(pair, pole.color, pole.term) for pole in perspective.poles.all()]

    center, lean_left, lean_right = [], [], []
    for combination_trait in combo.combination_traits.select_related("trait").all():
        item = _trait_item(combination_trait)
        if not combination_trait.leaning_toward:
            center.append(item)
        elif combination_trait.leaning_toward == left:
            lean_left.append(item)
        elif combination_trait.leaning_toward == right:
            lean_right.append(item)
        # Ein leaning_toward, das keiner der beiden Nachbarn ist, kann
        # laut CombinationTrait.clean() gar nicht in der Datenbank
        # stehen — keine weitere Verzweigung nötig.

    return {
        "vertex_extra": {},
        "theme_labels": theme_labels,
        "pole_labels": pole_labels,
        "box": {
            "kind": "single",
            "name": combo.name,
            "guiding_question": combo.guiding_question,
            "allies": [names[left], names[right]],
            "enemies": [names[foe] for foe in foes],
        },
        "trait_groups": {
            "kind": "single",
            "left_name": names[left],
            "right_name": names[right],
            "center": center,
            "left": lean_left,
            "right": lean_right,
        },
    }


def _content_for_two(a, b):
    pair = canonical_code(a + b)
    combo = _combinations([pair])[pair]

    if combo.relation == ColorCombination.Relation.ALLY:
        return _content_for_ally(a, b, combo)
    return _content_for_enemy(pair, combo)


def _content_for_ally(a, b, combo):
    pair = combo.code
    names = _names()
    other_a = next(c for c in _neighbors(a) if c != b)
    other_b = next(c for c in _neighbors(b) if c != a)
    other_ally_a = canonical_code(a + other_a)
    other_ally_b = canonical_code(b + other_b)

    common_enemy = next(iter(set(_enemies(a)) & set(_enemies(b))))
    enemy_pair_a = canonical_code(a + common_enemy)
    enemy_pair_b = canonical_code(b + common_enemy)
    conflict_pair = canonical_code(other_a + other_b)

    combos = _combinations(
        [pair, other_ally_a, other_ally_b, enemy_pair_a, enemy_pair_b, conflict_pair]
    )

    theme_labels = [
        (code, combos[code].theme)
        for code in (pair, other_ally_a, other_ally_b)
        if combos[code].theme
    ]

    pole_labels = []
    for color, enemy_pair in ((a, enemy_pair_a), (b, enemy_pair_b)):
        perspective = combos[enemy_pair].perspectives.filter(from_color=color).first()
        if perspective:
            pole_labels += [(enemy_pair, pole.color, pole.term) for pole in perspective.poles.all()]

    conflict_poles = {}
    conflict_perspective = combos[conflict_pair].perspectives.filter(from_color="").first()
    if conflict_perspective:
        conflict_poles = {pole.color: pole.term for pole in conflict_perspective.poles.all()}
        pole_labels += list((conflict_pair, color, term) for color, term in conflict_poles.items())
    conflict_text = " vs ".join(conflict_poles[c] for c in conflict_pair if c in conflict_poles)

    traits = [
        _trait_item(combination_trait)
        for combination_trait in combo.combination_traits.select_related("trait").all()
    ]

    return {
        "vertex_extra": {},
        "theme_labels": theme_labels,
        "pole_labels": pole_labels,
        "box": {
            "kind": "ally",
            "relation_label": ColorCombination.Relation.ALLY.label,
            "name": combo.name,
            "archetype": combo.archetype,
            "guiding_question": combo.guiding_question,
            "common_enemy": names[common_enemy],
            "conflict_text": conflict_text,
        },
        "trait_groups": {"kind": "one-box", "title": combo.name, "traits": traits},
    }


def _content_for_enemy(pair, combo):
    theme_labels = [(pair, combo.theme)] if combo.theme else []
    names = _names()

    pole_labels = []
    perspectives = []
    for perspective in combo.perspectives.prefetch_related("poles").all():
        if not perspective.from_color:
            pole_labels += [(pair, pole.color, pole.term) for pole in perspective.poles.all()]
        perspectives.append(
            {
                "from_color": perspective.from_color,
                "from_name": names[perspective.from_color] if perspective.from_color else None,
                "text": perspective.text,
            }
        )

    # Feste, sprechende Reihenfolge (A, B, neutral) statt DB-Einfügereihenfolge.
    order = {pair[0]: 0, pair[1]: 1, "": 2}
    perspectives.sort(key=lambda p: order.get(p["from_color"] or "", 3))

    return {
        "vertex_extra": {},
        "theme_labels": theme_labels,
        "pole_labels": pole_labels,
        "box": {
            "kind": "enemy",
            "relation_label": ColorCombination.Relation.ENEMY.label,
            "name": combo.name,
            "archetype": combo.archetype,
            "guiding_question": combo.guiding_question,
            "perspectives": perspectives,
        },
        "trait_groups": None,
    }


def _content_for_many(selected):
    code = canonical_code(selected)
    combo = _combinations([code]).get(code)
    return {
        "vertex_extra": {},
        "theme_labels": [],
        "pole_labels": [],
        "box": {"kind": "many", "name": combo.name if combo else ""},
        "trait_groups": None,
    }
