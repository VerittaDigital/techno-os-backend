"""Admin authentication guard (X-ADMIN-KEY validation with audit trail)."""

import os
from typing import Optional
from uuid import uuid4

from app.decision_record import DecisionRecord
from app.audit_log import log_decision
from app.gate_artifacts import profiles_fingerprint_sha256


class AdminGuard:
    """
    Validate X-ADMIN-KEY header for admin endpoints.
    
    Fail-closed: Missing or invalid key → 403 + decision_audit
    
    Always emits decision_audit (including DENY) for auditability.
    """
    
    PROFILE_ID = "ADMIN_G2"
    
    @staticmethod
    def validate(admin_key_header: Optional[str]) -> tuple[bool, Optional[str], Optional[DecisionRecord]]:
        """
        Validate admin key and return decision record.
        
        Args:
            admin_key_header: Value of X-ADMIN-KEY header
        
        Returns:
            (is_valid: bool, reason_code: Optional[str], decision_record: DecisionRecord)
        """
        trace_id = str(uuid4())
        expected_key = os.getenv("VERITTA_ADMIN_API_KEY")
        
        # Check if VERITTA_ADMIN_API_KEY is configured
        if not expected_key or not expected_key.strip():
            decision_record = DecisionRecord(
                decision="DENY",
                profile_id=AdminGuard.PROFILE_ID,
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=["Admin authentication not configured"],
                reason_codes=["ADMIN_KEY_MISSING"],
                input_digest=None,
                trace_id=trace_id,
            )
            log_decision(decision_record)
            return (False, "ADMIN_KEY_MISSING", decision_record)
        
        # Check if header is present
        if not admin_key_header:
            decision_record = DecisionRecord(
                decision="DENY",
                profile_id=AdminGuard.PROFILE_ID,
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=["X-ADMIN-KEY header missing"],
                reason_codes=["ADMIN_KEY_MISSING"],
                input_digest=None,
                trace_id=trace_id,
            )
            log_decision(decision_record)
            return (False, "ADMIN_KEY_MISSING", decision_record)
        
        # Validate key value
        if admin_key_header != expected_key:
            decision_record = DecisionRecord(
                decision="DENY",
                profile_id=AdminGuard.PROFILE_ID,
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=["Admin key value mismatch"],
                reason_codes=["ADMIN_KEY_INVALID"],
                input_digest=None,
                trace_id=trace_id,
            )
            log_decision(decision_record)
            return (False, "ADMIN_KEY_INVALID", decision_record)
        
        # Valid admin key
        decision_record = DecisionRecord(
            decision="ALLOW",
            profile_id=AdminGuard.PROFILE_ID,
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=["Admin key valid"],
            reason_codes=[],
            input_digest=None,
            trace_id=trace_id,
        )
        log_decision(decision_record)
        return (True, None, decision_record)
