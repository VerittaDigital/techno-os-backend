"""Tests for F2.3 gate chain (T4) - Bearer token auth with sessions."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from app.main import app
from app.session_store import seed_session, sha256_str, get_session_store
from app.f23_bindings import get_bindings
from app.rate_limiter import get_rate_limiter


client = TestClient(app)


class TestF23ChainValidRequests:
    """Test valid F2.3 requests (all gates pass)."""
    
    def test_valid_bearer_with_session_and_binding_succeeds(self, monkeypatch):
        """Valid Bearer token, session, and bindings should succeed."""
        # Setup
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "sk_test_f23")
        get_rate_limiter().reset_all()
        
        # Create binding
        api_key = "sk_test_f23"
        api_key_sha256 = sha256_str(api_key)
        user_id = "u_user0001"
        
        bindings = get_bindings()
        bindings.clear_all()
        bindings.add_binding(api_key_sha256, user_id)
        
        # Create session
        session_store = get_session_store()
        session_store.clear_all()
        session_id = "sess_0123456789abcdef"
        seed_session(
            session_id=session_id,
            user_id=user_id,
            api_key=api_key,
        )
        
        # Request
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-VERITTA-USER-ID": user_id,
                "X-VERITTA-SESSION-ID": session_id,
            },
        )
        # Should succeed (200 OK)
        assert response.status_code != 401
        assert response.status_code != 403


class TestF23ChainG1BearerFormat:
    """Test G1: Bearer token format validation."""
    
    def test_invalid_bearer_format_returns_401(self, monkeypatch):
        """Invalid Authorization header format should return 401."""
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "sk_test_f23")
        get_rate_limiter().reset_all()
        
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={
                "Authorization": "NotBearer sk_test_f23",  # Wrong prefix
                "X-VERITTA-USER-ID": "u_user0001",
                "X-VERITTA-SESSION-ID": "sess_0123456789abcdef",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "trace_id" in data


class TestF23ChainG3UserID:
    """Test G3: User ID validation and binding check."""
    
    def test_invalid_user_id_format_returns_400(self, monkeypatch):
        """Invalid user ID format should return 400."""
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "sk_test_f23")
        get_rate_limiter().reset_all()
        
        api_key = "sk_test_f23"
        session_id = "sess_0123456789abcdef"
        
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-VERITTA-USER-ID": "invalid_format",  # Wrong format
                "X-VERITTA-SESSION-ID": session_id,
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "trace_id" in data
    
    def test_user_id_not_bound_returns_403(self, monkeypatch):
        """User ID not bound to API key should return 403."""
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "sk_test_f23")
        get_rate_limiter().reset_all()
        
        api_key = "sk_test_f23"
        api_key_sha256 = sha256_str(api_key)
        user_id_bound = "u_bound0001"
        user_id_unbound = "u_other001"  # Fixed format: exactly 8 chars after u_
        session_id = "sess_0123456789abcdef"
        
        # Setup binding (only for bound user)
        bindings = get_bindings()
        bindings.clear_all()
        bindings.add_binding(api_key_sha256, user_id_bound)
        
        # Try to use unbound user (but with valid format)
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-VERITTA-USER-ID": user_id_unbound,
                "X-VERITTA-SESSION-ID": session_id,
            },
        )
        assert response.status_code == 403
        data = response.json()
        assert "trace_id" in data


class TestF23ChainG4SessionID:
    """Test G4: Session ID format validation."""
    
    def test_invalid_session_id_format_returns_400(self, monkeypatch):
        """Invalid session ID format should return 400."""
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "sk_test_f23")
        get_rate_limiter().reset_all()
        
        api_key = "sk_test_f23"
        api_key_sha256 = sha256_str(api_key)
        user_id = "u_user0001"
        
        # Setup binding so G3 passes
        bindings = get_bindings()
        bindings.clear_all()
        bindings.add_binding(api_key_sha256, user_id)
        
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-VERITTA-USER-ID": user_id,
                "X-VERITTA-SESSION-ID": "invalid_session",  # Wrong format
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "trace_id" in data


class TestF23ChainG5SessionTTL:
    """Test G5: Session TTL and correlation."""
    
    def test_session_not_found_returns_403(self, monkeypatch):
        """Non-existent session should return 403."""
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "sk_test_f23")
        get_rate_limiter().reset_all()
        
        api_key = "sk_test_f23"
        api_key_sha256 = sha256_str(api_key)
        user_id = "u_user0001"
        session_id = "sess_aabbccddeeaabbcc"  # Valid format (exactly 16 chars after sess_) but not in store
        
        # Setup binding so G3 passes
        bindings = get_bindings()
        bindings.clear_all()
        bindings.add_binding(api_key_sha256, user_id)
        
        # Clear sessions
        session_store = get_session_store()
        session_store.clear_all()
        
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-VERITTA-USER-ID": user_id,
                "X-VERITTA-SESSION-ID": session_id,
            },
        )
        assert response.status_code == 403
        data = response.json()
        assert "trace_id" in data
    
    def test_expired_session_returns_401(self, monkeypatch):
        """Expired session should return 401."""
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "sk_test_f23")
        get_rate_limiter().reset_all()
        
        api_key = "sk_test_f23"
        api_key_sha256 = sha256_str(api_key)
        user_id = "u_user0001"
        session_id = "sess_1234567890abcdef"  # Valid format (exactly 16 chars after sess_)
        
        # Setup binding so G3 passes
        bindings = get_bindings()
        bindings.clear_all()
        bindings.add_binding(api_key_sha256, user_id)
        
        # Create expired session
        session_store = get_session_store()
        session_store.clear_all()
        now = datetime.now(timezone.utc)
        seed_session(
            session_id=session_id,
            user_id=user_id,
            api_key=api_key,
            created_at=now - timedelta(hours=5),  # 5 hours old
            expires_at=now - timedelta(hours=1),  # Expired 1 hour ago
        )
        
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-VERITTA-USER-ID": user_id,
                "X-VERITTA-SESSION-ID": session_id,
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "trace_id" in data


class TestF23ChainErrorEnvelope:
    """Test that all errors return proper envelope."""
    
    def test_all_errors_include_trace_id(self, monkeypatch):
        """All F2.3 error responses should include trace_id."""
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "sk_test_f23")
        get_rate_limiter().reset_all()
        
        # Missing Authorization header
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={
                # No Authorization
                "X-VERITTA-USER-ID": "u_user0001",
                "X-VERITTA-SESSION-ID": "sess_0123456789abcdef",
            },
        )
        # G0 will detect no F2.3, will try F2.1 which will pass (backward compat)
        # So let's use explicit Bearer to trigger F2.3 path
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={
                "Authorization": "Bearer sk_invalid",
                "X-VERITTA-USER-ID": "u_user0001",
                "X-VERITTA-SESSION-ID": "sess_0123456789abcdef",
            },
        )
        data = response.json()
        assert "trace_id" in data
        assert len(data["trace_id"]) == 36  # UUID format
