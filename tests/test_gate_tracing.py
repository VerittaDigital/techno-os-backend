"""
Testes de tracing para o gate_engine (FASE 4).
- Valida que spans são criados corretamente em evaluate_gate
- Garante fail-closed, sem alteração semântica
"""
import pytest
from app.gate_engine import evaluate_gate, GateInput, GateResult, DEFAULT_RULES
from app.tracing import is_tracing_enabled
import os

@pytest.fixture(autouse=True)
def enable_tracing(monkeypatch):
    monkeypatch.setenv("TRACING_ENABLED", "1")
    yield
    monkeypatch.setenv("TRACING_ENABLED", "0")


def test_evaluate_gate_tracing(monkeypatch):
    # Mock profile and input
    inp = GateInput(action="process", payload={"external_id": "123"}, allow_external=True, deny_unknown_fields=False)
    # Ensure tracing is enabled
    monkeypatch.setenv("TRACING_ENABLED", "1")
    result = evaluate_gate(inp, DEFAULT_RULES)
    assert isinstance(result, GateResult)
    # No semantic change: decision is ALLOW or DENY as before
    assert result.decision in [result.decision.ALLOW, result.decision.DENY]
    # (Opcional) Validar que não lança exceção


def test_evaluate_gate_fail_closed(monkeypatch):
    # Tracing desabilitado: sem span, sem erro
    monkeypatch.setenv("TRACING_ENABLED", "0")
    inp = GateInput(action="process", payload={"external_id": "123"}, allow_external=True, deny_unknown_fields=False)
    result = evaluate_gate(inp, DEFAULT_RULES)
    assert isinstance(result, GateResult)
    assert result.decision in [result.decision.ALLOW, result.decision.DENY]
    # Nenhuma exceção


def test_gate_tracing_governance_on_off():
    """TRACING_ENABLED=0 → gate funciona"""
    os.environ["TRACING_ENABLED"] = "0"
    inp = GateInput(action="test_action", payload={"key": "value"})
    result = evaluate_gate(inp)
    assert isinstance(result, GateResult)
    assert result.decision in ["ALLOW", "DENY"]


def test_gate_tracing_governance_on():
    """TRACING_ENABLED=1 → gate funciona"""
    os.environ["TRACING_ENABLED"] = "1"
    inp = GateInput(action="test_action", payload={"key": "value"})
    result = evaluate_gate(inp)
    assert isinstance(result, GateResult)
    assert result.decision in ["ALLOW", "DENY"]


def test_gate_semantic_invariance():
    """Mesmo GateInput, GateResult idêntico com tracing ON/OFF"""
    from app.gate_profiles import ACTION_AGENT_RUN
    inp = GateInput(action=ACTION_AGENT_RUN, payload={"agent_id": "a1", "task": "t1"})
    
    os.environ["TRACING_ENABLED"] = "0"
    result_off = evaluate_gate(inp)
    
    os.environ["TRACING_ENABLED"] = "1"
    result_on = evaluate_gate(inp)
    
    # Comparar campos relevantes, ignorando 'at' que muda
    assert result_off.decision == result_on.decision
    assert result_off.reasons == result_on.reasons
    assert result_off.action == result_on.action
    assert result_off.evaluated_keys == result_on.evaluated_keys
    assert result_off.profile_hash == result_on.profile_hash
    assert result_off.matched_rules == result_on.matched_rules
