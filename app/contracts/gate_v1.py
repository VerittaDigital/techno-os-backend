from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GateDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class GateReasonCode(str, Enum):
    OK = "OK"
    UNKNOWN_ACTION = "UNKNOWN_ACTION"
    UNKNOWN_FIELDS_PRESENT = "UNKNOWN_FIELDS_PRESENT"
    ADMIN_SIGNAL_FORBIDDEN = "ADMIN_SIGNAL_FORBIDDEN"
    EXTERNAL_FIELDS_NOT_ALLOWED = "EXTERNAL_FIELDS_NOT_ALLOWED"
    RULE_EXCEPTION_FAIL_CLOSED = "RULE_EXCEPTION_FAIL_CLOSED"


class GateReason(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: GateReasonCode
    message: str
    evidence: Dict[str, Any] = Field(default_factory=dict)


class GateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    allow_external: bool = False
    deny_unknown_fields: bool = True

    request_id: Optional[str] = None
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: GateDecision
    reasons: List[GateReason] = Field(default_factory=list)

    action: str
    evaluated_keys: List[str] = Field(default_factory=list)
    
    profile_hash: str  # ← P1.5: Profile fingerprint (never empty)
    matched_rules: List[str] = Field(default_factory=list)  # ← P1.5: Rules that matched (may be empty)

    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
