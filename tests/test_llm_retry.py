"""Testes para retry logic (RISK-3)."""

import time
from unittest.mock import Mock

import pytest

from app.llm.retry import retry_with_backoff


def test_retry_recovers_from_transient_error():
    """Retry recupera de erro temporário na 2ª tentativa."""
    mock_func = Mock(side_effect=[
        RuntimeError("PROVIDER_ERROR"),  # 1ª tentativa falha
        {"text": "success", "usage": {}, "model": "test", "latency_ms": 10}  # 2ª sucesso
    ])

    result = retry_with_backoff(
        func=mock_func,
        max_retries=2,
        base_delay_ms=10,  # delay curto para teste rápido
        timeout_s=5.0
    )

    assert result["text"] == "success"
    assert mock_func.call_count == 2


def test_retry_fails_after_max_attempts():
    """Retry falha após esgotar max_retries."""
    mock_func = Mock(side_effect=RuntimeError("PROVIDER_ERROR"))

    with pytest.raises(RuntimeError, match="MAX_RETRIES"):
        retry_with_backoff(
            func=mock_func,
            max_retries=2,
            base_delay_ms=10,
            timeout_s=5.0
        )

    assert mock_func.call_count == 3  # 1 inicial + 2 retries


def test_exponential_backoff_delays():
    """Retry aplica exponential backoff corretamente."""
    call_times = []
    
    def mock_func():
        call_times.append(time.perf_counter())
        if len(call_times) < 3:
            raise RuntimeError("PROVIDER_ERROR")
        return {"text": "success", "usage": {}, "model": "test", "latency_ms": 10}

    result = retry_with_backoff(
        func=mock_func,
        max_retries=2,
        base_delay_ms=100,  # 100ms, 200ms
        timeout_s=5.0
    )

    assert result["text"] == "success"
    assert len(call_times) == 3

    # Verificar delays aproximados (100ms ±50ms, 200ms ±50ms)
    delay1 = (call_times[1] - call_times[0]) * 1000  # em ms
    delay2 = (call_times[2] - call_times[1]) * 1000
    assert 50 < delay1 < 150, f"delay1={delay1}ms esperado ~100ms"
    assert 150 < delay2 < 250, f"delay2={delay2}ms esperado ~200ms"


def test_timeout_total_enforced():
    """Timeout total impede retries demorados."""
    def slow_func():
        time.sleep(0.5)  # 500ms cada tentativa
        raise RuntimeError("PROVIDER_ERROR")

    with pytest.raises(TimeoutError, match="TIMEOUT"):
        retry_with_backoff(
            func=slow_func,
            max_retries=5,  # Tentaria 6x * 500ms = 3s, mas timeout = 1s
            base_delay_ms=50,
            timeout_s=1.0
        )
