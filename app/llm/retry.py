"""LLM retry decorator (F9.9-B resilience layer).

Retry automático para erros temporários (429, 5xx).
- Max 2 retries
- Exponential backoff: 1s, 2s
- Retry only: 429, 5xx HTTP errors
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable

from .errors import ProviderError


def with_retry(max_retries: int = 2) -> Callable:
    """Decorator para retry automático de LLM calls.
    
    F9.9-B: Retry apenas erros temporários (429, 5xx).
    Não faz retry de timeout, 4xx (exceto 429), validation errors.
    
    Args:
        max_retries: Número máximo de retries (default 2)
        
    Raises:
        ProviderError: Se todos os retries falharem
        TimeoutError: Se timeout (sem retry)
        ConfigurationError: Se configuração inválida (sem retry)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except TimeoutError:
                    # Timeout: não faz retry (fail-fast)
                    raise
                except ProviderError as e:
                    last_error = e
                    # F9.9-B: Retry apenas se erro temporário
                    if _is_retryable(e) and attempt < max_retries:
                        delay = 2**attempt  # Exponential backoff: 1s, 2s
                        time.sleep(delay)
                        continue
                    # Erro não retryable ou última tentativa
                    raise
                except Exception as e:
                    # Outros erros: não faz retry
                    raise

            # Se chegou aqui, esgotou retries
            if last_error:
                raise last_error
            raise ProviderError("MAX_RETRIES_EXCEEDED")

        return wrapper

    return decorator


def _is_retryable(error: ProviderError) -> bool:
    """Verifica se erro é retryable (429, 5xx)."""
    msg = str(error).lower()
    # Heurística simples: detectar 429 ou 5xx na mensagem
    return "429" in msg or "rate" in msg or "5" in msg[:3]
