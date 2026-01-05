"""OpenAI client adapter for Techno OS (V-COF governed).

Integra SDK oficial OpenAI com governança V-COF:
- Timeout configurável (fail-closed)
- Rate limit respeitado
- Erros normalizados
- Privacy by design (sem log de prompts)
- F9.9-B: Retorna LLMResponse Pydantic + Prometheus metrics
"""

from __future__ import annotations

import time
from typing import Dict

from .client import LLMClient
from .response import LLMResponse, TokenUsage
from .errors import ProviderError
from .metrics import llm_request_latency_seconds, llm_tokens_total, llm_errors_total


class OpenAIClient(LLMClient):
    """OpenAI GPT adapter (gpt-4, gpt-3.5-turbo, etc)."""

    def __init__(self, api_key: str, *, default_timeout_s: float = 30.0):
        """
        Args:
            api_key: OpenAI API key (OPENAI_API_KEY)
            default_timeout_s: Timeout padrão (30s conforme F9.9-B)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("MISSING_DEPENDENCY: pip install openai")

        self._client = OpenAI(api_key=api_key, timeout=default_timeout_s)
        self._default_timeout_s = default_timeout_s

    def generate(
        self, *, prompt: str, model: str, temperature: float, max_tokens: int, timeout_s: float
    ) -> Dict:
        """Chama OpenAI Chat Completions API (retorna dict para compatibilidade).
        
        F9.9-B: Instrumentado com Prometheus metrics.
        """
        t = timeout_s or self._default_timeout_s
        start = time.perf_counter()

        try:
            response = self._client.chat.completions.create(
                model=model,  # e.g., "gpt-4", "gpt-3.5-turbo"
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=t,
            )

            print(f"[OPENAI_CLIENT] response type: {type(response)}", flush=True)

            latency_ms = (time.perf_counter() - start) * 1000

            # F9.9-B: Construir LLMResponse normalizado
            try:
                text = response.choices[0].message.content or ""
            except Exception as e:
                print(f"[OPENAI_CLIENT_PARSE_ERROR] type={type(e).__name__} msg={str(e)[:200]}", flush=True)
                raise

            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            
            llm_response = LLMResponse(
                text=text,
                model=model,
                usage=usage,
                latency_ms=latency_ms,
                provider="openai",
            )
            
            # F9.9-B: Prometheus metrics
            llm_request_latency_seconds.labels(provider="openai", model=model).observe(
                latency_ms / 1000
            )
            if usage:
                llm_tokens_total.labels(provider="openai", model=model, type="prompt").inc(
                    usage.prompt_tokens
                )
                llm_tokens_total.labels(provider="openai", model=model, type="completion").inc(
                    usage.completion_tokens
                )
            
            # Retornar como dict para compatibilidade com contrato atual
            return {
                "text": llm_response.text,
                "model": llm_response.model,
                "usage": {
                    "prompt": llm_response.usage.prompt_tokens,
                    "completion": llm_response.usage.completion_tokens,
                    "total": llm_response.usage.total_tokens,
                } if llm_response.usage else None,
                "latency_ms": llm_response.latency_ms,
            }

        except TimeoutError:
            # F9.9-B: Métrica de timeout
            llm_errors_total.labels(provider="openai", error_type="timeout").inc()
            raise TimeoutError()
        except Exception as e:
            # F9.9-B: Métrica de provider error + usar ProviderError consistente
            llm_errors_total.labels(provider="openai", error_type="provider_error").inc()
            raise ProviderError("PROVIDER_ERROR") from e
