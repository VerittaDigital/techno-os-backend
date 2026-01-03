"""DeepSeek client adapter for Techno OS (V-COF governed).

Integra DeepSeek API (OpenAI-compatible) com governança V-COF:
- Timeout configurável (fail-closed)
- Rate limit respeitado
- Erros normalizados
- Privacy by design (sem log de prompts)
"""

from __future__ import annotations

import time
from typing import Dict

from .client import LLMClient


class DeepSeekClient(LLMClient):
    """DeepSeek adapter (deepseek-chat, deepseek-coder, etc)."""

    def __init__(self, api_key: str, *, default_timeout_s: float = 10.0):
        """
        Args:
            api_key: DeepSeek API key (DEEPSEEK_API_KEY)
            default_timeout_s: Timeout padrão para chamadas
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("MISSING_DEPENDENCY: pip install openai")

        # DeepSeek usa API compatível com OpenAI, mas com base_url customizada
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",  # Endpoint DeepSeek
            timeout=default_timeout_s,
        )
        self._default_timeout_s = default_timeout_s

    def generate(
        self, *, prompt: str, model: str, temperature: float, max_tokens: int, timeout_s: float
    ) -> Dict:
        """Chama DeepSeek API (OpenAI-compatible)."""
        t = timeout_s or self._default_timeout_s
        start = time.perf_counter()

        try:
            response = self._client.chat.completions.create(
                model=model,  # e.g., "deepseek-chat", "deepseek-coder"
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=t,
            )

            latency_ms = int((time.perf_counter() - start) * 1000)

            # Normalizar resposta (idêntico ao OpenAI)
            text = response.choices[0].message.content
            usage = {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens,
            }

            return {"text": text, "usage": usage, "model": model, "latency_ms": latency_ms}

        except TimeoutError:
            raise TimeoutError()
        except Exception as e:
            # Normalizar todos os erros para PROVIDER_ERROR (fail-closed)
            raise RuntimeError("PROVIDER_ERROR") from e
