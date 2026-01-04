from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from app.action_contracts import ActionRequest
from app.executors.base import Executor, ExecutorLimits
from app.llm.client import LLMClient
from app.llm.factory import create_llm_client, get_circuit_breaker
from app.llm.policy import Policy
from app.llm.rate_limiter import RateLimiter
from app.llm.retry import retry_with_backoff
from app.tracing import observed_span


# Instância global de rate limiter (singleton)
_rate_limiter = RateLimiter()


class _Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str
    model: str
    max_tokens: int = Field(...)


class LLMExecutorV1(Executor):
    def __init__(self, *, client: LLMClient | None = None):
        self.executor_id = "llm_executor_v1"
        self.version = "1.0.0"
        self.capabilities: list[str] = []
        self.limits = ExecutorLimits(
            timeout_ms=int(Policy.TIMEOUT_S * 1000),
            max_payload_bytes=Policy.MAX_PROMPT_CHARS,
            max_depth=10,
            max_list_items=100,
        )
        # Usar factory se client não injetado (respeita LLM_PROVIDER env)
        self._client = client if client is not None else create_llm_client()

    def execute(self, req: ActionRequest) -> Any:
        # F8.6.1 FASE 3: Instrument executor at boundaries (fail-closed, wrapper-only)
        with observed_span(
            f"executor.{self.executor_id}",
            attributes={
                "executor_name": self.executor_id,
                "action": getattr(req, "action", "unknown"),
                "trace_id": getattr(req, "trace_id", "unknown"),
            }
        ):
            # Strict payload validation
            try:
                p = _Payload.model_validate(req.payload)
            except Exception as e:
                raise ValueError("INVALID_PAYLOAD") from e

            # Policy validation (hard governance)
            try:
                Policy.validate(prompt=p.prompt, model=p.model, max_tokens=p.max_tokens, timeout_s=Policy.TIMEOUT_S)
            except ValueError:
                raise ValueError("POLICY_VIOLATION")

            # Detectar provider do client atual
            provider_name = getattr(self._client, "__class__.__name__", "unknown").replace("Client", "").lower()
            if provider_name not in ["openai", "anthropic", "gemini", "grok", "deepseek", "fake"]:
                provider_name = "unknown"

            # RISK-3, RISK-4, RISK-5, RISK-6: Retry + Circuit Breaker + Rate Limiting + Fail-closed
            try:
                # RISK-5: Rate limiting (bloqueia se necessário)
                _rate_limiter.acquire(provider_name)

                # RISK-4: Circuit breaker por provider
                cb = get_circuit_breaker(provider_name)

                # RISK-3 + RISK-4: Retry com circuit breaker
                resp = cb.call(
                    lambda: retry_with_backoff(
                        func=lambda: self._client.generate(
                            prompt=p.prompt,
                            model=p.model,
                            temperature=Policy.TEMPERATURE,
                            max_tokens=p.max_tokens,
                            timeout_s=Policy.TIMEOUT_S
                        ),
                        max_retries=Policy.MAX_RETRIES,
                        base_delay_ms=Policy.RETRY_BASE_DELAY_MS,
                        timeout_s=Policy.TIMEOUT_S
                    )
                )

                # Return only the allowed fields
                return {"text": resp.get("text"), "model": resp.get("model"), "usage": resp.get("usage")}

            except (TimeoutError, RuntimeError) as e:
                # RISK-6: Fail-closed enforcement
                # NUNCA retornar data parcial ou "try anyway"
                # Reraising para pipeline tratar como FAILED
                raise
