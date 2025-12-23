"""Tests for G0: Feature flag routing (auth mode detection).

Validates that:
1. Requests without Authorization or X-API-Key => 401 missing_authorization
2. Requests with X-API-Key => auth_mode F2.1
3. Requests with Authorization => 501 f23_not_implemented (temporarily blocked)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_missing_auth_headers_returns_401(client):
    """POST /process without auth headers should return 401 missing_authorization."""
    response = client.post(
        "/process",
        json={"text": "test"},
    )
    
    # Should be 401 (missing authorization)
    assert response.status_code == 401
    
    # Check normalized error envelope
    data = response.json()
    assert "error" in data
    assert "trace_id" in data
    assert "X-TRACE-ID" in response.headers


def test_missing_auth_error_details(client):
    """Error message should indicate missing authorization."""
    response = client.post(
        "/process",
        json={"text": "test"},
    )
    
    assert response.status_code == 401
    data = response.json()
    
    # Error should be about missing auth
    error_str = str(data.get("error", "")).lower()
    detail_str = str(data.get("message", "")).lower()
    
    # Should indicate missing auth (not bad key, not forbidden, etc.)
    assert "missing" in error_str or "unauthorized" in error_str or "missing" in detail_str


def test_authorization_header_returns_501(client):
    """POST /process with Authorization header (F2.3) should return 401 on invalid token."""
    response = client.post(
        "/process",
        json={"text": "test"},
        headers={"Authorization": "Bearer fake_token"},
    )
    
    # Should be 401 (F2.3 validates Bearer token format and returns 401 on invalid)
    assert response.status_code == 401
    
    # Check error envelope
    data = response.json()
    assert "error" in data
    assert "trace_id" in data
    assert "X-TRACE-ID" in response.headers
    
    # Error message should indicate authorization failure (either bearer format or api key)
    detail = str(data.get("message", "")).lower()
    assert "bearer" in detail or "api key" in detail or "authorization" in detail or "token" in detail


def test_x_api_key_header_processed(client):
    """POST /process with X-API-Key header (F2.1) should attempt F2.1 flow."""
    # Note: This may fail at F2.1 validation, but should NOT return 501
    response = client.post(
        "/process",
        json={"text": "test"},
        headers={"X-API-Key": "fake_key"},
    )
    
    # Should NOT be 501 (F2.3 not implemented)
    # It may be 401 (invalid key) or 403 (gate denied), but NOT 501
    assert response.status_code != 501
    
    # Should have X-TRACE-ID
    assert "X-TRACE-ID" in response.headers


def test_trace_id_in_missing_auth_error(client):
    """Missing auth error should include X-TRACE-ID header and body."""
    response = client.post(
        "/process",
        json={"text": "test"},
    )
    
    assert response.status_code == 401
    data = response.json()
    
    # trace_id in body
    assert "trace_id" in data
    assert data["trace_id"] != ""
    
    # X-TRACE-ID in header
    assert "X-TRACE-ID" in response.headers
    assert response.headers["X-TRACE-ID"] != ""
    # Note: X-TRACE-ID may use different format (trc_...) than body UUID


def test_f23_temporarily_blocked(client):
    """F2.3 (Authorization Bearer) validates token and returns 401 on invalid."""
    response = client.post(
        "/process",
        json={"text": "test"},
        headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"},
    )
    
    assert response.status_code == 401
    data = response.json()
    
    # Should indicate authorization failure
    assert "error" in data
    error_lower = str(data.get("error", "")).lower()
    assert "unauthorized" in error_lower or "bearer" in error_lower


def test_health_endpoint_no_auth_required(client):
    """GET /health should NOT require auth (no dependencies)."""
    # Health check should work without any auth headers
    response = client.get("/health")
    
    assert response.status_code == 200
    assert "X-TRACE-ID" in response.headers
    
    # Should not have error fields
    data = response.json()
    assert "error" not in data
