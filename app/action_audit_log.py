"""Action audit logger for execution proof trail.

Emits structured JSON logs for every ActionResult.
No raw payloads, outputs, or stack traces. Only digests and metadata.
"""
from __future__ import annotations

import logging

from app.action_contracts import ActionResult
from app.audit_log import AuditLogError
from app.audit_sink import append_audit_record

# Named logger for action execution audit trail
logger = logging.getLogger("action_audit")


def log_action_result(result: ActionResult) -> None:
    """Log an action execution result as a single JSON line.

    - Serializes ActionResult to JSON
    - Contains only structured metadata (no raw payload/output)
    - One line per execution for parsing and audit analysis
    - Logs MUST occur even on FAILED/BLOCKED outcomes
    - event_type: "action_audit" for offline reconciliation
    
    Raises AuditLogError if logging fails (fail-closed).
    """
    try:
        # Persist to file first (fail-closed)
        result_dict = result.model_dump(mode="json")
        result_dict["event_type"] = "action_audit"
        append_audit_record(result_dict)
        
        # Then emit to logger
        logger.info(result.model_dump_json())
    except Exception as e:
        raise AuditLogError(f"Failed to log action result (trace_id={result.trace_id}, action={result.action}): {e}") from e
