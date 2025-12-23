"""Structured audit logging for gate decisions.

Writes one JSON line per decision. No raw payload or PII.
Uses Python's standard logging, configured for stdout/file rotation.
"""
from __future__ import annotations

import logging

from app.audit_sink import append_audit_record
from app.decision_record import DecisionRecord
from app.gate_artifacts import profiles_fingerprint_sha256


class AuditLogError(Exception):
    """Raised when audit logging fails. Signals critical failure in governance trail."""
    pass


# Named logger for gate audit trail
logger = logging.getLogger("gate_audit")


def log_decision(record: DecisionRecord) -> None:
    """Log a gate decision as a single JSON line.

    - Serializes DecisionRecord to JSON
    - Contains only structured metadata (no raw payload)
    - One line per decision for parsing and audit analysis
    - event_type: "decision_audit" for offline reconciliation
    
    Raises AuditLogError if logging fails (fail-closed).
    """
    try:
        # Persist to file first (fail-closed)
        record_dict = record.model_dump(mode="json")
        
        # P1.1: Enforce non-empty profile_hash in persisted record
        ph = record_dict.get("profile_hash")
        if ph is None or (isinstance(ph, str) and not ph.strip()):
            record_dict["profile_hash"] = profiles_fingerprint_sha256()
        
        record_dict["event_type"] = "decision_audit"
        append_audit_record(record_dict)
        
        # Then emit to logger
        logger.info(record.model_dump_json())
    except Exception as e:
        raise AuditLogError(f"Failed to log gate decision (trace_id={getattr(record, 'trace_id', 'unknown')}): {e}") from e
