from app.contracts.gate_v1 import GateDecision, GateInput
from app.gate_profiles import ACTION_AGENT_RUN
from app.gate_engine import evaluate_gate


def test_unknown_action_denied():
    out = evaluate_gate(GateInput(action="UNKNOWN.ACTION", payload={"x": 1}))
    assert out.decision == GateDecision.DENY


def test_forbidden_admin_key_denied():
    out = evaluate_gate(GateInput(action=ACTION_AGENT_RUN, payload={"agent_id": "a1", "task": "t1", "admin_signal": "X"}))
    assert out.decision == GateDecision.DENY


def test_external_fields_denied():
    out = evaluate_gate(GateInput(action=ACTION_AGENT_RUN, payload={"agent_id": "a1", "task": "t1", "external_id": "e1"}))
    assert out.decision == GateDecision.DENY


def test_determinism():
    inp = GateInput(action=ACTION_AGENT_RUN, payload={"agent_id": "a1", "task": "t1"})
    out1 = evaluate_gate(inp)
    out2 = evaluate_gate(inp)
    assert out1.decision == out2.decision
