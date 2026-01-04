"""Circuit breaker para LLM providers (V-COF governed).

RISK-4 mitigation: Previne chamadas a provider instável.
Estados: CLOSED (normal), OPEN (falhou 3x, rejeita 60s), HALF_OPEN (teste recuperação).
"""

from __future__ import annotations

import time
from typing import Callable, Dict

from prometheus_client import Counter, Gauge


# Métricas Prometheus (RISK-7)
circuit_state_gauge = Gauge(
    "llm_circuit_breaker_state",
    "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
    ["provider"]
)

llm_requests_counter = Counter(
    "llm_requests_total",
    "Total LLM requests by status",
    ["provider", "status"]  # status: success, failed, timeout, circuit_open
)


class CircuitBreaker:
    """
    Circuit breaker pattern para LLM providers.
    
    Estados:
    - CLOSED: Normal (permite chamadas)
    - OPEN: Falhou failure_threshold vezes consecutivas (rejeita por timeout_s segundos)
    - HALF_OPEN: Teste de recuperação (permite 1 chamada tentativa)
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        timeout_s: int = 60,
        provider_name: str = "unknown",
    ):
        """
        Args:
            failure_threshold: Número de falhas consecutivas para abrir circuit
            timeout_s: Tempo em segundos que circuit permanece OPEN
            provider_name: Nome do provider (para métricas)
        """
        self.failure_threshold = failure_threshold
        self.timeout_s = timeout_s
        self.provider_name = provider_name

        self.state = "CLOSED"
        self.failures = 0
        self.last_failure_time: float | None = None

        # Inicializar métrica
        circuit_state_gauge.labels(provider=provider_name).set(0)  # 0 = CLOSED

    def call(self, func: Callable[[], Dict]) -> Dict:
        """
        Executa func se circuit permitir, senão raise.
        
        Args:
            func: Função a executar (sem argumentos, retorna Dict)
        
        Returns:
            Dict: Resultado de func() se bem-sucedido
        
        Raises:
            RuntimeError: Se circuit OPEN (provider indisponível)
        """
        # Verificar se deve transitar de OPEN para HALF_OPEN
        if self.state == "OPEN":
            elapsed = time.time() - (self.last_failure_time or 0)
            if elapsed >= self.timeout_s:
                self.state = "HALF_OPEN"
                circuit_state_gauge.labels(provider=self.provider_name).set(2)

        # Se OPEN, rejeitar imediatamente
        if self.state == "OPEN":
            llm_requests_counter.labels(provider=self.provider_name, status="circuit_open").inc()
            raise RuntimeError(f"CIRCUIT_OPEN: Provider {self.provider_name} indisponível (timeout {self.timeout_s}s)")

        # Tentar chamada (CLOSED ou HALF_OPEN)
        try:
            result = func()
            # Sucesso: resetar falhas e fechar circuit
            self.failures = 0
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                circuit_state_gauge.labels(provider=self.provider_name).set(0)
            llm_requests_counter.labels(provider=self.provider_name, status="success").inc()
            return result

        except TimeoutError as e:
            self._record_failure()
            llm_requests_counter.labels(provider=self.provider_name, status="timeout").inc()
            raise

        except RuntimeError as e:
            self._record_failure()
            llm_requests_counter.labels(provider=self.provider_name, status="failed").inc()
            raise

    def _record_failure(self) -> None:
        """Registra falha e abre circuit se atingiu threshold."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            circuit_state_gauge.labels(provider=self.provider_name).set(1)  # 1 = OPEN
