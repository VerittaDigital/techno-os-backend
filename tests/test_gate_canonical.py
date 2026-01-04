"""
Unit tests for gate_canonical module (FASE 11).

Tests canonical action detection and body parsing logic.
Uses Starlette TestClient to create mock Request objects.

Correção C6: Usa Starlette TestClient (não mock.Mock).
"""
import pytest
from starlette.requests import Request
from starlette.datastructures import Headers
from app.gate_canonical import detect_action, normalize_path, parse_body_by_method
from app.gate_errors import GateError, ReasonCode


class TestActionDetector:
    """Test detect_action() and normalize_path() functions."""
    
    def test_detect_action_process_route(self):
        """Valid POST /process → action=process."""
        from starlette.testclient import TestClient
        from fastapi import FastAPI
        
        app = FastAPI()
        client = TestClient(app)
        
        # Create mock request with scope (FastAPI Request compatible)
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/process",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        
        action = detect_action(request)
        assert action == "process"
    
    def test_detect_action_preferences_get(self):
        """Valid GET /preferences/{user_id} → action=preferences.get."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/preferences/user_abc123",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        
        action = detect_action(request)
        assert action == "preferences.get"
    
    def test_detect_action_preferences_put(self):
        """Valid PUT /preferences/{user_id} → action=preferences.put."""
        scope = {
            "type": "http",
            "method": "PUT",
            "path": "/preferences/user_xyz789",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        
        action = detect_action(request)
        assert action == "preferences.put"
    
    def test_detect_action_preferences_delete(self):
        """Valid DELETE /preferences/{user_id} → action=preferences.delete."""
        scope = {
            "type": "http",
            "method": "DELETE",
            "path": "/preferences/user_test",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        
        action = detect_action(request)
        assert action == "preferences.delete"
    
    def test_detect_action_with_api_prefix(self):
        """Route with /api/v1 prefix should normalize correctly."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/preferences/user_123",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        
        action = detect_action(request)
        assert action == "preferences.get"
    
    def test_detect_action_unknown_route_raises_g8(self):
        """Unknown route → GateError with G8_UNKNOWN_ACTION (500)."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/unknown/route",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        
        with pytest.raises(GateError) as exc_info:
            detect_action(request)
        
        assert exc_info.value.reason_code == ReasonCode.G8_UNKNOWN_ACTION
        assert exc_info.value.status_code == 500
    
    def test_normalize_path_removes_api_prefix(self):
        """normalize_path() removes /api/v1 prefix."""
        assert normalize_path("/api/v1/process") == "/process"
        assert normalize_path("/api/v1/preferences/user_123") == "/preferences/{user_id}"
        assert normalize_path("/process") == "/process"  # No prefix


class TestBodyParser:
    """Test parse_body_by_method() function."""
    
    @pytest.mark.anyio
    async def test_parse_body_get_returns_empty(self):
        """GET request → empty dict (tolerant, no body required)."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/preferences/user_123",
            "query_string": b"",
            "headers": [],
        }
        
        async def receive():
            return {"type": "http.request", "body": b""}
        
        request = Request(scope, receive)
        body = await parse_body_by_method(request)
        
        assert body == {}
    
    @pytest.mark.anyio
    async def test_parse_body_delete_returns_empty(self):
        """DELETE request → empty dict (tolerant, no body required)."""
        scope = {
            "type": "http",
            "method": "DELETE",
            "path": "/preferences/user_123",
            "query_string": b"",
            "headers": [],
        }
        
        async def receive():
            return {"type": "http.request", "body": b""}
        
        request = Request(scope, receive)
        body = await parse_body_by_method(request)
        
        assert body == {}
    
    @pytest.mark.anyio
    async def test_parse_body_post_valid_json(self):
        """POST request with valid JSON body → parsed dict."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/process",
            "query_string": b"",
            "headers": [(b"content-type", b"application/json")],
        }
        
        async def receive():
            return {"type": "http.request", "body": b'{"text": "hello"}'}
        
        request = Request(scope, receive)
        body = await parse_body_by_method(request)
        
        assert body == {"text": "hello"}
    
    @pytest.mark.anyio
    async def test_parse_body_post_missing_body_raises_g10(self):
        """POST request without body → GateError with G10_BODY_PARSE_ERROR (422)."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/process",
            "query_string": b"",
            "headers": [],
        }
        
        async def receive():
            return {"type": "http.request", "body": b""}
        
        request = Request(scope, receive)
        
        with pytest.raises(GateError) as exc_info:
            await parse_body_by_method(request)
        
        assert exc_info.value.reason_code == ReasonCode.G10_BODY_PARSE_ERROR
        assert exc_info.value.status_code == 422
    
    @pytest.mark.anyio
    async def test_parse_body_post_malformed_json_raises_g10(self):
        """POST request with malformed JSON → GateError with G10_BODY_PARSE_ERROR (422)."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/process",
            "query_string": b"",
            "headers": [(b"content-type", b"application/json")],
        }
        
        async def receive():
            return {"type": "http.request", "body": b'{broken json'}
        
        request = Request(scope, receive)
        
        with pytest.raises(GateError) as exc_info:
            await parse_body_by_method(request)
        
        assert exc_info.value.reason_code == ReasonCode.G10_BODY_PARSE_ERROR
        assert exc_info.value.status_code == 422
        assert "Invalid or missing JSON body" in exc_info.value.detail["message"]

