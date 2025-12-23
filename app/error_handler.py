"""Global exception handlers for error normalization.

Implements G11: Normalizes all errors into a consistent envelope.
- HTTPException (preserved status_code)
- RequestValidationError (400 invalid_request_shape)
- Generic Exception (500 internal_error)

Always includes: error, message, trace_id, reason_codes
Never includes: stack traces, api_key, tokens, secrets
"""

import logging
from typing import Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def build_error(
    error: str,
    message: str,
    trace_id: str,
    reason_codes: list[str] | None = None,
) -> dict:
    """Build normalized error envelope.
    
    Args:
        error: Error code/category (e.g., "missing_authorization")
        message: User-friendly message (must not contain secrets)
        trace_id: Request trace ID
        reason_codes: List of reason codes for audit (optional)
    
    Returns:
        Dict with error envelope
    """
    return {
        "error": error,
        "message": message,
        "trace_id": trace_id,
        "reason_codes": reason_codes or [],
    }


def _get_trace_id_from_request(request: Request) -> str:
    """Extract trace_id from request.state, or generate fallback."""
    if hasattr(request, "state") and hasattr(request.state, "trace_id"):
        return request.state.trace_id
    
    # Fallback: generate minimal trace_id if middleware failed
    import secrets
    return f"trc_{secrets.token_hex(8)}"


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException."""
    trace_id = _get_trace_id_from_request(request)
    
    # Determine error code from detail
    error_code = str(exc.detail) if exc.detail else "http_error"
    
    # Map common status codes to error codes
    if exc.status_code == 401:
        error_code = error_code if error_code != "Unauthorized" else "unauthorized"
    elif exc.status_code == 403:
        error_code = error_code if error_code != "Forbidden" else "forbidden"
    elif exc.status_code == 404:
        error_code = error_code if error_code != "Not Found" else "not_found"
    
    error_envelope = build_error(
        error=error_code,
        message=str(exc.detail) if exc.detail else "An error occurred",
        trace_id=trace_id,
        reason_codes=[],
    )
    
    response = JSONResponse(
        status_code=exc.status_code,
        content=error_envelope,
    )
    response.headers["X-TRACE-ID"] = trace_id
    return response


async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic/FastAPI validation errors."""
    trace_id = _get_trace_id_from_request(request)
    
    error_envelope = build_error(
        error="invalid_request_shape",
        message="Request validation failed",
        trace_id=trace_id,
        reason_codes=["pydantic_validation_error"],
    )
    
    response = JSONResponse(
        status_code=400,
        content=error_envelope,
    )
    response.headers["X-TRACE-ID"] = trace_id
    return response


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exception."""
    trace_id = _get_trace_id_from_request(request)
    
    # Log the exception for debugging (but don't expose to client)
    logger.exception(
        f"Unhandled exception (trace_id={trace_id})",
        exc_info=exc,
    )
    
    error_envelope = build_error(
        error="internal_error",
        message="An internal error occurred",
        trace_id=trace_id,
        reason_codes=["unhandled_exception"],
    )
    
    response = JSONResponse(
        status_code=500,
        content=error_envelope,
    )
    response.headers["X-TRACE-ID"] = trace_id
    return response


def register_error_handlers(app: FastAPI) -> None:
    """Register all error handlers with FastAPI app."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
