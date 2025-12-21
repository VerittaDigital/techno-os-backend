"""Canonical action contracts for governed execution layer.

ActionRequest and ActionResult are proof objects for the execution pipeline.
All fields are auditable and non-repudiable. No raw payloads or outputs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ActionRequest(BaseModel):
    """Immutable request to execute an action through the governed pipeline.

    - action: canonical action identifier (must exist in ACTION_REGISTRY)
    - payload: JSON-like dict (validated before execution)
    - trace_id: propagated from gate DecisionRecord for correlation
    - ts_utc: timezone-aware UTC timestamp when request was created
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    payload: dict[str, Any]
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


class ActionResult(BaseModel):
    """Immutable proof object of an execution outcome.

    This is the ONLY artifact returned by the execution pipeline.
    Raw outputs are NEVER included.

    - action: canonical action identifier
    - executor_id: which executor handled the request
    - executor_version: immutable version of executor code
    - status: SUCCESS, FAILED, BLOCKED, or PENDING (pre-audit only)
    - reason_codes: MUST be non-empty if status != SUCCESS
    - input_digest: SHA256 of canonical input (never raw payload)
    - output_digest: SHA256 of canonical output (or None if not serializable)
    - trace_id: links to DecisionRecord for full audit trail
    - ts_utc: timezone-aware UTC timestamp when execution completed
    """

    model_config = ConfigDict(extra="forbid")

    action: str
    executor_id: str
    executor_version: str
    status: Literal["SUCCESS", "FAILED", "BLOCKED", "PENDING"]
    reason_codes: list[str]
    input_digest: str
    output_digest: str | None
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
    def validate_reason_codes_non_empty_if_not_success(cls, v: list[str], info) -> list[str]:
        """Ensure reason_codes is non-empty when status is not SUCCESS or PENDING."""
        # info.data contains other validated fields
        status = info.data.get("status")
        if status and status not in ("SUCCESS", "PENDING") and not v:
            raise ValueError("reason_codes must be non-empty when status is not SUCCESS or PENDING")
        return v
