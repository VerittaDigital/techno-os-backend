"""Provider fallback strategy (V-COF governed).

RISK-8 mitigation: Fallback automático entre providers.
Strategy B (conforme parecer): Log warning + continue para próximo provider.
"""

from __future__ import annotations

import logging
from typing import Dict

from app.llm.factory import create_llm_client, get_circuit_breaker
from app.llm.retry import retry_with_backoff
from app.llm.policy import Policy

logger = logging.getLogger(__name__)


class ProviderFallback:
    """
    Fallback automático entre providers.
    
    Strategy B: Log warning quando primary falha, tenta secondary transparentemente.
    """

    def __init__(self):
        self.providers_attempted: list[str] = []

    def try_providers(
        self,
        prompt: str,
        model_map: Dict[str, str],  # {"openai": "gpt-4", "anthropic": "claude-3-opus"}
        temperature: float,
        max_tokens: int,
    ) -> Dict:
        """
        Tenta providers em ordem até sucesso.
        
        Args:
            prompt: Texto do prompt
            model_map: Mapeamento provider → model
            temperature: Temperatura (0-1)
            max_tokens: Máximo de tokens
        
        Returns:
            Dict: Resultado do provider que teve sucesso
        
        Raises:
            RuntimeError: Se todos os providers falharem
        """
        self.providers_attempted = []
        last_error: Exception | None = None

        for provider, model in model_map.items():
            self.providers_attempted.append(provider)

            try:
                # Verificar circuit breaker antes de tentar
                cb = get_circuit_breaker(provider)
                if cb.state == "OPEN":
                    logger.warning(f"FALLBACK: Pulando {provider} (circuit OPEN)")
                    continue

                # Criar client para provider
                client = create_llm_client(provider=provider)

                # Tentar com retry + circuit breaker
                result = cb.call(
                    lambda: retry_with_backoff(
                        func=lambda: client.generate(
                            prompt=prompt,
                            model=model,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            timeout_s=Policy.TIMEOUT_S
                        ),
                        max_retries=Policy.MAX_RETRIES,
                        base_delay_ms=Policy.RETRY_BASE_DELAY_MS,
                        timeout_s=Policy.TIMEOUT_S
                    )
                )

                # Sucesso: log se não foi primary
                if len(self.providers_attempted) > 1:
                    logger.warning(
                        f"FALLBACK: Primary provider(s) falharam, sucesso com {provider}. "
                        f"Tentativas: {', '.join(self.providers_attempted)}"
                    )

                return result

            except (TimeoutError, RuntimeError) as e:
                last_error = e
                logger.warning(f"FALLBACK: Provider {provider} falhou ({e}), tentando próximo...")
                continue

        # Todos os providers falharam
        raise RuntimeError(
            f"ALL_PROVIDERS_FAILED: Tentados {len(self.providers_attempted)} providers "
            f"({', '.join(self.providers_attempted)}). Último erro: {last_error}"
        )
