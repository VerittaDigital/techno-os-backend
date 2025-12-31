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
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from packaging import version as pkg_version

from app.action_audit_log import log_action_result
from app.action_contracts import ActionRequest, ActionResult
from app.action_registry import get_action_registry
from app.action_router import route_action as route_action_deterministic
from app.audit_log import AuditLogError
from app.digests import sha256_json_or_none
from app.executors.registry import get_executor
from app.executors.registry import UnknownExecutorError
from app.tracing import observed_span



# Semver pattern: X.Y.Z
SEMVER_PATTERN = re.compile(r'^\d+\.\d+\.\d+$')


def _get_executor_timeout() -> float:
    """Get executor timeout from env var VERITTA_EXECUTOR_TIMEOUT_S.
    
    Returns:
        Timeout in seconds (default: 10.0)
        If invalid value, returns default (fail-safe).
    """
    default_timeout = 10.0
    timeout_str = os.environ.get("VERITTA_EXECUTOR_TIMEOUT_S", str(default_timeout))
    
    try:
        timeout = float(timeout_str)
        if timeout <= 0:
            return default_timeout
        return timeout
    except (ValueError, TypeError):
        return default_timeout


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


def _compare_semver(version_a: str, version_b: str) -> int:
    """Compare two semantic versions using packaging.version.
    
    Args:
        version_a: version string (e.g., "1.0.0")
        version_b: version string to compare against (e.g., "1.1.0")
    
    Returns:
        -1 if version_a < version_b
         0 if version_a == version_b
         1 if version_a > version_b
    
    Raises:
        ValueError if either version is invalid
    """
    try:
        va = pkg_version.Version(version_a)
        vb = pkg_version.Version(version_b)
    except pkg_version.InvalidVersion as exc:
        raise ValueError(f"Invalid semantic version: {exc}")
    
    if va < vb:
        return -1
    elif va > vb:
        return 1
    else:
        return 0


def _compute_input_digest(payload: Dict[str, Any]) -> Optional[str]:
    """Compute SHA256 digest of payload. Return None if payload is not JSON-serializable.
    
    Uses canonical sha256_json_or_none() for consistency with Gate.
    """
    return sha256_json_or_none(payload)


def _compute_output_digest(output: Any) -> Optional[str]:
    """Compute SHA256 digest of output, or None if no output.
    
    Uses canonical sha256_json_or_none() for consistency with Gate.
    """
    if output is None:
        return None
    return sha256_json_or_none(output)


def _safe_log_action_result(result: ActionResult) -> ActionResult:
    """
    Log action result with fail-closed behavior.
    If logging fails, return BLOCKED result with AUDIT_LOG_FAILED reason.
    """
    try:
        log_action_result(result)
        return result
    except AuditLogError:
        # Audit log failed — convert to BLOCKED
        blocked_result = ActionResult(
            action=result.action,
            executor_id=result.executor_id,
            executor_version=result.executor_version,
            status="BLOCKED",
            reason_codes=["AUDIT_LOG_FAILED"],
            input_digest=result.input_digest,
            output_digest=result.output_digest,
            trace_id=result.trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        # Try to log the blocked result (if this also fails, we have a bigger problem)
        try:
            log_action_result(blocked_result)
        except AuditLogError:
            pass  # Last resort: logging is completely down
        return blocked_result


def run_agentic_action(
    action: str,
    payload: Dict[str, Any],
    trace_id: str,
    executor_id: str = "unknown",
    executor_version: str = "unknown",
) -> Tuple[ActionResult, Optional[Any]]:
    """
    Run action through governance pipeline (F8.6.1 observed).
    
    Returns:
        (ActionResult, output) where output is None on BLOCKED/FAILED
    """
    
    # F8.6.1: Create root span for entire pipeline execution (fail-closed, wrapper-only)
    with observed_span(
        "agentic_action",
        attributes={
            "action": action,
            "executor_id": executor_id,
            "trace_id": trace_id,
        }
    ):
        # Step 1: Route action to executor_id (if not explicitly provided)
        with observed_span("route_action"):
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
        
        # Step 2: Compute input digest for audit (returns None if not JSON-serializable)
        with observed_span("compute_digests"):
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
            result = _safe_log_action_result(result)
            return (result, None)
        
        # Step 3: Validate action metadata
        with observed_span("validate_action"):
            # Get action metadata from registry (ALWAYS, not skipped)
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
                result = _safe_log_action_result(result)
                return (result, None)
        
            # Step 3B: Validate action_version (always enforced when metadata exists)
            if action_meta is not None:
                action_version = action_meta.get("action_version")
                if action_version is None:
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
                    result = _safe_log_action_result(result)
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
                    result = _safe_log_action_result(result)
                    return (result, None)
        
        # Step 4: Resolve executor
        with observed_span("resolve_executor", attributes={"executor_id": executor_id}):
            # Resolve executor (needed for capability and limit checks below)
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
                result = _safe_log_action_result(result)
                return (result, None)
        
            # Step 4A: Validate executor version (AG-03)
            if action_meta:
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
                        result = _safe_log_action_result(result)
                        return (result, None)
                    else:
                        # Use semver comparison instead of string comparison
                        try:
                            if _compare_semver(executor_version, min_executor_version) < 0:
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
                                result = _safe_log_action_result(result)
                                return (result, None)
                        except ValueError:
                            # If version comparison fails, treat as incompatible
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
                            result = _safe_log_action_result(result)
                            return (result, None)

            # Step 4B: Validate executor capabilities (AG-03)
            # Check that executor has all required_capabilities
            if action_meta:
                required_capabilities = action_meta.get("required_capabilities", [])
                if required_capabilities:
                    # Get capabilities attribute
                    executor_capabilities = getattr(executor, "capabilities", None)
                    
                    # If executor has no capabilities attribute at all -> MISSING
                    # Check for None or non-list types (e.g. MagicMock)
                    if executor_capabilities is None or not isinstance(executor_capabilities, (list, tuple, set)):
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
                        result = _safe_log_action_result(result)
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
                        result = _safe_log_action_result(result)
                        return (result, None)

        # Step 5: Enforce payload limits
        with observed_span("enforce_limits"):
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
                result = _safe_log_action_result(result)
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
                result = _safe_log_action_result(result)
                return (result, None)

        # Step 6: Execute executor (with pre-audit for safety)
        with observed_span("execute_action", attributes={"executor_id": executor_id}):
            # PRE-AUDIT: Log execution attempt BEFORE executor runs
            # This guarantees auditability even if executor has side-effects or fails
            pre_audit_result = ActionResult(
                action=action,
                executor_id=executor_id,
                executor_version=executor_version,
                status="PENDING",  # Special: indicates execution was attempted
                reason_codes=["EXECUTION_ATTEMPT"],  # Marker for pre-audit
                input_digest=input_digest,
                output_digest=None,  # Not known yet
                trace_id=trace_id,
                ts_utc=datetime.now(timezone.utc),
            )
            pre_audit_result = _safe_log_action_result(pre_audit_result)
            
            # Get executor timeout
            timeout_seconds = _get_executor_timeout()
            
            # Create ThreadPoolExecutor explicitly (not with context manager)
            # to avoid blocking on thread cleanup after timeout
            pool = ThreadPoolExecutor(max_workers=1)
            
            try:
                # Create ActionRequest
                action_req = ActionRequest(
                    action=action,
                    payload=payload,
                    trace_id=trace_id,
                )
                
                # Execute with timeout
                future = pool.submit(executor.execute, action_req)
                output = future.result(timeout=timeout_seconds)
                
                # Success: clean shutdown (wait for thread to complete)
                pool.shutdown(wait=True)
                    
            except (FuturesTimeoutError, TimeoutError):
                # Executor exceeded timeout (fail-safe)
                # Catches both:
                # - FuturesTimeoutError: ThreadPoolExecutor timeout
                # - TimeoutError: Executor raises TimeoutError directly
                # Shutdown immediately without waiting (don't block on orphan thread)
                pool.shutdown(wait=False)
                
                status = "BLOCKED"
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
                result = _safe_log_action_result(result)
                return (result, None)
            except Exception as e:
                # Any other exception during execution
                # Shutdown pool without waiting
                pool.shutdown(wait=False)
                
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
                result = _safe_log_action_result(result)
                return (result, None)

        # Step 7: Success — Compute output digest and return
        with observed_span("audit_result"):
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
            result = _safe_log_action_result(result)
            return (result, None)  # Raw output never returned (privacy by design)
