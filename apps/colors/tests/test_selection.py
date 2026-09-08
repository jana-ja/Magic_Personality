"""
Tests für die reine Auswahl-Logik (Task 1.6, FR-C4 bis FR-C7).

Kein Zugriff auf Modelle oder Request — reine Mengenoperationen,
unabhängig von der Datenbank.
"""

from apps.colors import selection

# parse_url_code -------------------------------------------------------


def test_parses_a_single_letter():
    assert selection.parse_url_code("w") == {"W"}


def test_parses_mixed_case():
    assert selection.parse_url_code("Wu") == {"W", "U"}


def test_parses_all_five_letters():
    assert selection.parse_url_code("wubrg") == {"W", "U", "B", "R", "G"}


def test_rejects_a_letter_outside_wubrg():
    assert selection.parse_url_code("x") is None
    assert selection.parse_url_code("wx") is None


def test_rejects_a_duplicated_letter():
    assert selection.parse_url_code("ww") is None


def test_rejects_more_than_five_letters():
    assert selection.parse_url_code("wubrgw") is None


def test_rejects_an_empty_string():
    assert selection.parse_url_code("") is None


# canonical_url_code -----------------------------------------------------


def test_canonical_url_code_is_lowercase_and_wubrg_ordered():
    assert selection.canonical_url_code({"U", "W"}) == "wu"


def test_canonical_url_code_of_an_empty_set_is_empty():
    assert selection.canonical_url_code(set()) == ""


# toggled ------------------------------------------------------------------


def test_toggling_an_unselected_color_adds_it():
    assert selection.toggled({"W"}, "U") == {"W", "U"}


def test_toggling_a_selected_color_removes_it():
    assert selection.toggled({"W", "U"}, "U") == {"W"}


def test_toggling_the_only_selected_color_empties_the_set():
    assert selection.toggled({"W"}, "W") == set()
