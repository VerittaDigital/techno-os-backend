"""
Audit sink for persistent audit trail (JSONL append-only).

Writes audit records to file in JSONL format (one JSON per line).
Fail-closed: any write failure propagates as exception.
"""

import json
import os
from typing import Dict, Any


def get_audit_log_path() -> str:
    """
    Get audit log file path from environment variable.
    
    Returns:
        Path from VERITTA_AUDIT_LOG_PATH env var, or "./audit.log" if not set.
    """
    return os.environ.get("VERITTA_AUDIT_LOG_PATH", "./audit.log")


def append_audit_record(record: Dict[str, Any]) -> None:
    """
    Append audit record to JSONL file (fail-closed).
    
    Args:
        record: Dictionary to serialize as JSON line
    
    Raises:
        Any exception during file write (fail-closed: do not suppress)
    """
    log_path = get_audit_log_path()
    
    # Serialize to compact JSON (no whitespace)
    json_line = json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"
    
    # Append to file (fail-closed: exceptions propagate)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json_line)
        f.flush()
