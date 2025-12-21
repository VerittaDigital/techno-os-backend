from app.contracts.field_governance import (
    get_rule,
    is_runtime_allowed,
    explain_field,
    Criticality,
)


def test_canonical_fields_return_rules():
    r = get_rule("agent_id")
    assert r is not None
    assert r.author.name == "SYSTEM"
    assert r.criticality == Criticality.CANONICAL_CORE


def test_prohibited_runtime_fields():
    assert not is_runtime_allowed("%SEAL")
    assert not is_runtime_allowed("Some rollup total")
    rule = get_rule("%SEAL")
    assert rule is not None
    assert rule.criticality == Criticality.PROHIBITED_RUNTIME


def test_unknown_field_explain():
    assert explain_field("this_does_not_exist") == "unknown field"


def test_unknown_field_denied_by_default():
    assert is_runtime_allowed("some_new_field") is False


def test_external_fields_not_runtime_allowed():
    assert is_runtime_allowed("external_id") is False
    assert is_runtime_allowed("external_source") is False
