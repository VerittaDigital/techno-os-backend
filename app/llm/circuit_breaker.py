"""Circuit Breaker for LLM calls (F9.9-B resilience layer).

Implementa circuit breaker para proteger sistema de falhas em cascata.
- 3 falhas consecutivas → open (60s cooldown)
- Estados: CLOSED, OPEN, HALF_OPEN
- Thread-safe (threading.Lock)
"""

from __future__ import annotations

import logging

logging.basicConfig(level=logging.ERROR)

import time
from enum import Enum
from threading import Lock
from typing import Any, Callable

from .errors import ProviderError


class CircuitState(Enum):
    """Estados do circuit breaker."""

    CLOSED = "closed"  # Operação normal
    OPEN = "open"  # Bloqueio ativo (falhas detectadas)
    HALF_OPEN = "half_open"  # Tentativa de recuperação


class CircuitBreaker:
    """Circuit breaker para LLM calls (F9.9-B).
    
    Protege sistema contra falhas em cascata:
    - CLOSED: operação normal
    - 3 falhas consecutivas → OPEN (60s cooldown)
    - Após cooldown → HALF_OPEN (1 tentativa)
    - Sucesso em HALF_OPEN → CLOSED
    - Falha em HALF_OPEN → OPEN novamente
    """

    def __init__(self, failure_threshold: int = 3, timeout_s: int = 60):
        """
        Args:
            failure_threshold: Falhas consecutivas para abrir circuito (default 3)
            timeout_s: Tempo de cooldown em OPEN state (default 60s)
        """
        self._failure_threshold = failure_threshold
        self._timeout_s = timeout_s
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time: float = 0
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state (thread-safe)."""
        with self._lock:
            return self._state

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Executa função com circuit breaker protection.
        
        Raises:
            ProviderError: Se circuito aberto ou função falhar
        """
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Verificar se cooldown expirou
                if time.time() - self._last_failure_time >= self._timeout_s:
                    self._state = CircuitState.HALF_OPEN
                    self._failure_count = 0
                else:
                    logging.error(f"Circuit breaker open: too many failures, retry later")
                    print(f"Circuit breaker open: too many failures, retry later")
                    raise ProviderError("CIRCUIT_OPEN: Too many failures, retry later")

        # Executar função
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Callback de sucesso (thread-safe)."""
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        """Callback de falha (thread-safe)."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self._failure_threshold:
                self._state = CircuitState.OPEN
