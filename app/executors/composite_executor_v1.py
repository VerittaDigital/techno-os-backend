from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from packaging.version import Version, InvalidVersion
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.action_contracts import ActionRequest
from app.digests import sha256_json_or_none
from app.executors.base import Executor, ExecutorLimits
from app.executors.registry import get_executor


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _bytes_of(obj: Any) -> int:
    return len(_canonical_json(obj).encode("utf-8"))


def _sanitize(obj: Any, strip_keys: List[str]) -> Any:
    """Recursively remove keys in strip_keys from dicts inside obj."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in strip_keys:
                continue
            out[k] = _sanitize(v, strip_keys)
        return out
    if isinstance(obj, list):
        return [_sanitize(v, strip_keys) for v in obj]
    return obj


class StepSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    executor_id: str
    min_executor_version: Optional[str] = None
    input: dict
    merge: str = Field(...)
    output_key: Optional[str] = None


class PlanSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    steps: List[StepSpec]


class CompositePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan: PlanSpec
    input: dict
    limits: Optional[dict] = None
    privacy: Optional[dict] = None


class CompositeExecutorV1(Executor):
    def __init__(self):
        self.executor_id = "composite_executor_v1"
        self.version = "1.0.0"
        self.capabilities: list[str] = []
        # conservative limits; not used by pipeline but for local checks
        # Ensure pipeline does not pre-block composite runs; composite enforces global limits itself
        self.limits = ExecutorLimits(timeout_ms=5000, max_payload_bytes=10_000_000, max_depth=20, max_list_items=1000)

    def execute(self, req: ActionRequest) -> Any:
        try:
            payload = CompositePayload.model_validate(req.payload)
        except ValidationError:
            raise ValueError("PLAN_VALIDATION")

        # Pre-run: compute plan digest and enforce global plan limits
        try:
            plan_obj = req.payload.get("plan")
            plan_digest = sha256_json_or_none(plan_obj) or ""
            declared_plan_canonical = _canonical_json(plan_obj)
            declared_input_canonical = _canonical_json(req.payload.get("input"))
        except Exception:
            raise ValueError("PLAN_VALIDATION")

        # Defaults
        max_steps = 8
        max_total_payload_bytes = 65536
        max_llm_calls = None
        if payload.limits:
            max_steps = int(payload.limits.get("max_steps", max_steps))
            max_total_payload_bytes = int(payload.limits.get("max_total_payload_bytes", max_total_payload_bytes))
            max_llm_calls = payload.limits.get("max_llm_calls")

        # Validate declared sizes
        declared_bytes = len((declared_plan_canonical + declared_input_canonical).encode("utf-8"))
        if declared_bytes > max_total_payload_bytes:
            raise ValueError("PLAN_VALIDATION")

        # Count declared LLM calls by resolving executors (capabilities or id)
        declared_llm_calls = 0
        for s in payload.plan.steps:
            try:
                exe = get_executor(s.executor_id)
                caps = getattr(exe, "capabilities", []) or []
                # case-insensitive match for LLM capability
                if any(str(c).upper() == "LLM" for c in caps) or str(s.executor_id).startswith("llm_executor"):
                    declared_llm_calls += 1
            except Exception:
                # If executor can't be resolved, treat as validation failure
                raise ValueError("PLAN_VALIDATION")

        if max_llm_calls is not None and declared_llm_calls > int(max_llm_calls):
            raise ValueError("PLAN_VALIDATION")

        # Validate steps count
        steps = payload.plan.steps
        if not steps or len(steps) == 0:
            raise ValueError("PLAN_VALIDATION")
        if len(steps) > max_steps:
            raise ValueError("PLAN_VALIDATION")

        # Validate each step input serializability and min_executor_version BEFORE running any step
        for step in steps:
            try:
                _ = _canonical_json(step.input)
            except Exception:
                raise ValueError("PLAN_VALIDATION")

            if step.min_executor_version:
                try:
                    exe = get_executor(step.executor_id)
                    from packaging.version import Version

                    reg_ver = Version(getattr(exe, "version", "0.0.0"))
                    needed = Version(step.min_executor_version)
                    if reg_ver < needed:
                        raise ValueError("PLAN_VALIDATION")
                except Exception:
                    raise ValueError("PLAN_VALIDATION")

        # Privacy sanitization keys
        strip_keys = ["prompt", "raw_prompt", "messages", "input", "context", "payload"]
        if payload.privacy and isinstance(payload.privacy.get("strip_keys"), list):
            strip_keys = payload.privacy.get("strip_keys")

        # initial current payload
        current_payload: Any = payload.input

        # validate initial payload size (runtime check)
        try:
            initial_bytes = _bytes_of(current_payload)
        except Exception:
            raise ValueError("PLAN_VALIDATION")
        if initial_bytes > max_total_payload_bytes:
            raise ValueError("PLAN_VALIDATION")

        steps_out: List[Dict[str, Any]] = []

        for step in steps:
            # Resolve executor
            try:
                executor = get_executor(step.executor_id)
            except Exception:
                raise ValueError("PLAN_VALIDATION")

            # Build action request for the step
            step_input = step.input
            action_req = ActionRequest(action=step.name, payload=step_input, trace_id=req.trace_id)

            # Execute step (fail-closed semantics)
            try:
                raw_out = executor.execute(action_req)
            except Exception:
                raise RuntimeError(f"COMPOSITE_STEP_FAILED:{step.name}")

            # Normalize step_output
            step_output_normalized = raw_out if raw_out is not None else {}

            # Sanitization before digest/merge
            step_output_sanitized = _sanitize(step_output_normalized, strip_keys)

            # Check serializability
            try:
                canonical = _canonical_json(step_output_sanitized)
            except Exception:
                raise RuntimeError(f"COMPOSITE_STEP_FAILED:{step.name}")

            output_digest = sha256_json_or_none(step_output_sanitized)
            output_bytes = len(canonical.encode("utf-8"))

            # Merge semantics
            if step.merge == "replace":
                current_payload = step_output_sanitized
            elif step.merge == "merge_under":
                if not step.output_key:
                    raise ValueError("PLAN_VALIDATION")
                if not isinstance(current_payload, dict):
                    raise ValueError("PLAN_VALIDATION")
                current_payload = dict(current_payload)
                current_payload[step.output_key] = step_output_sanitized
            elif step.merge == "append_results":
                if not step.output_key:
                    raise ValueError("PLAN_VALIDATION")
                if not isinstance(current_payload, dict):
                    raise ValueError("PLAN_VALIDATION")
                current_payload = dict(current_payload)
                existing = current_payload.get(step.output_key)
                if existing is None:
                    current_payload[step.output_key] = [step_output_sanitized]
                elif isinstance(existing, list):
                    current_payload[step.output_key] = existing + [step_output_sanitized]
                else:
                    # convert to list
                    current_payload[step.output_key] = [existing, step_output_sanitized]
            else:
                raise ValueError("PLAN_VALIDATION")

            # Validate payload size after merge (runtime enforcement against global limit)
            try:
                cur_bytes = _bytes_of(current_payload)
            except Exception:
                raise ValueError("PLAN_VALIDATION")
            if cur_bytes > max_total_payload_bytes:
                raise ValueError("PLAN_VALIDATION")

            steps_out.append({
                "name": step.name,
                "executor_id": step.executor_id,
                "status": "SUCCESS",
                "output_digest": output_digest or "",
                "output_bytes": output_bytes,
            })

        # Final result digest/bytes
        try:
            result_canonical = _canonical_json(current_payload)
        except Exception:
            raise RuntimeError("COMPOSITE_STEP_FAILED:finalization")
        result_digest = sha256_json_or_none(current_payload)
        result_bytes = len(result_canonical.encode("utf-8"))

        composite_out = {
            "plan": {"digest": plan_digest or "", "steps_declared": len(steps), "llm_calls_declared": declared_llm_calls},
            "composite": {"executor_id": self.executor_id, "version": self.version, "steps_executed": len(steps_out)},
            "steps": steps_out,
            "result": current_payload,
            "result_digest": result_digest or "",
            "result_bytes": result_bytes,
        }

        return composite_out
