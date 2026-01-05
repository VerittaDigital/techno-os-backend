"""Circuit breaker singleton for LLM calls (F9.10 - ENV configuration).

Provides global circuit breaker instance shared across executors.
Thread-safe, fail-closed, configured via ENV variables.
"""

from __future__ import annotations

import os
from threading import Lock

from .circuit_breaker import CircuitBreaker

# Singleton instance
_circuit_breaker_instance: CircuitBreaker | None = None
_lock = Lock()

# F9.10: Configuration via ENV (with fallback to defaults)
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("VERITTA_CB_THRESHOLD", "3"))
CIRCUIT_BREAKER_TIMEOUT = int(os.getenv("VERITTA_CB_TIMEOUT", "60"))


def get_circuit_breaker() -> CircuitBreaker:
    """Get global circuit breaker instance (thread-safe singleton).
    
    F9.10: Configuração via ENV variables:
    - VERITTA_CB_THRESHOLD: Falhas consecutivas para abrir (default: 3)
    - VERITTA_CB_TIMEOUT: Cooldown em segundos (default: 60)
    
    Returns:
        CircuitBreaker: Instância global compartilhada
    """
    global _circuit_breaker_instance

    if _circuit_breaker_instance is None:
        with _lock:
            # Double-check locking
            if _circuit_breaker_instance is None:
                _circuit_breaker_instance = CircuitBreaker(
                    failure_threshold=CIRCUIT_BREAKER_THRESHOLD,
                    timeout_s=CIRCUIT_BREAKER_TIMEOUT,
                )

    return _circuit_breaker_instance
