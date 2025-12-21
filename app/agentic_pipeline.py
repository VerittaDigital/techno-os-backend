"""
Agentic pipeline with V-COF governance (AG-03: Action Versioning & Executor Capabilities).

This pipeline orchestrates:
1. Payload validation (Gate)
2. Action version check (AG-03)
3. Executor resolution (AG-03) 
4. Executor capability & version check (AG-03)
5. Payload limit enforcement
6. Executor invocation
7. Audit logging

Supports legacy actions for retrocompatibility while enforcing AG-03 for new actions.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from app.action_audit_log import log_action_result
from app.action_contracts import ActionRequest, ActionResult
from app.action_registry import get_action_registry
from app.action_router import route_action as route_action_deterministic
from app.executors.registry import get_executor
from app.executors.registry import UnknownExecutorError


# Legacy actions exempt from strict AG-03 version/capability checks
LEGACY_ACTIONS = {"process"}

# Semver pattern: X.Y.Z
SEMVER_PATTERN = re.compile(r'^\d+\.\d+\.\d+$')


def route_action(action: str) -> str:
    """Wrapper for test compatibility. Delegates to imported route_action_deterministic."""
    return route_action_deterministic(action)


def _normalize_capabilities(caps):
    """Normalize capability list (uppercase, deduplicate, sort)."""
    if not caps:
        return []
    return sorted(set(c.strip().upper() for c in caps if c.strip()))


def _is_valid_semver(version_str):
    """Check if version string matches semantic versioning (X.Y.Z)."""
    return bool(SEMVER_PATTERN.match(version_str))


def _compute_input_digest(payload: Dict[str, Any]) -> Optional[str]:
    """Compute SHA256 digest of payload. Return None if payload is not JSON-serializable."""
    try:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    except (TypeError, ValueError):
        # Payload contains non-JSON-serializable objects
        return None


def _compute_output_digest(output: Any) -> Optional[str]:
    """Compute SHA256 digest of output, or None if no output."""
    if output is None:
        return None
    try:
        canonical = json.dumps(output, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    except TypeError:
        # Non-serializable output
        return None


def run_agentic_action(
    action: str,
    payload: Dict[str, Any],
    trace_id: str,
    executor_id: str = "unknown",
    executor_version: str = "unknown",
) -> Tuple[ActionResult, Optional[Any]]:
    """
    Run action through governance pipeline.
    
    Returns:
        (ActionResult, output) where output is None on BLOCKED/FAILED
    """
    
    # Step 1: Route action to executor_id (if not explicitly provided)
    action_routed = False
    if executor_id == "unknown":
        try:
            # Try deterministic router first (used in tests)
            executor_id = route_action_deterministic(action)
            action_routed = True
        except Exception:
            # Fall back to action registry metadata if not found
            try:
                registry = get_action_registry()
                action_meta = registry.actions.get(action)
                if action_meta and isinstance(action_meta, dict):
                    executor_id = action_meta.get("executor", "unknown")
                    action_routed = (executor_id != "unknown")
            except Exception:
                pass
    
    # Compute input digest for audit (returns None if not JSON-serializable)
    input_digest = _compute_input_digest(payload)
    output_digest = None
    output = None
    
    # If payload is not JSON-serializable, block immediately
    if input_digest is None:
        status = "BLOCKED"
        reason_codes = ["NON_JSON_PAYLOAD"]
        result = ActionResult(
            action=action,
            executor_id=executor_id,
            executor_version=executor_version,
            status=status,
            reason_codes=reason_codes,
            input_digest=input_digest or "",
            output_digest=output_digest,
            trace_id=trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        log_action_result(result)
        return (result, None)
    
    # Step 3: Get action metadata from registry (ALWAYS, not skipped)
    action_meta = None
    try:
        registry = get_action_registry()
        action_meta = registry.actions.get(action)
    except Exception:
        # Registry not available - proceed with routing only
        pass
    
    # Step 3A: Validate action exists (if we have registry)
    if action_meta is None and not action_routed:
        # Action not in registry and not routed successfully
        status = "BLOCKED"
        reason_codes = ["ACTION_UNKNOWN"]
        result = ActionResult(
            action=action,
            executor_id=executor_id,
            executor_version="unknown",
            status=status,
            reason_codes=reason_codes,
            input_digest=input_digest,
            output_digest=output_digest,
            trace_id=trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        log_action_result(result)
        return (result, None)
    
    # Step 3B: Validate action_version (ALWAYS for non-legacy, never skip)
    if action_meta is not None:
        action_version = action_meta.get("action_version")
        if action_version is None:
            if action not in LEGACY_ACTIONS:
                status = "BLOCKED"
                reason_codes = ["ACTION_VERSION_MISSING"]
                result = ActionResult(
                    action=action,
                    executor_id=executor_id,
                    executor_version="unknown",
                    status=status,
                    reason_codes=reason_codes,
                    input_digest=input_digest,
                    output_digest=output_digest,
                    trace_id=trace_id,
                    ts_utc=datetime.now(timezone.utc),
                )
                log_action_result(result)
                return (result, None)
        elif not _is_valid_semver(action_version):
            status = "BLOCKED"
            reason_codes = ["ACTION_VERSION_INVALID"]
            result = ActionResult(
                action=action,
                executor_id=executor_id,
                executor_version="unknown",
                status=status,
                reason_codes=reason_codes,
                input_digest=input_digest,
                output_digest=output_digest,
                trace_id=trace_id,
                ts_utc=datetime.now(timezone.utc),
            )
            log_action_result(result)
            return (result, None)
    
    # Step 4: Resolve executor (needed for capability and limit checks below)
    executor = None
    try:
        executor = get_executor(executor_id)
        # Ensure executor_version is a string (not MagicMock)
        exec_version_raw = getattr(executor, "version", None)
        if isinstance(exec_version_raw, str):
            executor_version = exec_version_raw
        else:
            executor_version = None
    except UnknownExecutorError:
        status = "BLOCKED"
        reason_codes = ["EXECUTOR_NOT_FOUND"]
        result = ActionResult(
            action=action,
            executor_id=executor_id,
            executor_version="unknown",
            status=status,
            reason_codes=reason_codes,
            input_digest=input_digest,
            output_digest=output_digest,
            trace_id=trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        log_action_result(result)
        return (result, None)
    
    # Step 4A: Validate executor version (AG-03)
    # Only check min_executor_version for non-legacy actions
    if action_meta and action not in LEGACY_ACTIONS:
        min_executor_version = action_meta.get("min_executor_version")
        if min_executor_version is not None:
            if executor_version is None:
                status = "BLOCKED"
                reason_codes = ["EXECUTOR_VERSION_MISSING"]
                result = ActionResult(
                    action=action,
                    executor_id=executor_id,
                    executor_version="unknown",
                    status=status,
                    reason_codes=reason_codes,
                    input_digest=input_digest,
                    output_digest=output_digest,
                    trace_id=trace_id,
                    ts_utc=datetime.now(timezone.utc),
                )
                log_action_result(result)
                return (result, None)
            elif executor_version < min_executor_version:
                status = "BLOCKED"
                reason_codes = ["EXECUTOR_VERSION_INCOMPATIBLE"]
                result = ActionResult(
                    action=action,
                    executor_id=executor_id,
                    executor_version=executor_version,
                    status=status,
                    reason_codes=reason_codes,
                    input_digest=input_digest,
                    output_digest=output_digest,
                    trace_id=trace_id,
                    ts_utc=datetime.now(timezone.utc),
                )
                log_action_result(result)
                return (result, None)

    # Step 4B: Validate executor capabilities (AG-03)
    # Check that executor has all required_capabilities
    if action_meta and action not in LEGACY_ACTIONS:
        required_capabilities = action_meta.get("required_capabilities", [])
        if required_capabilities:
            executor_capabilities = getattr(executor, "capabilities", None)
            
            # If executor has no capabilities attribute at all -> MISSING
            if executor_capabilities is None:
                status = "BLOCKED"
                reason_codes = ["EXECUTOR_CAPABILITY_MISSING"]
                result = ActionResult(
                    action=action,
                    executor_id=executor_id,
                    executor_version=executor_version or "unknown",
                    status=status,
                    reason_codes=reason_codes,
                    input_digest=input_digest,
                    output_digest=output_digest,
                    trace_id=trace_id,
                    ts_utc=datetime.now(timezone.utc),
                )
                log_action_result(result)
                return (result, None)
            
            # If executor has capabilities but insufficient -> MISMATCH
            normalized_executor_caps = _normalize_capabilities(executor_capabilities)
            normalized_required_caps = _normalize_capabilities(required_capabilities)

            missing_capabilities = set(normalized_required_caps) - set(normalized_executor_caps)
            if missing_capabilities:
                status = "BLOCKED"
                reason_codes = ["EXECUTOR_CAPABILITY_MISMATCH"]
                result = ActionResult(
                    action=action,
                    executor_id=executor_id,
                    executor_version=executor_version or "unknown",
                    status=status,
                    reason_codes=reason_codes,
                    input_digest=input_digest,
                    output_digest=output_digest,
                    trace_id=trace_id,
                    ts_utc=datetime.now(timezone.utc),
                )
                log_action_result(result)
                return (result, None)

    # Step 5: Enforce payload limits
    try:
        from app.payload_limits import check_payload_limits, LimitExceeded
        check_payload_limits(
            payload,
            max_bytes=executor.limits.max_payload_bytes,
            max_depth_limit=executor.limits.max_depth,
            max_list_limit=executor.limits.max_list_items,
        )
    except TypeError:
        # Non-JSON-serializable payload
        status = "BLOCKED"
        reason_codes = ["NON_JSON_PAYLOAD"]
        result = ActionResult(
            action=action,
            executor_id=executor_id,
            executor_version=executor_version,
            status=status,
            reason_codes=reason_codes,
            input_digest=input_digest,
            output_digest=output_digest,
            trace_id=trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        log_action_result(result)
        return (result, None)
    except LimitExceeded:
        status = "BLOCKED"
        reason_codes = ["LIMIT_EXCEEDED"]
        result = ActionResult(
            action=action,
            executor_id=executor_id,
            executor_version=executor_version,
            status=status,
            reason_codes=reason_codes,
            input_digest=input_digest,
            output_digest=output_digest,
            trace_id=trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        log_action_result(result)
        return (result, None)

    # Step 6: Execute executor
    try:
        # Create ActionRequest
        action_req = ActionRequest(
            action=action,
            payload=payload,
            trace_id=trace_id,
        )
        output = executor.execute(action_req)
    except TimeoutError:
        # Simulated timeout (for tests; real timeout requires async)
        status = "FAILED"
        reason_codes = ["EXECUTOR_TIMEOUT"]
        result = ActionResult(
            action=action,
            executor_id=executor_id,
            executor_version=executor_version,
            status=status,
            reason_codes=reason_codes,
            input_digest=input_digest,
            output_digest=output_digest,
            trace_id=trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        log_action_result(result)
        return (result, None)
    except Exception as e:
        # Any other exception during execution
        status = "FAILED"
        reason_codes = ["EXECUTOR_EXCEPTION"]
        result = ActionResult(
            action=action,
            executor_id=executor_id,
            executor_version=executor_version,
            status=status,
            reason_codes=reason_codes,
            input_digest=input_digest,
            output_digest=output_digest,
            trace_id=trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        log_action_result(result)
        return (result, None)

    # Step 7: Success — Compute output digest and return
    output_digest = _compute_output_digest(output)
    status = "SUCCESS"
    reason_codes = []
    result = ActionResult(
        action=action,
        executor_id=executor_id,
        executor_version=executor_version,
        status=status,
        reason_codes=reason_codes,
        input_digest=input_digest,
        output_digest=output_digest,
        trace_id=trace_id,
        ts_utc=datetime.now(timezone.utc),
    )
    log_action_result(result)
    return (result, None)  # Raw output never returned (privacy by design)
