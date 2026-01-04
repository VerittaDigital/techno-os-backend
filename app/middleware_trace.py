"""Trace correlation middleware for request/response tracking.

Implements G6: Ensures every request/response carries X-TRACE-ID header.
- Validates or generates trace_id
- Stores in request.state for downstream use
- Injects into response headers
"""

import re
from uuid import uuid4
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def _validate_and_normalize_trace_id(trace_id_str: str) -> str:
    """Validate trace_id format. If invalid, return None (will generate new).
    
    Valid format: UUID (with or without hyphens).
    """
    if not isinstance(trace_id_str, str):
        return None
    # Accept UUID format with or without hyphens
    if not re.match(r"^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}$", trace_id_str.lower()):
        return None
    return trace_id_str


def _generate_trace_id() -> str:
    """Generate new trace_id as UUID v4."""
    return str(uuid4())


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
