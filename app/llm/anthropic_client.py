"""Anthropic Claude client adapter for Techno OS (V-COF governed).

Integra SDK oficial Anthropic com governança V-COF:
- Timeout configurável (fail-closed)
- Rate limit respeitado
- Erros normalizados
- Privacy by design (sem log de prompts)
"""

from __future__ import annotations

import time
from typing import Dict

from .client import LLMClient


class AnthropicClient(LLMClient):
    """Anthropic Claude adapter (claude-3-opus, claude-3-sonnet, etc)."""

    def __init__(self, api_key: str, *, default_timeout_s: float = 10.0):
        """
        Args:
            api_key: Anthropic API key (ANTHROPIC_API_KEY)
            default_timeout_s: Timeout padrão para chamadas
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise RuntimeError("MISSING_DEPENDENCY: pip install anthropic")

        self._client = Anthropic(api_key=api_key, timeout=default_timeout_s)
        self._default_timeout_s = default_timeout_s

    def generate(
        self, *, prompt: str, model: str, temperature: float, max_tokens: int, timeout_s: float
    ) -> Dict:
        """Chama Anthropic Messages API."""
        t = timeout_s or self._default_timeout_s
        start = time.perf_counter()

        try:
            response = self._client.messages.create(
                model=model,  # e.g., "claude-3-opus-20240229", "claude-3-sonnet-20240229"
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                timeout=t,
            )

            latency_ms = int((time.perf_counter() - start) * 1000)

            # Normalizar resposta
            text = response.content[0].text
            usage = {
                "prompt": response.usage.input_tokens,
                "completion": response.usage.output_tokens,
                "total": response.usage.input_tokens + response.usage.output_tokens,
            }

            return {"text": text, "usage": usage, "model": model, "latency_ms": latency_ms}

        except TimeoutError:
            raise TimeoutError()
        except Exception as e:
            # Normalizar todos os erros para PROVIDER_ERROR (fail-closed)
            raise RuntimeError("PROVIDER_ERROR") from e
