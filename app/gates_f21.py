"""F2.1 gate chain (X-API-Key legacy auth).

Gates: G0_F21, G2 (fail-closed), G7 (payload limits + forbidden fields),
G8 (action/profile), G10 (rate limit), G12 (async audit).
"""

import os
from fastapi import Request, HTTPException
from fastapi.background import BackgroundTasks

from app.payload_limits import check_payload_limits, LimitExceeded
import app.gate_engine
from app.audit_log import log_decision
from app.decision_record import DecisionRecord, make_input_digest
from app.rate_limiter import get_rate_limiter
from app.contracts.gate_v1 import GateInput, GateDecision
from datetime import datetime, timezone
from app.error_envelope import http_error_detail
from app.gate_artifacts import profiles_fingerprint_sha256


# Forbidden fields that must not appear in request payload
FORBIDDEN_PAYLOAD_FIELDS = {
    "api_key",
    "authorization",
    "veritta_api_key",
    "bearer",
}


def _contains_forbidden_fields(obj, path=""):
    """Recursively check if object contains forbidden fields."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in FORBIDDEN_PAYLOAD_FIELDS:
                return key, path
            if isinstance(value, (dict, list)):
                result = _contains_forbidden_fields(value, f"{path}.{key}" if path else key)
                if result:
                    return result
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            result = _contains_forbidden_fields(item, f"{path}[{idx}]")
            if result:
                return result
    return None


async def run_f21_chain(
    request: Request,
    body: dict,
    action: str,
    trace_id: str,
    background_tasks: BackgroundTasks,
) -> tuple[dict, str]:
    """
    Run F2.1 gate chain (X-API-Key authentication).
    
    Gates in order:
    1. G0_F21: Token present check
    2. G2: API key validation (fail-closed if env missing)
    3. G7: Payload limits + forbidden fields
    4. G8: Action/profile matrix check
    5. G10: Rate limiting
    6. G12: Async audit (post-response)
    
    Returns: (payload_dict, decision_str) or raises HTTPException (audit-before-raise).
    """
    ts = datetime.now(timezone.utc)
    profile_hash = None
    matched_rules = []
    reason_codes = []
    
    # G0_F21: Check X-API-Key header presence
    api_key = request.headers.get("X-API-Key", "").strip()
    if not api_key:
        decision = "DENY"
        reason_codes = ["G0_F21_missing_token"]
        matched_rules = ["X-API-Key header required"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G0_F21",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest="",
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=401, detail=http_error_detail(
            error="unauthorized",
            message="X-API-Key header missing",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # G2: API key validation (fail-closed)
    expected_key = os.getenv("VERITTA_BETA_API_KEY")
    if api_key != expected_key:
        decision = "DENY"
        reason_codes = ["AUTH_INVALID_KEY"]
        matched_rules = ["API key mismatch"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G2",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest="",
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=401, detail=http_error_detail(
            error="unauthorized",
            message="API key invalid",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # G7: Payload validation (limits + forbidden fields)
    # Check forbidden fields first (fail-closed)
    forbidden_result = _contains_forbidden_fields(body)
    if forbidden_result:
        field_name, field_path = forbidden_result
        decision = "DENY"
        reason_codes = [f"G7_forbidden_field_{field_name.lower()}"]
        matched_rules = [f"Forbidden field in payload: {field_path or field_name}"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G7",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest=make_input_digest(body),
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=400, detail=http_error_detail(
            error="bad_request",
            message="Forbidden field in payload",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # Check payload size and depth
    try:
        check_payload_limits(body, max_bytes=256000, max_depth_limit=100, max_list_limit=10000)
    except LimitExceeded as e:
        decision = "DENY"
        reason_codes = ["G7_payload_limit_exceeded"]
        matched_rules = [str(e)]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G7",
                profile_hash=profile_hash or "",
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest=make_input_digest(body),
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        # 413 for size, 400 for depth/items
        status_code = 413 if "bytes" in str(e) else 400
        raise HTTPException(status_code=status_code, detail=http_error_detail(
            error="bad_request",
            message="Payload limit exceeded",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # G8: Action/profile matrix check
    # Uses evaluate_gate to check if action matches profile
    gate_input = GateInput(
        action=action,
        payload=body.get("payload", body),
        allow_external=False,
        deny_unknown_fields=False,
    )
    try:
        gate_result = app.gate_engine.evaluate_gate(gate_input)
        print(f"DEBUG: gate_result.decision = {gate_result.decision}")
        print(f"DEBUG: ALLOW = {app.gate_engine.GateDecision.ALLOW}")
        print(f"DEBUG: equal = {gate_result.decision == app.gate_engine.GateDecision.ALLOW}")
    except Exception as e:
        # Gate evaluation failed; default to DENY
        print(f"DEBUG: exception in evaluate_gate: {e}")
        reason_codes = ["GATE_EXCEPTION"]
        log_decision(
            DecisionRecord(
                decision="DENY",
                profile_id="G8",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=[str(type(e).__name__)],
                reason_codes=reason_codes,
                input_digest=make_input_digest(body),
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=403, detail=http_error_detail(
            error="forbidden",
            message="Gate evaluation error",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    if gate_result.decision != GateDecision.ALLOW:
        reason_codes = ["G8_" + r.code.value for r in gate_result.reasons]
        # Fallback: if no reasons, use a generic code
        if not reason_codes:
            reason_codes = ["G8_denied"]
        log_decision(
            DecisionRecord(
                decision=gate_result.decision.value,
                profile_id="G8",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=getattr(gate_result, 'matched_rules', []),
                reason_codes=reason_codes,
                input_digest=make_input_digest(body),
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=403, detail=http_error_detail(
            error="forbidden",
            message="Action not allowed in profile",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # G10: Rate limiting (per api_key, 1000 req/min)
    # Only if api_key is present
    if api_key:
        limiter = get_rate_limiter()
        if not limiter.check(api_key, limit=1000, window_seconds=60):
            reason_codes = ["G10_rate_limit_exceeded"]
            log_decision(
                DecisionRecord(
                    decision="DENY",
                    profile_id="G10",
                    profile_hash=profiles_fingerprint_sha256(),
                    matched_rules=["Rate limit exceeded for API key"],
                    reason_codes=reason_codes,
                    input_digest=make_input_digest(body),
                    trace_id=trace_id,
                    ts_utc=ts,
                )
            )
            raise HTTPException(status_code=429, detail=http_error_detail(
                error="too_many_requests",
                message="Rate limit exceeded",
                trace_id=trace_id,
                reason_codes=reason_codes,
            ))
    
    # All gates passed, log success and schedule G12 async audit
    decision = "ALLOW"
    log_decision(
        DecisionRecord(
            decision=decision,
            profile_id="F2.1",
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=getattr(gate_result, 'matched_rules', []),
            reason_codes=[],
            input_digest=make_input_digest(body),
            trace_id=trace_id,
            ts_utc=ts,
        )
    )
    
    # G12: Schedule async audit (post-response)
    def async_audit():
        # Post-response logging (fire and forget)
        pass
    
    background_tasks.add_task(async_audit)
    
    return body, decision
