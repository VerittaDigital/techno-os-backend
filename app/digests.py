"""
Canonical digest computation for privacy-first audit logging.

Rule: JSON-serializable payloads get SHA256 digest; non-JSON get None.
No fallback to str() representation (privacy by design).
"""

import hashlib
import json
from typing import Any, Optional


def sha256_json_or_none(obj: Any) -> Optional[str]:
    """
    Compute SHA256 digest of canonical JSON, or None if not JSON-serializable.

    Args:
        obj: Any Python object

    Returns:
        Hex digest of SHA256(canonical_json_bytes) if JSON-serializable, None otherwise.

    Rule (P1.4):
        - Try to serialize as canonical JSON (sorted keys, compact separators, UTF-8)
        - If successful, return hex digest
        - If TypeError or ValueError (non-JSON-serializable), return None
        - NO FALLBACK to str() representation (privacy by design)
    """
    try:
        canonical = json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        blob = canonical.encode("utf-8")
        return hashlib.sha256(blob).hexdigest()
    except (TypeError, ValueError):
        # Non-JSON-serializable: return None (privacy-first)
        return None
