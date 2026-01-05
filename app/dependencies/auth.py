"""FastAPI dependencies for user preferences endpoints (F9.9-A).

Dependencies extract user_id from validated F2.3 auth headers.
No JWT claims parsing - user_id comes from X-VERITTA-USER-ID header.
"""

from fastapi import HTTPException, Request


async def get_user_from_gate(request: Request) -> str:
    """
    Extract user_id from F2.3 gate-validated header.
    
    Pre-condition: gate_request() dependency has already validated:
    - Authorization: Bearer header exists and is valid
    - X-VERITTA-USER-ID header exists and matches format u_[a-z0-9]{8}
    - user_id is bound to the api_key
    
    This dependency trusts upstream gate validation (fail-closed).
    If header is missing here, it indicates a gate bypass (internal error).
    
    Returns:
        user_id (str): Validated user identifier (format: u_[a-z0-9]{8})
    
    Raises:
        HTTPException 500: If header is missing (gate bypass detected)
    """
    user_id = request.headers.get("X-VERITTA-USER-ID", "").strip()
    
    if not user_id:
        # This should never happen if gate is working correctly
        # Fail-closed: reject request rather than proceeding with empty user_id
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Auth gate bypass detected (missing user_id)",
                "trace_id": getattr(request.state, "trace_id", "unknown"),
            }
        )
    
    return user_id
