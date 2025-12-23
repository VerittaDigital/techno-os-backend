"""Canonical error envelope builder for HTTP responses.

All HTTPException details must use http_error_detail() to ensure
consistent error structure: error, message, trace_id, reason_codes.
"""

from typing import Optional, List, Dict, Any


def http_error_detail(
    error: str,
    message: str,
    trace_id: str,
    reason_codes: List[str],
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build canonical error envelope for HTTPException detail.
    
    Args:
        error: Error code (e.g., 'unauthorized', 'bad_request', 'forbidden', 'internal_error')
        message: Human-readable error message
        trace_id: Request trace ID (UUID)
        reason_codes: List of gate/reason codes (e.g., ['G0_F21_missing_token', 'G2_invalid_api_key'])
        extra: Optional additional fields (merged into envelope)
    
    Returns:
        Dict with canonical structure: {error, message, trace_id, reason_codes, ...extra}
    """
    envelope = {
        "error": error,
        "message": message,
        "trace_id": trace_id,
        "reason_codes": reason_codes,
    }
    if extra:
        envelope.update(extra)
    return envelope
