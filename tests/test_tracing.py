"""Tests for OpenTelemetry tracing module (F8.6.1)."""

import pytest
from app.tracing import init_tracing, get_tracer, observed_span, is_tracing_enabled
from conftest import tracing_available


class TestTracingGovernance:
    """Test tracing governance (fail-closed, env var)."""
    
    def test_tracing_disabled_by_default(self, monkeypatch):
        """TRACING_ENABLED=0 by default (fail-closed)."""
        # Reset state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        # Default behavior (no env var set)
        monkeypatch.delenv("TRACING_ENABLED", raising=False)
        
        assert not is_tracing_enabled()
        tracer = init_tracing()
        assert tracer is None
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_tracing_enabled_via_env(self, monkeypatch):
        """TRACING_ENABLED=1 enables tracing."""
        # Reset state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        assert is_tracing_enabled()
        tracer = init_tracing()
        assert tracer is not None


class TestTracingInitialization:
    """Test tracing initialization (fail-closed)."""
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_init_tracing_idempotent(self, monkeypatch):
        """Calling init_tracing() multiple times is safe."""
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        tracer1 = init_tracing()
        tracer2 = init_tracing()
        assert tracer1 is tracer2
    
    def test_get_tracer_before_init(self):
        """get_tracer() returns None before initialization."""
        # Reset state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        assert get_tracer() is None


class TestObservedSpan:
    """Test observed_span wrapper (wrapper-only, fail-closed)."""
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_observed_span_with_tracer(self, monkeypatch):
        """observed_span() returns context manager when tracer available."""
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset and init
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        # Should not raise
        with observed_span("test_span", attributes={"test": "value"}):
            pass
    
    def test_observed_span_without_tracer(self, monkeypatch):
        """observed_span() returns no-op context when tracer unavailable."""
        monkeypatch.setenv("TRACING_ENABLED", "0")
        
        # Reset
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        # Should not raise exception (fail-closed)
        with observed_span("test_span"):
            pass
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_observed_span_preserves_semantics(self, monkeypatch):
        """observed_span() does NOT alter function semantics."""
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset and init
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        # Test that return value is preserved
        def dummy_function():
            with observed_span("dummy_op"):
                return 42
        
        result = dummy_function()
        assert result == 42  # Semantics preserved
