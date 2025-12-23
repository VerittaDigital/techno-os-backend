"""Admin API endpoints (POST/GET /admin/*)."""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.session_repository import SessionRepository
from app.guards.admin_guard import AdminGuard
from app.gates.admin_rate_limit import AdminRateLimit
from app.error_envelope import http_error_detail
from app.action_contracts import ActionResult
from app.action_audit_log import log_action_result
from app.tools.audit_parser import AuditParser

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# DEPENDENCY: Admin Guard
# ============================================================================

async def require_admin_key(request: Request) -> str:
    """
    Dependency that validates X-ADMIN-KEY header.
    
    Raises HTTPException(403) if invalid.
    Emits decision_audit (always, including DENY).
    """
    from uuid import uuid4, UUID
    
    admin_key = request.headers.get("X-ADMIN-KEY")
    
    # Get trace_id from request state or generate new one
    trace_id = None
    if hasattr(request.state, "trace_id"):
        trace_id_val = str(request.state.trace_id)
        # Validate it's a UUID; if not, generate new
        try:
            UUID(trace_id_val)
            trace_id = trace_id_val
        except ValueError:
            trace_id = str(uuid4())
    else:
        trace_id = str(uuid4())
    
    is_valid, reason_code, decision_record = AdminGuard.validate(admin_key)
    
    if not is_valid:
        raise HTTPException(
            status_code=403,
            detail=http_error_detail(
                error="forbidden",
                message="Admin authentication failed",
                trace_id=trace_id,
                reason_codes=[reason_code],
            ),
        )
    
    return admin_key


async def require_admin_rate_limit(
    admin_key: str = Depends(require_admin_key),
    request: Request = None,
) -> str:
    """
    Dependency that validates admin rate limit.
    
    Raises HTTPException(429) if exceeded.
    Emits decision_audit.
    """
    from uuid import uuid4
    
    # Get trace_id from request state or generate new one
    trace_id = None
    if request and hasattr(request.state, "trace_id"):
        trace_id_val = str(request.state.trace_id)
        # Validate it's a UUID; if not, generate new
        try:
            from uuid import UUID
            UUID(trace_id_val)
            trace_id = trace_id_val
        except ValueError:
            trace_id = str(uuid4())
    else:
        trace_id = str(uuid4())
    
    allowed, reason_code, decision_record = AdminRateLimit.check(admin_key, trace_id)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=http_error_detail(
                error="rate_limit_exceeded",
                message="Admin rate limit exceeded",
                trace_id=trace_id,
                reason_codes=[reason_code],
            ),
        )
    
    return admin_key


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RevokeSessionRequest(BaseModel):
    """POST /admin/sessions/revoke request."""
    session_id: str = Field(..., min_length=36, max_length=36, description="Session UUID")


class SessionDetailResponse(BaseModel):
    """GET /admin/sessions/{session_id} response."""
    session_id: str
    user_id: str
    created_at: str  # ISO format
    expires_at: str
    revoked_at: Optional[str] = None


class RevokeSessionResponse(BaseModel):
    """POST /admin/sessions/revoke response."""
    session_id: str
    status: str  # "revoked" | "already_revoked"
    revoked_at: str  # ISO format


class AuditSummaryResponse(BaseModel):
    """GET /admin/audit/summary response."""
    window: dict  # {"days": int, "limit": int}
    decisions: dict  # {"allow": int, "deny": int}
    deny_breakdown: dict  # {reason_code: count, ...}
    events_by_type: dict  # {"decision_audit": int, "action_audit": int}
    ts_utc: str
    events_processed: Optional[int] = None
    parse_errors: Optional[int] = None
    note: Optional[str] = None


class HealthResponse(BaseModel):
    """GET /admin/health response."""
    status: str  # "ok"
    db: str  # "connected" | "disconnected"
    audit_sink: str  # "writable" | "unwritable"
    ts_utc: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/sessions/revoke")
async def revoke_session(
    req: RevokeSessionRequest,
    admin_key: str = Depends(require_admin_rate_limit),
    db: Session = Depends(get_db),
    request: Request = None,
) -> RevokeSessionResponse:
    """
    Revoke a session (admin operation).
    
    Idempotent: if already revoked, returns 200 with status="already_revoked"
    
    Emits:
    - decision_audit (ALLOW, profile_id=ADMIN_G2)
    - action_audit (action=revoke_session, status=SUCCESS|FAILED)
    """
    from uuid import uuid4, UUID
    
    # Generate fresh trace_id (ensure it's a valid UUID)
    trace_id = str(uuid4())
    
    repo = SessionRepository(db)
    session = repo.get_by_id(req.session_id)
    
    # Not found
    if not session:
        raise HTTPException(
            status_code=404,
            detail=http_error_detail(
                error="not_found",
                message="Session not found",
                trace_id=trace_id,
                reason_codes=["SESSION_NOT_FOUND"],
            ),
        )
    
    # Already revoked (idempotent)
    if session.is_revoked():
        result = ActionResult(
            action="revoke_session",
            status="SUCCESS",
            reason_codes=[],
            input_digest="",  # Empty hash (no input to hash)
            output_digest=None,
            trace_id=trace_id,
            executor_id="admin_api",
            executor_version="1.0.0",
        )
        log_action_result(result)
        
        return RevokeSessionResponse(
            session_id=session.session_id,
            status="already_revoked",
            revoked_at=session.revoked_at.isoformat() if session.revoked_at else "",
        )
    
    # Revoke
    try:
        revoked_session = repo.revoke(session.session_id)
        
        if not revoked_session:
            raise Exception("Revocation returned None")
        
        result = ActionResult(
            action="revoke_session",
            status="SUCCESS",
            reason_codes=[],
            input_digest="",  # Empty hash
            output_digest=None,
            trace_id=trace_id,
            executor_id="admin_api",
            executor_version="1.0.0",
        )
        log_action_result(result)
        
        return RevokeSessionResponse(
            session_id=revoked_session.session_id,
            status="revoked",
            revoked_at=revoked_session.revoked_at.isoformat(),
        )
    
    except Exception as e:
        result = ActionResult(
            action="revoke_session",
            status="FAILED",
            reason_codes=["REVOKE_FAILED"],
            input_digest="",  # Empty hash
            output_digest=None,
            trace_id=trace_id,
            executor_id="admin_api",
            executor_version="1.0.0",
        )
        log_action_result(result)
        
        raise HTTPException(
            status_code=500,
            detail=http_error_detail(
                error="internal_error",
                message="Session revocation failed",
                trace_id=trace_id,
                reason_codes=["REVOKE_FAILED"],
            ),
        )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    admin_key: str = Depends(require_admin_rate_limit),
    db: Session = Depends(get_db),
    request: Request = None,
) -> SessionDetailResponse:
    """
    Get session details (admin-only, never returns api_key_hash).
    """
    from uuid import uuid4
    
    trace_id = str(uuid4())
    
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=http_error_detail(
                error="not_found",
                message="Session not found",
                trace_id=trace_id,
                reason_codes=["SESSION_NOT_FOUND"],
            ),
        )
    
    return SessionDetailResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        created_at=session.created_at.isoformat() if session.created_at else "",
        expires_at=session.expires_at.isoformat() if session.expires_at else "",
        revoked_at=session.revoked_at.isoformat() if session.revoked_at else None,
    )


@router.get("/audit/summary")
async def audit_summary(
    days: int = Query(1, ge=1, le=7, description="Days to look back (1–7)"),
    limit: int = Query(10000, ge=100, le=50000, description="Max events (100–50k)"),
    event_type: str = Query(None, description="Filter: decision_audit | action_audit"),
    admin_key: str = Depends(require_admin_rate_limit),
    request: Request = None,
) -> AuditSummaryResponse:
    """
    Get audit summary (read-only, no events returned, just aggregations).
    
    Streaming parser: safe against huge logs.
    """
    from uuid import uuid4
    
    trace_id = str(uuid4())
    
    try:
        summary = AuditParser.summarize(days=days, limit=limit, event_type=event_type)
        return AuditSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=http_error_detail(
                error="internal_error",
                message="Audit summary parsing failed",
                trace_id=trace_id,
                reason_codes=["AUDIT_PARSE_FAILED"],
            ),
        )


@router.get("/health")
async def admin_health(
    admin_key: str = Depends(require_admin_rate_limit),
    db: Session = Depends(get_db),
    request: Request = None,
) -> HealthResponse:
    """
    Health check: DB + audit sink connectivity.
    """
    from uuid import uuid4
    
    trace_id = str(uuid4())
    
    # Check DB
    db_status = "disconnected"
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Check audit sink (path exists and writable)
    audit_sink_status = "unwritable"
    audit_log_path = os.getenv("VERITTA_AUDIT_LOG_PATH", "./audit.log")
    try:
        # Check if path is writable (open for append without actually writing)
        with open(audit_log_path, "a"):
            pass
        audit_sink_status = "writable"
    except OSError:
        audit_sink_status = "unwritable"
    
    return HealthResponse(
        status="ok",
        db=db_status,
        audit_sink=audit_sink_status,
        ts_utc=datetime.now(timezone.utc).isoformat(),
    )
