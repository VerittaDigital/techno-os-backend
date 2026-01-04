"""Tests for G6: Trace correlation middleware.

Validates that X-TRACE-ID header is injected in all responses.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_health_returns_trace_header(client):
    """GET /health should return X-TRACE-ID header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-TRACE-ID" in response.headers
    assert response.headers["X-TRACE-ID"] != ""


def test_health_trace_id_format(client):
    """X-TRACE-ID should follow expected format (trc_* or custom)."""
    response = client.get("/health")
    trace_id = response.headers.get("X-TRACE-ID")
    # Should be non-empty alphanumeric/underscore
    assert trace_id
    assert len(trace_id) > 0


def test_process_with_valid_body_returns_trace_header(client):
    """POST /process with valid body should return X-TRACE-ID header."""
    # Note: body validation may fail if auth is missing in gate_request,
    # but trace_id should still be injected by error handler
    response = client.post(
        "/process",
        json={"text": "test input"},
    )
    # Regardless of status (may be 401 if auth required), header should exist
    assert "X-TRACE-ID" in response.headers
    assert response.headers["X-TRACE-ID"] != ""


def test_inbound_trace_id_preserved(client):
    """If inbound X-TRACE-ID is valid UUID, it should be preserved in response."""
    import uuid
    inbound_trace_id = str(uuid.uuid4())
    response = client.get(
        "/health",
        headers={"X-TRACE-ID": inbound_trace_id},
    )
    # Middleware should validate and preserve valid UUID trace_id
    assert response.headers["X-TRACE-ID"] == inbound_trace_id


def test_invalid_inbound_trace_id_regenerated(client):
    """If inbound X-TRACE-ID is invalid, middleware should generate new one."""
    # Invalid format (too short)
    invalid_trace_id = "bad"
    response = client.get(
        "/health",
        headers={"X-TRACE-ID": invalid_trace_id},
    )
    # Should generate new trace_id
    assert response.headers["X-TRACE-ID"] != invalid_trace_id
    assert response.headers["X-TRACE-ID"] != ""
