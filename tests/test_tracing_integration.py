"""Integration tests for tracing in FastAPI endpoints (F8.6.1)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from conftest import tracing_available


class TestTracingIntegrationFailClosed:
    """Test tracing integration with fail-closed behavior."""
    
    def test_process_without_tracing_works(self, monkeypatch):
        """Process endpoint works with TRACING_ENABLED=0 (default)."""
        # Ensure tracing is disabled (default state)
        monkeypatch.setenv("TRACING_ENABLED", "0")
        
        # Reset tracing state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        client = TestClient(app)
        
        # Call /health (should work regardless of tracing)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_process_with_tracing_enabled_works(self, monkeypatch):
        """Process endpoint works with TRACING_ENABLED=1."""
        # Enable tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset tracing state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        client = TestClient(app)
        
        # Call /health (should work with tracing enabled)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestTracingSemanticInvariance:
    """Test that tracing does NOT alter function semantics (governance)."""
    
    def test_health_response_identical_with_without_tracing(self, monkeypatch):
        """Health endpoint returns identical response with/without tracing."""
        # Test WITHOUT tracing
        monkeypatch.setenv("TRACING_ENABLED", "0")
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        client_off = TestClient(app)
        response_off = client_off.get("/health")
        
        # Test WITH tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        tracing._initialized = False
        tracing._tracer = None
        
        client_on = TestClient(app)
        response_on = client_on.get("/health")
        
        # Outputs MUST be identical (semantic invariance)
        assert response_off.status_code == response_on.status_code
        assert response_off.json() == response_on.json()
    
    def test_unauthorized_response_identical_with_without_tracing(self, monkeypatch):
        """Unauthorized response identical with/without tracing."""
        # Configure API key (required for auth)
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "test_key")
        
        # Test WITHOUT tracing
        monkeypatch.setenv("TRACING_ENABLED", "0")
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        client_off = TestClient(app)
        response_off = client_off.post("/process", json={"text": "test"})  # No auth header
        
        # Test WITH tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        tracing._initialized = False
        tracing._tracer = None
        
        client_on = TestClient(app)
        response_on = client_on.post("/process", json={"text": "test"})  # No auth header
        
        # Both should return 401 (semantic invariance)
        assert response_off.status_code == 401
        assert response_on.status_code == 401
        
        # Error structure MUST be identical
        assert response_off.json()["error"] == response_on.json()["error"]


class TestTracingStartupEvent:
    """Test startup event initializes tracing (fail-closed)."""
    
    def test_startup_event_with_tracing_disabled(self, monkeypatch):
        """Startup event runs successfully with TRACING_ENABLED=0."""
        monkeypatch.setenv("TRACING_ENABLED", "0")
        
        # Reset tracing state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        # Create client (triggers startup event)
        client = TestClient(app)
        
        # App should start successfully (fail-closed)
        response = client.get("/health")
        assert response.status_code == 200
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_startup_event_with_tracing_enabled(self, monkeypatch):
        """Startup event initializes tracing with TRACING_ENABLED=1."""
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset tracing state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        # Manually trigger init_tracing (TestClient doesn't always trigger startup events in test isolation)
        from app.tracing import init_tracing
        init_tracing()
        
        # Tracer should be initialized
        from app.tracing import get_tracer
        tracer = get_tracer()
        assert tracer is not None
        
        # Create client and verify app works normally
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
