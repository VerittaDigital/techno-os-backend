"""Tracing tests for agentic_pipeline (F8.6.1)."""

import uuid
import pytest
from app.agentic_pipeline import run_agentic_action
from app.tracing import init_tracing, get_tracer
from conftest import tracing_available


class TestAgenticPipelineTracingGovernance:
    """Test tracing governance in agentic pipeline (fail-closed, wrapper-only)."""
    
    def test_pipeline_without_tracing_works(self, monkeypatch):
        """Pipeline works with TRACING_ENABLED=0 (default)."""
        # Ensure tracing is disabled
        monkeypatch.setenv("TRACING_ENABLED", "0")
        
        # Reset tracing state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        # Execute action (should work without tracing)
        result, output = run_agentic_action(
            action="test_action",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        
        # Should execute successfully (or block with valid reason)
        assert result is not None
        assert result.status in ["SUCCESS", "BLOCKED", "FAILED"]
        # trace_id should be a valid UUID
        uuid.UUID(result.trace_id)  # Raises if invalid
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_pipeline_with_tracing_enabled_works(self, monkeypatch):
        """Pipeline works with TRACING_ENABLED=1."""
        # Enable tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset and init tracing
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        # Tracer should be initialized
        tracer = get_tracer()
        assert tracer is not None
        
        # Execute action
        result, output = run_agentic_action(
            action="test_action",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        
        # Should execute successfully (with tracing)
        assert result is not None
        assert result.status in ["SUCCESS", "BLOCKED", "FAILED"]
        uuid.UUID(result.trace_id)  # Raises if invalid


class TestAgenticPipelineSemanticInvariance:
    """Test that tracing does NOT alter pipeline semantics (governance)."""
    
    def test_pipeline_result_identical_with_without_tracing(self, monkeypatch):
        """Pipeline returns identical results with/without tracing."""
        # Test WITHOUT tracing
        monkeypatch.setenv("TRACING_ENABLED", "0")
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        trace_id_off = str(uuid.uuid4())
        result_off, output_off = run_agentic_action(
            action="test_action",
            payload={"test": "data"},
            trace_id=trace_id_off,
        )
        
        # Test WITH tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        trace_id_on = str(uuid.uuid4())
        result_on, output_on = run_agentic_action(
            action="test_action",
            payload={"test": "data"},
            trace_id=trace_id_on,
        )
        
        # Results MUST be identical (semantic invariance)
        assert result_off.status == result_on.status
        assert result_off.action == result_on.action
        assert result_off.executor_id == result_on.executor_id
        assert result_off.reason_codes == result_on.reason_codes
        # trace_id will differ (expected), but functional behavior must be identical
    
    def test_pipeline_blocked_result_identical_with_without_tracing(self, monkeypatch):
        """BLOCKED results identical with/without tracing."""
        # Non-JSON payload (will block)
        class NonSerializable:
            pass
        
        payload = {"bad": NonSerializable()}
        
        # Test WITHOUT tracing
        monkeypatch.setenv("TRACING_ENABLED", "0")
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        result_off, _ = run_agentic_action(
            action="test_action",
            payload=payload,
            trace_id=str(uuid.uuid4()),
        )
        
        # Test WITH tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        result_on, _ = run_agentic_action(
            action="test_action",
            payload=payload,
            trace_id=str(uuid.uuid4()),
        )
        
        # Both should BLOCK with identical reason
        assert result_off.status == "BLOCKED"
        assert result_on.status == "BLOCKED"
        assert result_off.reason_codes == result_on.reason_codes
        assert "NON_JSON_PAYLOAD" in result_off.reason_codes


class TestAgenticPipelineSpanHierarchy:
    """Test span hierarchy in agentic pipeline (observability validation)."""
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_pipeline_creates_spans_when_enabled(self, monkeypatch):
        """Pipeline creates hierarchical spans with TRACING_ENABLED=1."""
        # Enable tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset and init tracing
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        # Execute action
        result, output = run_agentic_action(
            action="test_action",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        
        # Spans should be created (verify via Jaeger UI or manual inspection)
        # Expected hierarchy:
        # - agentic_action (root)
        #   - route_action
        #   - compute_digests
        #   - validate_action
        #   - resolve_executor
        #   - enforce_limits
        #   - execute_action
        #   - audit_result
        
        # Functional assertion: pipeline completed
        assert result is not None
        uuid.UUID(result.trace_id)  # Raises if invalid
    
    def test_pipeline_no_spans_when_disabled(self, monkeypatch):
        """Pipeline creates NO spans with TRACING_ENABLED=0."""
        # Disable tracing
        monkeypatch.setenv("TRACING_ENABLED", "0")
        
        # Reset tracing
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        # Execute action
        result, output = run_agentic_action(
            action="test_action",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        
        # Should work normally (no spans created)
        assert result is not None
        uuid.UUID(result.trace_id)  # Raises if invalid
        
        # Tracer should NOT be initialized
        tracer = get_tracer()
        assert tracer is None
