"""Action registry with fingerprinting for drift detection."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, field_validator


# Semver regex: X.Y.Z where X, Y, Z are integers
SEMVER_REGEX = re.compile(r'^\d+\.\d+\.\d+$')


class ActionMeta(BaseModel):
    """Metadata for a single action in the registry.
    
    Fields:
    - description: human-readable action description
    - executor: executor identifier
    - version: deprecated, use action_version
    - action_version: semantic version (optional, e.g., "1.0.0")
    - required_capabilities: list of required executor capabilities (ordered, normalized)
    - min_executor_version: minimum executor version required (optional)
    """
    
    model_config = ConfigDict(extra="allow")  # Allow backward compat fields like "version"
    
    description: str
    executor: str
    version: Optional[str] = None  # Legacy field for backward compat
    action_version: Optional[str] = None
    required_capabilities: List[str] = []
    min_executor_version: Optional[str] = None
    
    @field_validator("action_version")
    @classmethod
    def validate_action_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate action_version follows semver format if provided."""
        if v is not None and not SEMVER_REGEX.match(v):
            raise ValueError(f"action_version must follow semver (X.Y.Z), got: {v}")
        return v
    
    @field_validator("required_capabilities")
    @classmethod
    def normalize_capabilities(cls, v: List[str]) -> List[str]:
        """Normalize and sort capabilities for determinism."""
        if not v:
            return []
        # Strip whitespace, uppercase, deduplicate, and sort
        normalized = sorted(set(cap.strip().upper() for cap in v if cap.strip()))
        return normalized
    
    @field_validator("min_executor_version")
    @classmethod
    def validate_min_executor_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate min_executor_version follows semver format if provided."""
        if v is not None and not SEMVER_REGEX.match(v):
            raise ValueError(f"min_executor_version must follow semver (X.Y.Z), got: {v}")
        return v


class ActionRegistry(BaseModel):
    """Immutable registry of all governable actions.
    
    Fields:
    - actions: dict mapping action_id to ActionMeta (or dict for backward compat)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    actions: Dict[str, Any]  # Use Any to support both ActionMeta and dict during transition


def get_action_registry() -> ActionRegistry:
    """Return the canonical action registry.
    
    This is the source of truth for all actions that can be executed
    under V-COF governance.
    """
    return ActionRegistry(
        actions={
            "process": {
                "description": "Process text input",
                "executor": "text_process_v1",
                "version": "1.0",  # Legacy field
                "action_version": "1.0.0",  # AG-03: explicit semver
                "required_capabilities": ["TEXT_PROCESSING"],
                "min_executor_version": "1.0.0",
            },
        }
    )


def compute_registry_fingerprint(registry: ActionRegistry) -> str:
    """Compute SHA256 fingerprint of action registry.
    
    Used to detect unintended drift (actions added/removed/modified).
    Fingerprint is deterministic across same registry.
    """
    canonical = json.dumps(
        registry.model_dump(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    blob = canonical.encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
