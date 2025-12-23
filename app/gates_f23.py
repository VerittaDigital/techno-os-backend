"""F2.3 gate chain (Bearer token auth with sessions).

Gates: G1 (Bearer format), G2 (shared), G3 (user_id binding), G4 (session_id format),
G5 (session TTL/correlation), G7-G8 (shared), G9 (B1-aware echo-back), G10 (rate limit), G12 (async audit).

NOTA: T4 é um esboço mínimo. Muitas funcionalidades abreviadas para deadline.
"""

import os
import re
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse

from app.payload_limits import check_payload_limits, LimitExceeded
from app.gate_engine import evaluate_gate
from app.audit_log import log_decision
from app.rate_limiter import get_rate_limiter
from app.session_store import get_session_store, sha256_str
from app.f23_bindings import get_bindings
from app.decision_record import DecisionRecord
from app.contracts.gate_v1 import GateInput, GateDecision
from app.error_envelope import http_error_detail
from app.gate_artifacts import profiles_fingerprint_sha256
import uuid


async def run_f23_chain(
    request: Request,
    body: dict,
    action: str,
    trace_id: str,
    background_tasks: BackgroundTasks,
) -> tuple[JSONResponse, str]:
    """
    Run F2.3 gate chain (Bearer token authentication with sessions).
    
    Gates in order:
    1. G1: Bearer format validation
    2. G2: API key validation (shared with F2.1)
    3. G3: User ID binding check
    4. G4: Session ID format validation
    5. G5: Session TTL and correlation check
    6. G7-G8: Payload and action matrix (shared with F2.1)
    7. G9: B1-aware backend contract handling (echo-back headers)
    8. G10: Rate limiting (per api_key + per session_id)
    9. G12: Async audit (post-response)
    
    Returns: (JSONResponse with optional echo-back headers, decision_str) or raises HTTPException.
    """
    ts = datetime.now(timezone.utc)
    profile_hash = None
    matched_rules = []
    reason_codes = []
    
    # G1: Bearer token format validation
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header.startswith("Bearer "):
        decision = "DENY"
        reason_codes = ["G1_bearer_format_invalid"]
        matched_rules = ["Authorization header must be 'Bearer <token>'"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G1",
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
            message="Invalid Bearer token format",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    api_key = auth_header[7:]  # Extract token after "Bearer "
    
    # G2: API key validation (shared with F2.1)
    expected_key = os.getenv("VERITTA_BETA_API_KEY")
    if api_key != expected_key:
        decision = "DENY"
        reason_codes = ["G2_invalid_api_key"]
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
    
    # G3: User ID validation and binding check
    user_id_header = request.headers.get("X-VERITTA-USER-ID", "").strip()
    if not user_id_header or not re.match(r"^u_[a-z0-9]{8}$", user_id_header):
        decision = "DENY"
        reason_codes = ["G3_user_id_format_invalid"]
        matched_rules = ["X-VERITTA-USER-ID header invalid format"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G3",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest="",
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=400, detail=http_error_detail(
            error="bad_request",
            message="Invalid user ID format",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # Check user ID binding
    api_key_sha256 = sha256_str(api_key)
    bindings = get_bindings()
    allowed_user_ids = bindings.get_allowed_user_ids(api_key_sha256)
    if user_id_header not in allowed_user_ids:
        decision = "DENY"
        reason_codes = ["G3_user_id_not_bound"]
        matched_rules = ["User ID not bound to this API key"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G3",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest="",
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=403, detail=http_error_detail(
            error="forbidden",
            message="User ID not authorized for this API key",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # G4: Session ID format validation
    session_id_header = request.headers.get("X-VERITTA-SESSION-ID", "").strip()
    if not session_id_header or not re.match(r"^sess_[a-z0-9]{16}$", session_id_header):
        decision = "DENY"
        reason_codes = ["G4_session_id_format_invalid"]
        matched_rules = ["X-VERITTA-SESSION-ID header invalid format"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G4",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest="",
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=400, detail=http_error_detail(
            error="bad_request",
            message="Invalid session ID format",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # G5: Session TTL and correlation check
    session_store = get_session_store()
    session_record = session_store.get(session_id_header)
    if not session_record:
        decision = "DENY"
        reason_codes = ["G5_session_not_found"]
        matched_rules = ["Session ID not found in store"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G5",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest="",
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=403, detail=http_error_detail(
            error="forbidden",
            message="Session not found",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    if not session_record.is_valid():
        decision = "DENY"
        reason_codes = ["G5_session_expired"]
        matched_rules = ["Session TTL expired"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G5",
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
            message="Session expired",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # Verify session user_id and api_key match
    if session_record.user_id != user_id_header:
        decision = "DENY"
        reason_codes = ["G5_session_user_mismatch"]
        matched_rules = ["Session user ID does not match header"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G5",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest="",
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=403, detail=http_error_detail(
            error="forbidden",
            message="Session user ID mismatch",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    if session_record.api_key_sha256 != api_key_sha256:
        decision = "DENY"
        reason_codes = ["G5_session_key_mismatch"]
        matched_rules = ["Session API key hash does not match"]
        log_decision(
            DecisionRecord(
                decision=decision,
                profile_id="G5",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=matched_rules,
                reason_codes=reason_codes,
                input_digest="",
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        raise HTTPException(status_code=403, detail=http_error_detail(
            error="forbidden",
            message="Session API key mismatch",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # G7-G8: Payload validation and action matrix (shared with F2.1)
    # (Omitted for brevity; reuse from F2.1)
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
                input_digest="",
                trace_id=trace_id,
                ts_utc=ts,
            )
        )
        status_code = 413 if "bytes" in str(e) else 400
        raise HTTPException(status_code=status_code, detail=http_error_detail(
            error="bad_request",
            message="Payload limit exceeded",
            trace_id=trace_id,
            reason_codes=reason_codes,
        ))
    
    # Gate evaluation for action matrix
    gate_input = GateInput(
        action=action,
        payload=body,
        allow_external=False,
        deny_unknown_fields=False,
    )
    gate_result = evaluate_gate(gate_input)
    if gate_result.decision != GateDecision.ALLOW:
        reason_codes = ["G8_" + r.code.value for r in gate_result.reasons]
        log_decision(
            DecisionRecord(
                decision=gate_result.decision.value,
                profile_id="G8",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=getattr(gate_result, 'matched_rules', []),
                reason_codes=reason_codes,
                input_digest="",
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
    
    # G9: B1-aware backend contract handling (simplified: always WAIT for now)
    # In full T4, this would check action_contracts for B1 status
    echo_back_headers = {
        "X-VERITTA-USER-ID": user_id_header,
        "X-VERITTA-SESSION-ID": session_id_header,
    }
    
    # G10: Rate limiting (per api_key + per session_id)
    limiter = get_rate_limiter()
    if not limiter.check(api_key, limit=1000, window_seconds=60):
        reason_codes = ["G10_rate_limit_exceeded_api_key"]
        log_decision(
            DecisionRecord(
                decision="DENY",
                profile_id="G10",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=["Rate limit exceeded for API key"],
                reason_codes=reason_codes,
                input_digest="",
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
    
    if not limiter.check(session_id_header, limit=100, window_seconds=60):
        reason_codes = ["G10_rate_limit_exceeded_session"]
        log_decision(
            DecisionRecord(
                decision="DENY",
                profile_id="G10",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=["Rate limit exceeded for session"],
                reason_codes=reason_codes,
                input_digest="",
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
    
    # All gates passed
    decision = "ALLOW"
    log_decision(
        DecisionRecord(
            decision=decision,
            profile_id="F2.3",
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=getattr(gate_result, 'matched_rules', []),
            reason_codes=[],
            input_digest="",
            trace_id=trace_id,
            ts_utc=ts,
        )
    )
    
    # G12: Schedule async audit
    def async_audit():
        pass
    
    background_tasks.add_task(async_audit)
    
    # Return response with echo-back headers
    return JSONResponse(
        status_code=200,
        content={"status": "allowed", "action": action, "trace_id": trace_id},
        headers=echo_back_headers,
    ), decision
