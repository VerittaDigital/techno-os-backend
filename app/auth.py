"""
Beta minimal authentication module.

Implements fail-closed API key validation via X-API-Key header (F2.1).
Detects Authorization header for future F2.3 Bearer token support (G0).

Auth behavior:
- If VERITTA_BETA_API_KEY env var is set and non-empty: require valid key (fail-closed)
- If VERITTA_BETA_API_KEY is not set or empty: auth is optional (backward-compatible for tests)

G0 Auth mode detection:
- Authorization header present (Bearer token) => F2.3 mode
- X-API-Key header present => F2.1 mode
- Neither present => missing_authorization error
"""

import os
from typing import Literal, Optional
from fastapi import Header, HTTPException, Request


def get_expected_beta_key() -> Optional[str]:
    """
    Retrieve expected API key from environment variable.
    Returns None if not set (auth becomes optional).
    """
    return os.environ.get("VERITTA_BETA_API_KEY")


def require_beta_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """
    FastAPI dependency that validates X-API-Key header.
    
    Behavior depends on VERITTA_BETA_API_KEY env var:
    
    1. If VERITTA_BETA_API_KEY is set and non-empty:
       - Raises HTTPException(401) if header is missing or invalid
       - This is FAIL-CLOSED: invalid/missing = denied
    
    2. If VERITTA_BETA_API_KEY is not set or empty:
       - Auth is optional (allows backward compatibility for tests)
       - No exception raised
    
    This allows existing tests to run without modification,
    while beta tests can enforce auth by setting the env var.
    """
    expected_key = get_expected_beta_key()
    
    # If env var not set, auth is optional (backward compatible)
    if not expected_key:
        return
    
    # If env var is set, enforce fail-closed: header must match
    if x_api_key is None or x_api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )


def detect_auth_mode(request: Request) -> Optional[Literal["F2.3", "F2.1"]]:
    """Detect auth mode from request headers (G0).
    
    Returns:
        "F2.3" if Authorization header present (Bearer token)
        "F2.1" if X-API-Key header present
        None if neither header present
    
    Does NOT validate Bearer format or API key value yet.
    This is runtime detection only; validation happens downstream.
    """
    # Check for F2.3 Bearer token
    authorization = request.headers.get("Authorization")
    if authorization:
        return "F2.3"
    
    # Check for F2.1 API key
    x_api_key = request.headers.get("X-API-Key")
    if x_api_key:
        return "F2.1"
    
    # Neither header present
    return None
