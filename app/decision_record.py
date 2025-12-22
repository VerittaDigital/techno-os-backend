"""Canonical decision record for gate audit trail.

Immutable, deterministic record of every gate evaluation decision.
All fields are non-sensitive; payload digest only (no raw data).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.digests import sha256_json_or_none


class DecisionRecord(BaseModel):
    """Immutable gate decision record for auditability.

    - decision: ALLOW or DENY
    - profile_id: action identifier that matched a profile
    - profile_hash: fingerprint of the policy profile used (or empty)
    - matched_rules: names of rules that ran (without being denied)
    - reason_codes: list of GateReasonCode values that led to the decision
    - input_digest: SHA256 hex of canonicalized input (None if non-JSON, privacy-first)
    - trace_id: UUID linking this decision to HTTP request/log context
    - ts_utc: datetime (timezone-aware UTC) when decision was made
    """

    model_config = ConfigDict(extra="forbid")

    decision: Literal["ALLOW", "DENY"]
    profile_id: str
    profile_hash: str
    matched_rules: List[str]
    reason_codes: List[str]
    input_digest: Optional[str]  # ← Can be None for non-JSON payloads
    trace_id: str
    ts_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("trace_id")
    @classmethod
    def validate_trace_id_is_valid_uuid(cls, v: str) -> str:
        """Validate trace_id is non-empty and a valid UUID."""
        if not v or not v.strip():
            raise ValueError("trace_id must not be empty")
        try:
            uuid.UUID(v)
        except (ValueError, AttributeError):
            raise ValueError("trace_id must be a valid UUID")
        return v

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


def make_input_digest(payload: Any) -> Optional[str]:
    """Compute SHA256 digest of canonicalized input.

    - Sorts dict keys and uses compact JSON separators for determinism
    - Returns hex digest of canonical JSON string
    - If not JSON-serializable, returns None (privacy-first, no str() fallback)
    - Ensures no loss of Unicode characters (ensure_ascii=False)
    
    Rule (P1.4):
        Non-JSON payloads get None (not str() fallback).
        This aligns with pipeline digest rule.
    """
    return sha256_json_or_none(payload)
