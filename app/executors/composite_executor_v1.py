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
        self.limits = ExecutorLimits(timeout_ms=5000, max_payload_bytes=32768, max_depth=20, max_list_items=1000)

    def execute(self, req: ActionRequest) -> Any:
        try:
            payload = CompositePayload.model_validate(req.payload)
        except ValidationError:
            raise ValueError("COMPOSITE_VALIDATION")

        # Load limits and privacy
        max_steps = 8
        max_payload_bytes = 32768
        if payload.limits:
            max_steps = int(payload.limits.get("max_steps", max_steps))
            max_payload_bytes = int(payload.limits.get("max_payload_bytes", max_payload_bytes))

        strip_keys = ["prompt", "raw_prompt", "messages", "input", "context", "payload"]
        if payload.privacy and isinstance(payload.privacy.get("strip_keys"), list):
            strip_keys = payload.privacy.get("strip_keys")

        steps = payload.plan.steps
        if not steps or len(steps) == 0:
            raise ValueError("COMPOSITE_VALIDATION")
        if len(steps) > max_steps:
            raise ValueError("COMPOSITE_VALIDATION")

        # initial current payload
        current_payload: Any = payload.input

        # validate initial payload size
        try:
            initial_bytes = _bytes_of(current_payload)
        except Exception:
            raise ValueError("COMPOSITE_VALIDATION")
        if initial_bytes > max_payload_bytes:
            raise ValueError("COMPOSITE_VALIDATION")

        steps_out: List[Dict[str, Any]] = []

        for step in steps:
            # Validate step input serializability
            try:
                _ = _canonical_json(step.input)
            except Exception:
                raise ValueError("COMPOSITE_VALIDATION")

            # Resolve executor
            try:
                executor = get_executor(step.executor_id)
            except Exception:
                raise ValueError("COMPOSITE_VALIDATION")

            # Check min_executor_version
            if step.min_executor_version:
                try:
                    reg_ver = Version(getattr(executor, "version", "0.0.0"))
                    needed = Version(step.min_executor_version)
                    if reg_ver < needed:
                        raise ValueError("COMPOSITE_VALIDATION")
                except InvalidVersion:
                    raise ValueError("COMPOSITE_VALIDATION")

            # Build action request for the step
            step_input = step.input
            # Compose context: current_payload + step_input under 'input' if necessary
            # For isolation we pass step_input as payload to the executor
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
                    raise ValueError("COMPOSITE_VALIDATION")
                if not isinstance(current_payload, dict):
                    raise ValueError("COMPOSITE_VALIDATION")
                current_payload = dict(current_payload)
                current_payload[step.output_key] = step_output_sanitized
            elif step.merge == "append_results":
                if not step.output_key:
                    raise ValueError("COMPOSITE_VALIDATION")
                if not isinstance(current_payload, dict):
                    raise ValueError("COMPOSITE_VALIDATION")
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
                raise ValueError("COMPOSITE_VALIDATION")

            # Validate payload size after merge
            try:
                cur_bytes = _bytes_of(current_payload)
            except Exception:
                raise ValueError("COMPOSITE_VALIDATION")
            if cur_bytes > max_payload_bytes:
                raise ValueError("COMPOSITE_VALIDATION")

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
            "composite": {"executor_id": self.executor_id, "version": self.version, "steps_executed": len(steps_out)},
            "steps": steps_out,
            "result": current_payload,
            "result_digest": result_digest or "",
            "result_bytes": result_bytes,
        }

        return composite_out
