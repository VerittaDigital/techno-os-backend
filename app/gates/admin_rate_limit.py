"""Admin rate limit gate (100 req/min per admin key)."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List

from app.decision_record import DecisionRecord
from app.audit_log import log_decision
from app.gate_artifacts import profiles_fingerprint_sha256


class AdminRateLimit:
    """
    Rate limit for admin API (100 req/min per admin key).
    
    Separate from user rate limits (G10).
    
    In-memory implementation for simplicity (suitable for single-instance deployment).
    For multi-instance, use Redis.
    """
    
    PROFILE_ID = "ADMIN_G10"
    
    # In-memory store: {admin_key: [(timestamp, count), ...]}
    _requests: Dict[str, List[datetime]] = {}
    
    @classmethod
    def check(cls, admin_key: str, trace_id: str) -> tuple[bool, Optional[str], Optional[DecisionRecord]]:
        """
        Check if admin key has exceeded rate limit.
        
        Returns:
            (allowed: bool, reason_code: Optional[str], decision_record: DecisionRecord)
        """
        limit_per_min = int(os.getenv("VERITTA_ADMIN_RATE_LIMIT_PER_MIN", "100"))
        
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        minute_ago = now - timedelta(minutes=1)
        
        # Initialize tracking for this key if needed
        if admin_key not in cls._requests:
            cls._requests[admin_key] = []
        
        # Remove old requests (older than 1 minute)
        cls._requests[admin_key] = [
            ts for ts in cls._requests[admin_key]
            if ts > minute_ago
        ]
        
        # Check limit
        request_count = len(cls._requests[admin_key])
        
        if request_count >= limit_per_min:
            decision_record = DecisionRecord(
                decision="DENY",
                profile_id=cls.PROFILE_ID,
                profile_hash=profiles_fingerprint_sha256(),
                matched_rules=[f"Admin rate limit exceeded ({limit_per_min}/min)"],
                reason_codes=["RATE_LIMIT_EXCEEDED"],
                input_digest=None,
                trace_id=trace_id,
            )
            log_decision(decision_record)
            return (False, "RATE_LIMIT_EXCEEDED", decision_record)
        
        # Record this request
        cls._requests[admin_key].append(now)
        
        decision_record = DecisionRecord(
            decision="ALLOW",
            profile_id=cls.PROFILE_ID,
            profile_hash=profiles_fingerprint_sha256(),
            matched_rules=[f"Admin rate limit OK ({request_count + 1}/{limit_per_min})"],
            reason_codes=[],
            input_digest=None,
            trace_id=trace_id,
        )
        log_decision(decision_record)
        return (True, None, decision_record)
