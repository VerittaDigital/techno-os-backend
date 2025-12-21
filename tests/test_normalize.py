from app.contracts.normalize import (
    normalize_text,
    normalize_score,
    normalize_literal_enum,
    safe_list,
)


def test_normalize_text():
    assert normalize_text(None) is None
    assert normalize_text("") is None
    assert normalize_text("  ") is None
    assert normalize_text("abc") == "abc"
    assert normalize_text("  abc  ") == "abc"


def test_normalize_score():
    assert normalize_score(None) is None
    assert normalize_score("") is None
    assert normalize_score("80") == 80
    assert normalize_score(80) == 80
    assert normalize_score(80.0) == 80
    assert normalize_score("101") is None
    assert normalize_score(101) is None
    assert normalize_score(-1) is None
    assert normalize_score("abc") is None


def test_normalize_literal_enum():
    allowed = {"A", "B C"}
    assert normalize_literal_enum("A", allowed) == "A"
    assert normalize_literal_enum("  B   C  ", allowed) == "B C"
    assert normalize_literal_enum(None, allowed) == "UNKNOWN"
    assert normalize_literal_enum("", allowed) == "UNKNOWN"


def test_safe_list():
    assert safe_list(None) == []
    assert safe_list(1) == [1]
    assert safe_list([1, 2]) == [1, 2]
    assert safe_list((1, 2)) == [1, 2]
    s = {1, 2}
    res = safe_list(s)
    assert set(res) == s
