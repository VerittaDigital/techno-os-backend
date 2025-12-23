"""Trace correlation middleware for request/response tracking.

Implements G6: Ensures every request/response carries X-TRACE-ID header.
- Validates or generates trace_id
- Stores in request.state for downstream use
- Injects into response headers
"""

import secrets
import re
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def _validate_and_normalize_trace_id(trace_id_str: str) -> str:
    """Validate trace_id format. If invalid, return None (will generate new).
    
    Valid format: alphanumeric + underscore, length 8-64 chars.
    """
    if not isinstance(trace_id_str, str):
        return None
    if not re.match(r"^[a-zA-Z0-9_-]{8,64}$", trace_id_str):
        return None
    return trace_id_str


def _generate_trace_id() -> str:
    """Generate new trace_id: 'trc_' + 16 random hex chars."""
    random_hex = secrets.token_hex(8)  # 16 hex chars
    return f"trc_{random_hex}"


class TraceCorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware that injects trace_id into every request and response."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract inbound trace_id from header (if present)
        inbound_trace_id = request.headers.get("X-TRACE-ID")
        
        # Validate or generate trace_id
        if inbound_trace_id:
            trace_id = _validate_and_normalize_trace_id(inbound_trace_id)
        else:
            trace_id = None
        
        # Generate new if validation failed or not present
        if not trace_id:
            trace_id = _generate_trace_id()
        
        # Store in request.state for downstream use (handlers, error handlers, etc.)
        request.state.trace_id = trace_id
        
        # Call next middleware/handler
        try:
            response = await call_next(request)
        except Exception as e:
            # If exception occurs, we still inject X-TRACE-ID in the error response
            # This is handled by error handlers, but we set the state
            raise
        
        # Inject X-TRACE-ID into response headers
        response.headers["X-TRACE-ID"] = trace_id
        
        return response
