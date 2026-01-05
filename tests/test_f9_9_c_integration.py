"""Tests for F9.9-C LLM Integration (executor + retry + circuit breaker).

Suite de testes validando integração completa da resiliência LLM:
- Circuit breaker abre após 3 falhas
- Retry ocorre em erros 429
- Timeout efetivo de 30s
"""

from __future__ import annotations

import time
import uuid
from unittest.mock import MagicMock

import pytest

from app.action_contracts import ActionRequest
from app.executors.llm_executor_v1 import LLMExecutorV1
from app.llm.circuit_breaker import CircuitState, CircuitBreaker
from app.llm.errors import ProviderError
from app.llm.policy import Policy


# ==================== CIRCUIT BREAKER INTEGRATION TESTS ====================


def test_circuit_breaker_opens_after_3_failures():
    """Circuit breaker deve abrir após 3 falhas consecutivas (F9.9-C)."""
    isolated_cb = CircuitBreaker(failure_threshold=3, timeout_s=60)

    mock_client = MagicMock()
    mock_client.generate.side_effect = ProviderError("provider down")

    executor = LLMExecutorV1(client=mock_client)
    executor._circuit_breaker = isolated_cb

    req = ActionRequest(
        action="llm.generate",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4()),
    )

    # 3 falhas consecutivas
    for _ in range(3):
        with pytest.raises(RuntimeError, match="PROVIDER_ERROR"):
            executor.execute(req)

    assert isolated_cb.state == CircuitState.OPEN


def test_circuit_breaker_blocks_when_open():
    """Circuit breaker deve bloquear chamadas quando aberto (F9.9-C)."""
    isolated_cb = CircuitBreaker(failure_threshold=3, timeout_s=60)

    mock_client = MagicMock()
    mock_client.generate.side_effect = ProviderError("provider down")

    executor = LLMExecutorV1(client=mock_client)
    executor._circuit_breaker = isolated_cb

    req = ActionRequest(
        action="llm.generate",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4()),
    )

    # Abrir circuit (3 falhas)
    for _ in range(3):
        with pytest.raises(RuntimeError):
            executor.execute(req)

    # Próxima chamada bloqueada
    call_count_before = mock_client.generate.call_count

    with pytest.raises(RuntimeError, match="PROVIDER_ERROR"):
        executor.execute(req)

    assert mock_client.generate.call_count == call_count_before


def test_circuit_breaker_half_open_after_timeout():
    """Circuit breaker deve ir para HALF_OPEN após cooldown (F9.9-C)."""
    mock_client = MagicMock()
    mock_client.generate.side_effect = [
        ProviderError("fail 1"),
        ProviderError("fail 2"),
        ProviderError("fail 3"),
        {"text": "success", "model": "gpt-4o-mini", "usage": {"total": 10}, "latency_ms": 100},
    ]

    short_cb = CircuitBreaker(failure_threshold=3, timeout_s=1)

    executor = LLMExecutorV1(client=mock_client)
    executor._circuit_breaker = short_cb

    req = ActionRequest(
        action="llm.generate",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4()),
    )

    # Abrir circuit (3 falhas)
    for _ in range(3):
        with pytest.raises(RuntimeError):
            executor.execute(req)

    assert short_cb.state == CircuitState.OPEN

    # Aguardar cooldown
    time.sleep(1.1)

    # Deve tentar (HALF_OPEN) e suceder
    result = executor.execute(req)

    assert result["text"] == "success"
    assert short_cb.state == CircuitState.CLOSED


# ==================== RETRY INTEGRATION TESTS ====================


def test_retry_on_429_error():
    """Retry deve ocorrer em erro 429 (rate limit) — F9.9-C."""
    isolated_cb = CircuitBreaker(failure_threshold=10, timeout_s=60)

    mock_client = MagicMock()
    mock_client.generate.side_effect = [
        ProviderError("429 rate limit"),
        {"text": "success after retry", "model": "gpt-4o-mini", "usage": {"total": 10}, "latency_ms": 100},
    ]

    executor = LLMExecutorV1(client=mock_client)
    executor._circuit_breaker = isolated_cb

    req = ActionRequest(
        action="llm.generate",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4()),
    )

    result = executor.execute(req)

    assert result["text"] == "success after retry"
    assert mock_client.generate.call_count == 2


def test_retry_max_2_attempts():
    """Retry deve respeitar max 2 retries (total 3 tentativas) — F9.9-C."""
    isolated_cb = CircuitBreaker(failure_threshold=10, timeout_s=60)

    mock_client = MagicMock()
    mock_client.generate.side_effect = ProviderError("429 rate limit")

    executor = LLMExecutorV1(client=mock_client)
    executor._circuit_breaker = isolated_cb

    req = ActionRequest(
        action="llm.generate",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4()),
    )

    with pytest.raises(RuntimeError, match="PROVIDER_ERROR"):
        executor.execute(req)

    # 1 tentativa inicial + 2 retries = 3 calls
    assert mock_client.generate.call_count == 3


def test_no_retry_on_timeout():
    """Timeout não deve fazer retry (fail-fast) — F9.9-C."""
    isolated_cb = CircuitBreaker(failure_threshold=10, timeout_s=60)

    mock_client = MagicMock()
    mock_client.generate.side_effect = TimeoutError()

    executor = LLMExecutorV1(client=mock_client)
    executor._circuit_breaker = isolated_cb

    req = ActionRequest(
        action="llm.generate",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4()),
    )

    with pytest.raises(TimeoutError):
        executor.execute(req)

    assert mock_client.generate.call_count == 1


# ==================== TIMEOUT POLICY TESTS ====================


def test_timeout_policy_30s():
    """Timeout policy deve ser 30s conforme F9.9-C."""
    assert Policy.TIMEOUT_S == 30.0


def test_executor_respects_policy_timeout():
    """Executor deve respeitar Policy.TIMEOUT_S em chamadas — F9.9-C."""
    isolated_cb = CircuitBreaker(failure_threshold=10, timeout_s=60)

    mock_client = MagicMock()
    mock_client.generate.return_value = {
        "text": "response",
        "model": "gpt-4o-mini",
        "usage": {"total": 10},
        "latency_ms": 100,
    }

    executor = LLMExecutorV1(client=mock_client)
    executor._circuit_breaker = isolated_cb

    req = ActionRequest(
        action="llm.generate",
        payload={"prompt": "test", "model": "gpt-4o-mini", "max_tokens": 100},
        trace_id=str(uuid.uuid4()),
    )

    executor.execute(req)

    call_kwargs = mock_client.generate.call_args[1]
    assert call_kwargs["timeout_s"] == 30.0
