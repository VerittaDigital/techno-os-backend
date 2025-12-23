"""Techno OS FastAPI application with V-COF governance.

Wires:
- Gate (evaluate_gate) for action validation
- Agentic pipeline (run_agentic_action) for execution
- Audit logging (gate_audit, action_audit)

Endpoint POST /process:
- Accepts ProcessRequest ({"text": ...})
- Validates via gate
- Executes via pipeline if gate allows
- Returns ActionResult JSON (status, trace_id, action, etc.)
"""

import json
import logging
import uuid
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Request

from app.agentic_pipeline import run_agentic_action
from app.auth import require_beta_api_key
from app.action_audit_log import log_action_result
from app.action_matrix import get_action_matrix
from app.audit_log import log_decision
from app.audit_log import AuditLogError
from app.contracts.gate_v1 import GateDecision, GateInput
from app.decision_record import DecisionRecord, make_input_digest
from app.digests import sha256_json_or_none
from app.error_handler import register_error_handlers
from app.gate_engine import evaluate_gate as evaluate_gate
from app.middleware_trace import TraceCorrelationMiddleware
from app.schemas import ProcessRequest, ProcessResponse

app = FastAPI(title="Techno OS API", version="0.1.0")

# Register middleware (T1: G6 trace correlation)
app.add_middleware(TraceCorrelationMiddleware)

# Register exception handlers (T1: G11 error normalization)
register_error_handlers(app)


@app.get("/health", tags=["health"])
def health():
    """Lightweight health check used by orchestration and tests."""
    return {"status": "ok"}


async def gate_request(request: Request) -> Dict[str, Any]:
    """Dependency that validates via gate and emits gate_audit."""
    import hashlib
    import os
    
    trace_id = str(uuid.uuid4())

    # Step 1: Auth check (before reading body)
    expected_key = os.environ.get("VERITTA_BETA_API_KEY")
    if expected_key:  # Auth is required only if env var is set
        x_api_key = request.headers.get("X-API-Key")
        
        if x_api_key is None:
            # Missing key: log DENY with AUTH_MISSING_KEY
            from app.gate_artifacts import profiles_fingerprint_sha256
            decision_record = DecisionRecord(
                decision="DENY",
                profile_id="default",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=[],
                reason_codes=["AUTH_MISSING_KEY"],
                input_digest=None,  # Body not read yet
                trace_id=trace_id,
            )
            log_decision(decision_record)  # Persist audit (fail-closed)
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        if x_api_key != expected_key:
            # Invalid key: log DENY with AUTH_INVALID_KEY
            from app.gate_artifacts import profiles_fingerprint_sha256
            decision_record = DecisionRecord(
                decision="DENY",
                profile_id="default",
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=[],
                reason_codes=["AUTH_INVALID_KEY"],
                input_digest=None,  # Body not read yet
                trace_id=trace_id,
            )
            log_decision(decision_record)  # Persist audit (fail-closed)
            raise HTTPException(status_code=401, detail="Unauthorized")

    # Step 2: Read body (only after auth passes)
    try:
        body = await request.json()
    except (json.JSONDecodeError, ValueError):
        body = {}

    action = "process"
    
    # Compute input digest using canonical rule (None for non-JSON, privacy-first)
    input_digest = sha256_json_or_none(body)

    # Build gate input and evaluate
    try:
        gate_input = GateInput(
            action=action,
            payload=body,
            allow_external=False,
            deny_unknown_fields=False,
        )
        gate_result = evaluate_gate(gate_input)
        gate_decision = gate_result.decision.value
        gate_exception = None
    except Exception as exc:
        # Gate exception: treat as denial with GATE_EXCEPTION reason
        gate_decision = "DENY"
        gate_exception = str(exc)
        gate_result = None

    # Log decision
    reason_codes = []
    if gate_decision == "DENY":
        if gate_exception:
            # If gate raised exception, use GATE_EXCEPTION
            reason_codes = ["GATE_EXCEPTION"]
        elif gate_result and gate_result.reasons:
            reason_codes = [r.code.value for r in gate_result.reasons]
        if not reason_codes:
            reason_codes = ["UNKNOWN_DENIAL"]
    
    # P1.5: Extract profile_hash and matched_rules from gate_result
    # Fail-closed: if gate_result is None (exception), use placeholder profile_hash
    if gate_result:
        profile_hash = gate_result.profile_hash
        matched_rules = gate_result.matched_rules
    else:
        # Gate exception case: compute default profile_hash
        from app.gate_artifacts import profiles_fingerprint_sha256
        profile_hash = profiles_fingerprint_sha256()
        matched_rules = ["GATE_EXCEPTION"]
    
    decision_record = DecisionRecord(
        decision=gate_decision,
        profile_id="default",
        profile_hash=profile_hash,  # ← P1.5: Now from gate_result (never empty)
        matched_rules=matched_rules,  # ← P1.5: Now from gate_result
        reason_codes=reason_codes,
        input_digest=input_digest,
        trace_id=trace_id,
    )
    log_decision(decision_record)

    # Emit gate_audit
    gate_audit_log = logging.getLogger("gate_audit")
    gate_audit_log.info(
        json.dumps({
            "decision": gate_decision,
            "action": action,
            "trace_id": trace_id,
        })
    )

    # If denied, raise 403
    if gate_decision == "DENY":
        raise HTTPException(status_code=403, detail="Gate denied request")

    return {"payload": body, "action": action, "trace_id": trace_id}


@app.post("/process", tags=["processing"])
async def process(
    gate_data: Dict[str, Any] = Depends(gate_request),
):
    """Process action with gate + pipeline."""
    payload = gate_data.get("payload", {})
    action = gate_data.get("action", "process")
    trace_id = gate_data.get("trace_id", str(uuid.uuid4()))

    # Check if action is allowed in action matrix (PROFILE_ACTION_MISMATCH)
    matrix = get_action_matrix()
    if action not in matrix.allowed_actions:
        # Persist PROFILE_ACTION_MISMATCH ActionResult BLOCKED before returning 403
        from datetime import datetime, timezone
        from app.action_contracts import ActionResult
        
        mismatch_result = ActionResult(
            action=action,
            executor_id="unknown",
            executor_version="unknown",
            status="BLOCKED",
            reason_codes=["PROFILE_ACTION_MISMATCH"],
            input_digest="",
            output_digest=None,
            trace_id=trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        try:
            log_action_result(mismatch_result)
        except AuditLogError:
            # Audit logging failed — emit BLOCKED with AUDIT_LOG_FAILED marker (best effort)
            fallback_result = ActionResult(
                action=action,
                executor_id="unknown",
                executor_version="unknown",
                status="BLOCKED",
                reason_codes=["PROFILE_ACTION_MISMATCH", "AUDIT_LOG_FAILED"],
                input_digest="",
                output_digest=None,
                trace_id=trace_id,
                ts_utc=datetime.now(timezone.utc),
            )
            try:
                log_action_result(fallback_result)
            except AuditLogError:
                pass  # Last resort: logging is completely down
        
        raise HTTPException(status_code=403, detail="Action not allowed in profile")

    # Run pipeline
    result, output = run_agentic_action(
        action=action,
        payload=payload,
        trace_id=trace_id,
        executor_id="text_process_v1",
    )

    # Return ActionResult JSON
    return {
        "status": result.status,
        "action": result.action,
        "executor_id": result.executor_id,
        "executor_version": result.executor_version,
        "reason_codes": result.reason_codes,
        "input_digest": result.input_digest,
        "output_digest": result.output_digest,
        "trace_id": result.trace_id,
        "ts_utc": result.ts_utc.isoformat() if result.ts_utc else None,
    }
