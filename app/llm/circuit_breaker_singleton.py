"""Circuit breaker singleton for LLM calls (F9.9-C).

Provides global circuit breaker instance shared across executors.
Thread-safe, fail-closed, configured via constants (ENV support planned for F9.10+).
"""

from __future__ import annotations

from threading import Lock

from .circuit_breaker import CircuitBreaker

# Singleton instance
_circuit_breaker_instance: CircuitBreaker | None = None
_lock = Lock()

# Configuration (F9.9-C: constants, ENV support planned for F9.10+)
CIRCUIT_BREAKER_THRESHOLD = 3  # Falhas consecutivas para abrir
CIRCUIT_BREAKER_TIMEOUT = 60  # Cooldown em segundos


def get_circuit_breaker() -> CircuitBreaker:
    """Get global circuit breaker instance (thread-safe singleton).
    
    F9.9-C: Configuração via constantes.
    Planejado para F9.10+: VERITTA_CB_THRESHOLD e VERITTA_CB_TIMEOUT via ENV.
    
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
