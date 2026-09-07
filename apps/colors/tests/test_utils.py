from apps.colors.utils import canonical_code, is_canonical


def test_canonical_code_sorts_into_wubrg_order():
    assert canonical_code("UW") == "WU"
    assert canonical_code(["G", "R", "W"]) == "WRG"


def test_canonical_code_deduplicates():
    assert canonical_code("WW") == "W"


def test_canonical_code_ignores_unknown_letters():
    assert canonical_code("WX") == "W"


def test_is_canonical_true_for_a_correctly_sorted_code():
    assert is_canonical("WUBRG") is True
    assert is_canonical("W") is True


def test_is_canonical_false_for_an_unsorted_code():
    assert is_canonical("UW") is False
