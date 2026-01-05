"""Tests for F9.9-B LLM Hardening (factory, retry, circuit breaker).

Suite de testes cobrindo:
- Factory fail-closed com allowlists
- Retry decorator (429, 5xx)
- Circuit breaker (3 falhas → open)
- Prometheus metrics
"""

from __future__ import annotations

import os
import time
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from app.llm.circuit_breaker import CircuitBreaker, CircuitState
from app.llm.client import LLMClient
from app.llm.errors import ConfigurationError, ProviderError
from app.llm.factory import create_llm_client
from app.llm.retry import with_retry


# ==================== FACTORY TESTS ====================


def test_factory_fail_closed_no_allowlist():
    """Factory deve falhar se VERITTA_LLM_ALLOWED_PROVIDERS ausente."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError, match="not configured"):
            create_llm_client()


def test_factory_fail_closed_empty_allowlist():
    """Factory deve falhar se allowlist vazia."""
    with patch.dict(os.environ, {"VERITTA_LLM_ALLOWED_PROVIDERS": "  ,  "}):
        with pytest.raises(ConfigurationError, match="is empty"):
            create_llm_client()


def test_factory_fail_closed_provider_not_allowed():
    """Factory deve falhar se provider não estiver na allowlist."""
    with patch.dict(
        os.environ,
        {"VERITTA_LLM_ALLOWED_PROVIDERS": "openai,fake", "LLM_PROVIDER": "anthropic"},
    ):
        with pytest.raises(ConfigurationError, match="not in allowlist"):
            create_llm_client()


def test_factory_success_fake_in_allowlist():
    """Factory deve criar FakeLLMClient se 'fake' na allowlist."""
    with patch.dict(
        os.environ, {"VERITTA_LLM_ALLOWED_PROVIDERS": "fake", "LLM_PROVIDER": "fake"}
    ):
        client = create_llm_client()
        assert client is not None
        # FakeLLMClient deve existir
        from app.llm.fake_client import FakeLLMClient

        assert isinstance(client, FakeLLMClient)


def test_factory_timeout_default_30s():
    """Factory deve usar timeout default de 30s (F9.9-B)."""
    with patch.dict(
        os.environ, {"VERITTA_LLM_ALLOWED_PROVIDERS": "fake", "LLM_PROVIDER": "fake"}
    ):
        # FakeLLMClient não tem timeout, testar com mock
        with patch("app.llm.factory.OpenAIClient") as mock_openai:
            with patch.dict(
                os.environ,
                {
                    "VERITTA_LLM_ALLOWED_PROVIDERS": "openai",
                    "LLM_PROVIDER": "openai",
                    "OPENAI_API_KEY": "test-key",
                },
            ):
                create_llm_client()
                # Verificar que foi chamado com default_timeout_s=30
                mock_openai.assert_called_once()
                call_kwargs = mock_openai.call_args[1]
                assert call_kwargs.get("default_timeout_s") == 30.0


def test_factory_missing_api_key():
    """Factory deve falhar se API key ausente para provider real."""
    with patch.dict(
        os.environ,
        {"VERITTA_LLM_ALLOWED_PROVIDERS": "openai", "LLM_PROVIDER": "openai"},
        clear=True,
    ):
        with pytest.raises(ConfigurationError, match="Missing OPENAI_API_KEY"):
            create_llm_client()


# ==================== RETRY TESTS ====================


def test_retry_success_first_attempt():
    """Retry decorator não deve fazer retry se sucesso na 1ª tentativa."""
    mock_func = MagicMock(return_value="success")
    decorated = with_retry(max_retries=2)(mock_func)

    result = decorated()

    assert result == "success"
    assert mock_func.call_count == 1


def test_retry_fail_after_max_retries():
    """Retry deve falhar após esgotar max_retries."""
    mock_func = MagicMock(side_effect=ProviderError("rate limit"))

    decorated = with_retry(max_retries=2)(mock_func)

    with pytest.raises(ProviderError):
        decorated()

    # 1 tentativa inicial + 2 retries = 3 calls
    assert mock_func.call_count == 3


def test_retry_timeout_no_retry():
    """Timeout não deve fazer retry (fail-fast)."""
    mock_func = MagicMock(side_effect=TimeoutError())

    decorated = with_retry(max_retries=2)(mock_func)

    with pytest.raises(TimeoutError):
        decorated()

    # Apenas 1 tentativa (sem retry)
    assert mock_func.call_count == 1


def test_retry_non_retryable_error():
    """Erros não-retryable (4xx exceto 429) não devem fazer retry."""
    mock_func = MagicMock(side_effect=ProviderError("400 bad request"))

    decorated = with_retry(max_retries=2)(mock_func)

    with pytest.raises(ProviderError):
        decorated()

    # Apenas 1 tentativa (erro não retryable)
    assert mock_func.call_count == 1


def test_retry_exponential_backoff():
    """Retry deve usar exponential backoff (1s, 2s)."""
    mock_func = MagicMock(side_effect=ProviderError("429 rate limit"))

    decorated = with_retry(max_retries=2)(mock_func)

    start = time.perf_counter()
    with pytest.raises(ProviderError):
        decorated()
    elapsed = time.perf_counter() - start

    # Deve ter esperado ~3s (1s + 2s backoff)
    assert elapsed >= 3.0
    assert elapsed < 4.0  # Margem de tolerância


# ==================== CIRCUIT BREAKER TESTS ====================


def test_circuit_breaker_closed_by_default():
    """Circuit breaker deve iniciar em estado CLOSED."""
    cb = CircuitBreaker()
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_open_after_threshold():
    """Circuit breaker deve abrir após threshold de falhas."""
    cb = CircuitBreaker(failure_threshold=3, timeout_s=60)

    mock_func = MagicMock(side_effect=ProviderError("error"))

    # 3 falhas consecutivas
    for _ in range(3):
        with pytest.raises(ProviderError):
            cb.call(mock_func)

    # Circuito deve estar aberto
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_blocks_when_open():
    """Circuit breaker deve bloquear chamadas quando aberto."""
    cb = CircuitBreaker(failure_threshold=2, timeout_s=60)

    mock_func = MagicMock(side_effect=ProviderError("error"))

    # 2 falhas para abrir
    for _ in range(2):
        with pytest.raises(ProviderError):
            cb.call(mock_func)

    assert cb.state == CircuitState.OPEN

    # Nova chamada deve ser bloqueada (sem invocar mock_func)
    with pytest.raises(ProviderError, match="CIRCUIT_OPEN"):
        cb.call(mock_func)

    # mock_func só foi chamado 2 vezes (não 3)
    assert mock_func.call_count == 2


def test_circuit_breaker_half_open_after_timeout():
    """Circuit breaker deve ir para HALF_OPEN após cooldown."""
    cb = CircuitBreaker(failure_threshold=2, timeout_s=1)  # 1s cooldown

    mock_func = MagicMock(side_effect=ProviderError("error"))

    # 2 falhas para abrir
    for _ in range(2):
        with pytest.raises(ProviderError):
            cb.call(mock_func)

    assert cb.state == CircuitState.OPEN

    # Aguardar cooldown
    time.sleep(1.1)

    # Tentar novamente (deve ir para HALF_OPEN)
    mock_func.side_effect = None
    mock_func.return_value = "success"

    result = cb.call(mock_func)

    assert result == "success"
    assert cb.state == CircuitState.CLOSED  # Sucesso → volta para CLOSED


def test_circuit_breaker_success_resets_counter():
    """Sucesso deve resetar contador de falhas."""
    cb = CircuitBreaker(failure_threshold=3)

    mock_func = MagicMock()

    # 2 falhas
    mock_func.side_effect = ProviderError("error")
    for _ in range(2):
        with pytest.raises(ProviderError):
            cb.call(mock_func)

    # Sucesso
    mock_func.side_effect = None
    mock_func.return_value = "ok"
    cb.call(mock_func)

    # Contador deve ter zerado
    assert cb._failure_count == 0
    assert cb.state == CircuitState.CLOSED


# ==================== METRICS TESTS ====================


def test_metrics_registered():
    """Verificar que métricas Prometheus foram registradas."""
    from app.llm.metrics import (
        llm_errors_total,
        llm_request_latency_seconds,
        llm_tokens_total,
    )

    # Verificar que objetos foram criados
    assert llm_request_latency_seconds is not None
    assert llm_tokens_total is not None
    assert llm_errors_total is not None

    # Verificar que são do tipo correto
    from prometheus_client import Counter, Histogram

    assert isinstance(llm_request_latency_seconds, Histogram)
    assert isinstance(llm_tokens_total, Counter)
    assert isinstance(llm_errors_total, Counter)
