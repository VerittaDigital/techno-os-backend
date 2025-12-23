"""Tests for G11: Error normalization.

Validates that all errors return normalized envelope with trace_id.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def error_test_app():
    """Create a simple test app with error handlers for isolated testing."""
    from app.error_handler import register_error_handlers
    test_app = FastAPI()
    register_error_handlers(test_app)
    
    @test_app.get("/test-http-exception")
    def test_http_exception():
        raise HTTPException(status_code=401, detail="missing_authorization")
    
    @test_app.get("/test-invalid-json")
    def test_invalid_json():
        # This endpoint expects JSON but we'll send invalid
        pass
    
    return test_app


def test_trace_id_in_error_response(client):
    """Error responses should include trace_id in body."""
    # Request that will fail (invalid body format)
    response = client.post("/process", json={"invalid": "body"})
    
    # Check normalized envelope exists
    assert response.status_code in [400, 403]  # Either validation or auth error
    data = response.json()
    
    # Should have all required fields
    assert "error" in data
    assert "message" in data
    assert "trace_id" in data
    assert data["trace_id"] != ""


def test_error_response_has_trace_header(client):
    """Error responses should include X-TRACE-ID header."""
    response = client.post("/process", json={"invalid": "body"})
    
    # Both in header and in body
    assert "X-TRACE-ID" in response.headers
    assert response.headers["X-TRACE-ID"] != ""


def test_error_message_no_secrets(client):
    """Error messages should never contain API keys or secrets."""
    response = client.post("/process", json={"invalid": "body"})
    
    data = response.json()
    message = data.get("message", "").lower()
    error = data.get("error", "").lower()
    
    # Should not contain common secret patterns
    forbidden_words = ["api_key", "token", "secret", "password"]
    for word in forbidden_words:
        assert word not in message, f"Found '{word}' in error message"
        assert word not in error, f"Found '{word}' in error code"


def test_http_exception_handler_error_test_app(error_test_app):
    """Test HTTPException handler with isolated app."""
    client = TestClient(error_test_app)
    response = client.get("/test-http-exception")
    
    assert response.status_code == 401
    data = response.json()
    
    # Check envelope
    assert "error" in data
    assert "message" in data
    assert "trace_id" in data
    assert "reason_codes" in data
    
    # Check trace_id format
    assert data["trace_id"] != ""
    assert len(data["trace_id"]) > 5


def test_error_envelope_structure(client):
    """All error responses should have consistent envelope structure."""
    response = client.post("/process", json={})
    
    # If it's an error (any 4xx or 5xx), check envelope
    if response.status_code >= 400:
        data = response.json()
        
        # Must have all 4 required fields
        required_fields = {"error", "message", "trace_id", "reason_codes"}
        assert required_fields.issubset(set(data.keys())), \
            f"Missing fields: {required_fields - set(data.keys())}"
        
        # reason_codes must be a list
        assert isinstance(data["reason_codes"], list)
