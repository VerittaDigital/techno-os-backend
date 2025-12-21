"""Structured audit logging for gate decisions.

Writes one JSON line per decision. No raw payload or PII.
Uses Python's standard logging, configured for stdout/file rotation.
"""
from __future__ import annotations

import logging

from app.decision_record import DecisionRecord

# Named logger for gate audit trail
logger = logging.getLogger("gate_audit")


def log_decision(record: DecisionRecord) -> None:
    """Log a gate decision as a single JSON line.

    - Serializes DecisionRecord to JSON
    - Contains only structured metadata (no raw payload)
    - One line per decision for parsing and audit analysis
    """
    logger.info(record.model_dump_json())
