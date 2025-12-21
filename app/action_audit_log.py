"""Action audit logger for execution proof trail.

Emits structured JSON logs for every ActionResult.
No raw payloads, outputs, or stack traces. Only digests and metadata.
"""
from __future__ import annotations

import logging

from app.action_contracts import ActionResult
from app.audit_log import AuditLogError

# Named logger for action execution audit trail
logger = logging.getLogger("action_audit")


def log_action_result(result: ActionResult) -> None:
    """Log an action execution result as a single JSON line.

    - Serializes ActionResult to JSON
    - Contains only structured metadata (no raw payload/output)
    - One line per execution for parsing and audit analysis
    - Logs MUST occur even on FAILED/BLOCKED outcomes
    
    Raises AuditLogError if logging fails (fail-closed).
    """
    try:
        logger.info(result.model_dump_json())
    except Exception as e:
        raise AuditLogError(f"Failed to log action result (trace_id={result.trace_id}, action={result.action}): {e}") from e
