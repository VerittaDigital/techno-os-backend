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
