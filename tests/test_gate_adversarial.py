from app.contracts.gate_v1 import GateDecision, GateInput, GateReasonCode
from app.gate_engine import evaluate_gate
from app.gate_profiles import ACTION_AGENT_RUN


def test_nested_payload_denied_by_unknown_fields():
    # nested não é automaticamente proibido; a chave "nested" é unknown => DENY
    out = evaluate_gate(GateInput(action=ACTION_AGENT_RUN, payload={"agent_id": "a1", "task": "t1", "nested": {"x": 1}}))
    assert out.decision == GateDecision.DENY
    assert out.reasons[0].code == GateReasonCode.UNKNOWN_FIELDS_PRESENT


def test_list_payload_denied_by_unknown_fields():
    out = evaluate_gate(GateInput(action=ACTION_AGENT_RUN, payload={"agent_id": "a1", "task": "t1", "items": [1, 2, 3]}))
    assert out.decision == GateDecision.DENY
    assert out.reasons[0].code == GateReasonCode.UNKNOWN_FIELDS_PRESENT


def test_unicode_confusable_key_denied():
    # "аdmin_signal" com 'a' cirílico (confusable) não bate forbidden baseline,
    # então o perfil fail-closed deve negar por unknown field.
    confusable = "аdmin_signal"  # Cyrillic 'а'
    out = evaluate_gate(GateInput(action=ACTION_AGENT_RUN, payload={"agent_id": "a1", "task": "t1", confusable: "X"}))
    assert out.decision == GateDecision.DENY
    assert out.reasons[0].code == GateReasonCode.UNKNOWN_FIELDS_PRESENT
