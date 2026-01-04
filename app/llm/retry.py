"""Retry logic com exponential backoff (V-COF governed).

RISK-3 mitigation: Tenta chamada LLM com retry exponencial.
Fail-closed: Se timeout total excedido ou max retries atingido, raise.
"""

from __future__ import annotations

import time
from typing import Callable, Dict


def retry_with_backoff(
    func: Callable[[], Dict],
    max_retries: int,
    base_delay_ms: int,
    timeout_s: float,
) -> Dict:
    """
    Executa func com retry exponencial.
    
    Args:
        func: Função a executar (sem argumentos, retorna Dict)
        max_retries: Número máximo de retries (total = 1 + max_retries tentativas)
        base_delay_ms: Delay base em ms (cresce exponencialmente: base, base*2, base*4, ...)
        timeout_s: Timeout TOTAL para todas as tentativas
    
    Returns:
        Dict: Resultado de func() se bem-sucedido
    
    Raises:
        TimeoutError: Se timeout total excedido
        RuntimeError: Se todas as tentativas falharem
    """
    start_time = time.perf_counter()
    attempts = 0
    last_error: Exception | None = None

    while attempts <= max_retries:
        # Verificar timeout total ANTES de tentar
        elapsed = time.perf_counter() - start_time
        if elapsed >= timeout_s:
            raise TimeoutError(f"TIMEOUT: {timeout_s}s excedido após {attempts} tentativas")

        try:
            result = func()
            return result  # Sucesso
        except (TimeoutError, RuntimeError) as e:
            last_error = e
            attempts += 1

            # Se atingiu max retries, falha definitivamente
            if attempts > max_retries:
                raise RuntimeError(f"MAX_RETRIES: Falhou após {attempts} tentativas") from last_error

            # Calcular delay exponencial
            delay_ms = base_delay_ms * (2 ** (attempts - 1))
            delay_s = delay_ms / 1000.0

            # Verificar se delay cabe no timeout restante
            elapsed = time.perf_counter() - start_time
            remaining = timeout_s - elapsed
            if remaining < delay_s:
                # Não há tempo para esperar + tentar novamente
                raise TimeoutError(f"TIMEOUT: Sem tempo para retry {attempts} (restam {remaining:.2f}s)") from last_error

            # Aguardar antes do próximo retry
            time.sleep(delay_s)

    # Nunca deve chegar aqui (lógica above garante), mas fail-closed
    raise RuntimeError("UNEXPECTED: retry_with_backoff saiu do loop sem decisão") from last_error
