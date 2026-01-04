"""Testes para circuit breaker (RISK-4)."""

import time
from unittest.mock import Mock

import pytest

from app.llm.circuit_breaker import CircuitBreaker


def test_opens_after_threshold():
    """Circuit abre após failure_threshold falhas consecutivas."""
    cb = CircuitBreaker(failure_threshold=3, timeout_s=60, provider_name="test")
    mock_func = Mock(side_effect=RuntimeError("PROVIDER_ERROR"))

    # 3 falhas consecutivas
    for _ in range(3):
        with pytest.raises(RuntimeError):
            cb.call(mock_func)

    assert cb.state == "OPEN"
    assert cb.failures == 3


def test_rejects_when_open():
    """Circuit rejeita chamadas quando OPEN."""
    cb = CircuitBreaker(failure_threshold=1, timeout_s=60, provider_name="test")
    mock_func = Mock(side_effect=RuntimeError("PROVIDER_ERROR"))

    # Abrir circuit com 1 falha
    with pytest.raises(RuntimeError):
        cb.call(mock_func)

    assert cb.state == "OPEN"

    # Próxima chamada deve ser rejeitada SEM executar func
    with pytest.raises(RuntimeError, match="CIRCUIT_OPEN"):
        cb.call(mock_func)

    assert mock_func.call_count == 1  # Só executou na 1ª tentativa


def test_half_open_recovery():
    """Circuit fecha após recuperação em HALF_OPEN."""
    cb = CircuitBreaker(failure_threshold=1, timeout_s=1, provider_name="test")  # timeout curto
    mock_func = Mock(side_effect=[
        RuntimeError("PROVIDER_ERROR"),  # Abre circuit
        {"text": "success", "usage": {}, "model": "test", "latency_ms": 10}  # Recuperação
    ])

    # Abrir circuit
    with pytest.raises(RuntimeError):
        cb.call(mock_func)
    assert cb.state == "OPEN"

    # Aguardar timeout
    time.sleep(1.1)

    # Próxima chamada deve transitar para HALF_OPEN e tentar
    result = cb.call(mock_func)

    assert result["text"] == "success"
    assert cb.state == "CLOSED"  # Fechou após sucesso em HALF_OPEN
    assert cb.failures == 0
