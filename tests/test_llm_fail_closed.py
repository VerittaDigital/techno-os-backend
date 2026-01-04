"""Testes para fail-closed enforcement (RISK-6)."""

import uuid
from unittest.mock import Mock

import pytest

from app.action_contracts import ActionRequest
from app.executors.llm_executor_v1 import LLMExecutorV1
from app.llm.fake_client import FakeLLMClient


@pytest.fixture(autouse=True)
def clean_circuit_breaker_state():
    """Limpa estado compartilhado do circuit breaker antes de cada teste."""
    from app.llm.factory import _circuit_breakers
    _circuit_breakers.clear()
    yield


def test_timeout_raises_timeout_error():
    """Timeout → TimeoutError propagada (fail-closed)."""
    client = FakeLLMClient(simulate_timeout=True)
    executor = LLMExecutorV1(client=client)

    req = ActionRequest(
        action="test",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4())
    )

    with pytest.raises((TimeoutError, RuntimeError)):  # Pode ser wrapped em RuntimeError
        executor.execute(req)


def test_provider_error_raises_runtime_error():
    """RuntimeError → RuntimeError propagada (fail-closed)."""
    client = Mock()
    client.generate = Mock(side_effect=RuntimeError("PROVIDER_ERROR"))
    executor = LLMExecutorV1(client=client)

    req = ActionRequest(
        action="test",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4())
    )

    with pytest.raises(RuntimeError):
        executor.execute(req)


def test_never_returns_partial_response():
    """Nunca retorna data parcial em caso de erro."""
    client = Mock()
    # Simular erro parcial (começa resposta mas falha)
    client.generate = Mock(side_effect=RuntimeError("PARTIAL_FAILURE"))
    executor = LLMExecutorV1(client=client)

    req = ActionRequest(
        action="test",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4())
    )

    # Deve lançar exceção, NUNCA retornar dicionário parcial
    with pytest.raises(RuntimeError):
        executor.execute(req)


def test_circuit_open_raises_error():
    """Circuit OPEN → RuntimeError propagada (fail-closed, sem tentar chamada)."""
    client = Mock()
    client.generate = Mock(side_effect=RuntimeError("PROVIDER_ERROR"))
    client.__class__.__name__ = "FakeClient"  # Para detectar provider
    executor = LLMExecutorV1(client=client)

    trace_id = str(uuid.uuid4())

    # Abrir circuit com 3 falhas
    for _ in range(3):
        req = ActionRequest(
            action="test",
            payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
            trace_id=trace_id
        )
        with pytest.raises(RuntimeError):
            executor.execute(req)

    # Próxima chamada deve falhar por CIRCUIT_OPEN
    req = ActionRequest(
        action="test",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=trace_id
    )
    with pytest.raises(RuntimeError, match="CIRCUIT_OPEN"):
        executor.execute(req)


def test_success_returns_dict():
    """Sucesso → retorna dicionário com text, model, usage."""
    # Usar FakeLLMClient real (não Mock) para evitar interferência de rate limiter acumulado
    client = FakeLLMClient()
    executor = LLMExecutorV1(client=client)

    req = ActionRequest(
        action="test",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4())
    )

    result = executor.execute(req)

    assert "text" in result
    assert result["text"].startswith("FAKE::")  # FakeLLMClient retorna FAKE::hash
    assert result["model"] == "gpt-4o-mini"
    assert "usage" in result
