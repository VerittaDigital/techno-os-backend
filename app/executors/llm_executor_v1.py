from __future__ import annotations

import logging

logging.basicConfig(level=logging.ERROR)

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from app.action_contracts import ActionRequest
from app.executors.base import Executor, ExecutorLimits
from app.llm.client import LLMClient
from app.llm.factory import create_llm_client
from app.llm.policy import Policy
from app.llm.retry import with_retry
from app.llm.circuit_breaker_singleton import get_circuit_breaker
from app.tracing import observed_span


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
        # F9.9-C: Circuit breaker singleton
        self._circuit_breaker = get_circuit_breaker()

    def execute(self, req: ActionRequest) -> Any:
        # F8.6.1 FASE 3: Instrument executor at boundaries (fail-closed, wrapper-only)
        logger = logging.getLogger(__name__)
        logger.error("Executor called")
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

            # F9.9-C: Call client with retry + circuit breaker
            try:
                # Circuit breaker wrapper
                resp = self._circuit_breaker.call(
                    self._call_llm_with_retry,
                    prompt=p.prompt,
                    model=p.model,
                    max_tokens=p.max_tokens,
                )
            except TimeoutError:
                raise
            except RuntimeError:
                raise
            except Exception as e:
                # Any unexpected errors should surface as runtime error
                print(f"[LLM_EXECUTOR_ERROR] type={type(e).__name__} msg={str(e)[:200]}", flush=True)
                import traceback
                print("".join(traceback.format_exc().splitlines(True)[-20:]), flush=True)
                logger = logging.getLogger(__name__)
                logger.info(f"LLM provider error: {type(e).__name__}: {str(e)}")
                print(f"LLM provider error: {type(e).__name__}: {str(e)}")
                raise RuntimeError("PROVIDER_ERROR") from e

            # Return only the allowed fields
            return {"text": resp.get("text"), "model": resp.get("model"), "usage": resp.get("usage")}

    @with_retry(max_retries=2)
    def _call_llm_with_retry(self, *, prompt: str, model: str, max_tokens: int) -> Dict:
        """Call LLM with retry decorator (F9.9-C).
        
        Retry automático para erros temporários (429, 5xx).
        Max 2 retries conforme hardening F9.9-B.
        """
        return self._client.generate(
            prompt=prompt,
            model=model,
            temperature=Policy.TEMPERATURE,
            max_tokens=max_tokens,
            timeout_s=Policy.TIMEOUT_S,
        )
