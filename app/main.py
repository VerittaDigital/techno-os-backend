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
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response

from app.agentic_pipeline import run_agentic_action
from app.auth import detect_auth_mode
from app.action_audit_log import log_action_result
from app.action_matrix import get_action_matrix
from app.audit_log import log_decision
from app.tracing import init_tracing, observed_span
from app.audit_log import AuditLogError
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.contracts.gate_v1 import GateDecision, GateInput
from app.decision_record import DecisionRecord, make_input_digest
from app.digests import sha256_json_or_none
from app.error_handler import register_error_handlers
from app.error_envelope import http_error_detail
from app.gate_engine import evaluate_gate as evaluate_gate
from app.gate_canonical import detect_action, parse_body_by_method
from app.gate_errors import GateError
from app.middleware_trace import TraceCorrelationMiddleware
from app.gates_f21 import run_f21_chain
from app.gates_f23 import run_f23_chain
from app.api.admin import router as admin_router
from app.routes.preferences import router as preferences_router
from app.routes.notion import router as notion_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize tracing on app startup (F8.6.1 fail-closed)."""
    init_tracing(service_name="techno-os-backend")
    logging.info("✅ Startup complete (tracing initialized)")
    yield


from fastapi.middleware.cors import CORSMiddleware

# ... existing imports ...

app = FastAPI(title="Techno OS API", version="0.1.0", lifespan=lifespan)

# CORS for console origins (fail-closed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://techno-os-console.vercel.app"],  # Specify console origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Register admin API router
app.include_router(admin_router)

# Register preferences API router (F9.9-A)
app.include_router(preferences_router)

# Register notion read-only API router (Phase 4)
app.include_router(notion_router)

# Register middleware (T1: G6 trace correlation)
app.add_middleware(TraceCorrelationMiddleware)

# Register exception handlers (T1: G11 error normalization)
register_error_handlers(app)


@app.get("/health", tags=["health"])
def health():
    """Lightweight health check used by orchestration and tests."""
    return {"status": "ok"}


@app.get("/meta", tags=["meta"])
def meta():
    """Metadata endpoint for version and environment info."""
    return {"env": "production", "version": "v0.1.0", "service": "techno-os-api"}


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def gate_request(request: Request, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Dependency that validates via gate and emits gate_audit.
    
    T2: G0 Auth mode detection.
    T3: F2.1 chain execution.
    - Detect auth mode (F2.3 Bearer vs F2.1 X-API-Key)
    - Run F2.1 chain if X-API-Key
    - Block F2.3 temporarily (501) until T4
    - Store auth_mode in request.state for downstream
    """
    import hashlib
    import os
    from uuid import uuid4
    
    trace_id = str(uuid4())
    request.state.trace_id = trace_id
    
    # G0: Check if VERITTA_BETA_API_KEY is configured (mandatory)
    from app.gate_artifacts import profiles_fingerprint_sha256
    expected_key = os.getenv("VERITTA_BETA_API_KEY")
    if not expected_key or not expected_key.strip():
        decision_record = DecisionRecord(
            decision="DENY",
            profile_id="G0",
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=["Authentication must be configured"],
            reason_codes=["G0_auth_not_configured"],
            input_digest=None,
            trace_id=trace_id,
        )
        log_decision(decision_record)
        raise HTTPException(status_code=500, detail=http_error_detail(
            error="internal_error",
            message="Authentication not configured",
            trace_id=trace_id,
            reason_codes=["G0_auth_not_configured"],
        ))
    
    # T2: G0 Feature flag routing — detect auth mode
    auth_mode = detect_auth_mode(request)
    
    # If no auth header present at all, fail with 401 missing_authorization
    if auth_mode is None:
        decision_record = DecisionRecord(
            decision="DENY",
            profile_id="G0",
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=["Authorization header required"],
            reason_codes=["AUTH_MISSING_KEY"],
            input_digest=None,  # Body not read yet
            trace_id=trace_id,
        )
        log_decision(decision_record)  # Persist audit (fail-closed)
        raise HTTPException(status_code=401, detail=http_error_detail(
            error="unauthorized",
            message="missing_authorization",
            trace_id=trace_id,
            reason_codes=["AUTH_MISSING_KEY"],
        ))
    
    # Store auth_mode in request state (for audit/logging downstream)
    request.state.auth_mode = auth_mode
    
    # FASE 11: Parse body de forma determinística (GET/DELETE = {})
    try:
        body = await parse_body_by_method(request)
    except GateError as e:
        # G10_BODY_PARSE_ERROR: log decisão antes de raise
        decision_record = DecisionRecord(
            decision="DENY",
            profile_id="G10",
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=["Body parsing failed"],
            reason_codes=[e.reason_code.value],
            input_digest=None,
            trace_id=trace_id,
        )
        log_decision(decision_record)
        raise  # Re-raise GateError (já tem detail formatado)
    
    # FASE 11: Detectar action de forma canônica (com normalização de path ou body)
    try:
        path_action = detect_action(request)
        action = body.get("action", path_action) if isinstance(body, dict) else path_action
    except GateError as e:
        # G8_UNKNOWN_ACTION: log decisão antes de raise
        decision_record = DecisionRecord(
            decision="DENY",
            profile_id="G8",
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=["No action mapping for path"],
            reason_codes=[e.reason_code.value],
            input_digest=None,
            trace_id=trace_id,
        )
        log_decision(decision_record)
        raise  # Re-raise GateError (já tem detail formatado)
    
    # FASE 11: Validar que action está no action_matrix
    action_matrix = get_action_matrix()
    if action not in action_matrix.allowed_actions:
        from app.gate_errors import ReasonCode
        decision_record = DecisionRecord(
            decision="DENY",
            profile_id="G8",
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=[f"Action '{action}' not in action matrix"],
            reason_codes=[ReasonCode.G8_UNKNOWN_ACTION.value],
            input_digest=None,
            trace_id=trace_id,
        )
        log_decision(decision_record)
        raise GateError(
            reason_code=ReasonCode.G8_UNKNOWN_ACTION,
            message=f"Action '{action}' not in action matrix",
            http_status=403
        )
    
    # FASE 11: Validar que profile existe
    from app.gate_profiles import get_profile
    from app.gate_errors import ReasonCode
    profile = get_profile(action)
    if profile is None:
        decision_record = DecisionRecord(
            decision="DENY",
            profile_id="G9",
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=[f"No profile defined for action '{action}'"],
            reason_codes=[ReasonCode.G9_MISSING_PROFILE.value],
            input_digest=None,
            trace_id=trace_id,
        )
        log_decision(decision_record)
        raise GateError(
            reason_code=ReasonCode.G9_MISSING_PROFILE,
            message=f"No profile defined for action '{action}'",
            http_status=500  # Internal error, not user fault
        )
    
    # Body already parsed above
    
    # Compute input digest using canonical rule (None for non-JSON, privacy-first)
    input_digest = sha256_json_or_none(body)
    
    # T3: F2.1 chain execution for X-API-Key
    if auth_mode == "F2.1":
        # This will raise HTTPException (with audit-before-raise) if any gate fails
        payload, decision = await run_f21_chain(
            request=request,
            body=body,
            action=action,
            trace_id=trace_id,
            background_tasks=background_tasks,
        )
        return {"payload": payload, "action": action, "trace_id": trace_id}
    
    # T4: F2.3 chain execution for Bearer token auth with sessions
    elif auth_mode == "F2.3":
        response, decision = await run_f23_chain(
            request=request,
            body=body,
            action=action,
            trace_id=trace_id,
            background_tasks=background_tasks,
        )
        # Store response in request.state for endpoint to use
        request.state.f23_response = response
        return {"payload": body, "action": action, "trace_id": trace_id}


@app.post("/process", tags=["processing"])
async def process(
    request: Request,
    gate_data: Dict[str, Any] = Depends(gate_request),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Process action with gate + pipeline (F8.6.1 observed)."""
    # Check if F2.3 response already prepared (with echo-back headers)
    if hasattr(request.state, "f23_response") and request.state.f23_response:
        return request.state.f23_response
    
    payload = gate_data.get("payload", {})
    action = gate_data.get("action", "process")
    trace_id = gate_data.get("trace_id", str(uuid.uuid4()))
    
    # Extract inner payload for F2.1 (body has action and payload keys)
    if isinstance(payload, dict) and "payload" in payload:
        inner_payload = payload.get("payload", {})
    else:
        inner_payload = payload
    
    # F8.6.1: Create root span for request (fail-closed, wrapper-only)
    with observed_span(
        "process_action",
        attributes={
            "trace_id": trace_id,
            "action": action,
            "context_id": gate_data.get("context_id", "unknown"),
        }
    ):

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
            payload=inner_payload,
            trace_id=trace_id,
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
