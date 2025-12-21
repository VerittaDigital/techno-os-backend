"""Canonical decision record for gate audit trail.

Immutable, deterministic record of every gate evaluation decision.
All fields are non-sensitive; payload digest only (no raw data).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DecisionRecord(BaseModel):
    """Immutable gate decision record for auditability.

    - decision: ALLOW or DENY
    - profile_id: action identifier that matched a profile
    - profile_hash: fingerprint of the policy profile used (or empty)
    - matched_rules: names of rules that ran (without being denied)
    - reason_codes: list of GateReasonCode values that led to the decision
    - input_digest: SHA256 hex of canonicalized input (never raw data)
    - trace_id: UUID linking this decision to HTTP request/log context
    - ts_utc: datetime (timezone-aware UTC) when decision was made
    """

    model_config = ConfigDict(extra="forbid")

    decision: Literal["ALLOW", "DENY"]
    profile_id: str
    profile_hash: str
    matched_rules: List[str]
    reason_codes: List[str]
    input_digest: str
    trace_id: str
    ts_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("ts_utc")
    @classmethod
    def validate_ts_utc_is_utc_aware(cls, v: datetime) -> datetime:
        """Validate ts_utc is timezone-aware and in UTC."""
        if v.tzinfo is None:
            raise ValueError("ts_utc must be timezone-aware (UTC)")
        if v.tzinfo != timezone.utc:
            raise ValueError("ts_utc must be in UTC timezone")
        return v

    @field_validator("reason_codes")
    @classmethod
    def validate_reason_codes_non_empty_when_deny(cls, v: List[str], info) -> List[str]:
        """Ensure reason_codes is non-empty when decision is DENY."""
        decision = info.data.get("decision")
        if decision == "DENY" and not v:
            raise ValueError("reason_codes must be non-empty when decision is DENY")
        return v


def make_input_digest(payload: Any) -> str:
    """Compute SHA256 digest of canonicalized input.

    - Sorts dict keys and uses compact JSON separators for determinism
    - Returns hex digest of canonical JSON string
    - If not JSON-serializable, uses str() representation as fallback
    - Ensures no loss of Unicode characters (ensure_ascii=False)
    """
    try:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError):
        # Fallback: non-JSON-serializable values use str representation
        canonical = str(payload)

    blob = canonical.encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
