"""Rate limiter por provider (V-COF governed).

RISK-5 mitigation: Respeita limites de API (previne 429 errors).
Algoritmo: Token bucket com reposição contínua.
"""

from __future__ import annotations

import threading
import time


class RateLimiter:
    """
    Token bucket rate limiter por provider.
    
    Limites (requests por minuto):
    - OpenAI: 10 req/min
    - Anthropic: 5 req/min
    - Gemini: 60 req/min
    - Grok: 10 req/min
    - DeepSeek: 5 req/min
    - fake: sem limite (testes)
    """

    LIMITS = {
        "openai": 10,
        "anthropic": 5,
        "gemini": 60,
        "grok": 10,
        "deepseek": 5,
        "fake": 1000,  # Sem limite prático para testes
    }

    def __init__(self):
        # Estado por provider: {"provider": {"tokens": float, "last_update": float}}
        self._state: dict[str, dict] = {}
        self._lock = threading.Lock()

    def acquire(self, provider: str) -> None:
        """
        Adquire token para provider. Bloqueia até token disponível.
        
        Args:
            provider: Nome do provider ("openai", "anthropic", etc.)
        """
        limit = self.LIMITS.get(provider, 10)  # Default 10 req/min
        
        with self._lock:
            now = time.time()

            # Inicializar estado se primeira vez
            if provider not in self._state:
                self._state[provider] = {
                    "tokens": float(limit),
                    "last_update": now
                }

            state = self._state[provider]

            # Repor tokens baseado no tempo decorrido
            elapsed = now - state["last_update"]
            tokens_to_add = elapsed * (limit / 60.0)  # tokens por segundo
            state["tokens"] = min(limit, state["tokens"] + tokens_to_add)
            state["last_update"] = now

            # Se não há token, calcular quanto tempo esperar
            if state["tokens"] < 1.0:
                wait_time = (1.0 - state["tokens"]) / (limit / 60.0)
                # Liberar lock durante sleep (permite outros providers)
                self._lock.release()
                time.sleep(wait_time)
                self._lock.acquire()

                # Atualizar tokens após sleep
                now = time.time()
                elapsed = now - state["last_update"]
                tokens_to_add = elapsed * (limit / 60.0)
                state["tokens"] = min(limit, state["tokens"] + tokens_to_add)
                state["last_update"] = now

            # Consumir 1 token
            state["tokens"] -= 1.0
