from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from app.action_contracts import ActionRequest
from app.executors.base import Executor, ExecutorLimits
from app.llm.client import LLMClient
from app.llm.factory import create_llm_client
from app.llm.policy import Policy
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

            # Call client (must raise on errors)
            try:
                resp = self._client.generate(
                    prompt=p.prompt,
                    model=p.model,
                    temperature=Policy.TEMPERATURE,
                    max_tokens=p.max_tokens,
                    timeout_s=Policy.TIMEOUT_S,
                )
            except TimeoutError:
                raise
            except RuntimeError:
                raise
            except Exception as e:
                # Any unexpected errors should surface as runtime error
                raise RuntimeError("PROVIDER_ERROR") from e

            # Return only the allowed fields
            return {"text": resp.get("text"), "model": resp.get("model"), "usage": resp.get("usage")}
