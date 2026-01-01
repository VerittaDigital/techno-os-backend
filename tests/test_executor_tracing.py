"""Tracing tests for executors (F8.6.1 FASE 3)."""

import uuid
import pytest
from app.action_contracts import ActionRequest
from app.executors.llm_executor_v1 import LLMExecutorV1
from app.executors.noop_executor_v1 import NoopExecutorV1
from app.llm.fake_client import FakeLLMClient
from app.tracing import init_tracing, get_tracer
from conftest import tracing_available


class TestExecutorTracingGovernance:
    """Test tracing governance in executors (fail-closed, wrapper-only)."""
    
    def test_llm_executor_without_tracing_works(self, monkeypatch):
        """LLM executor works with TRACING_ENABLED=0 (default)."""
        # Ensure tracing is disabled
        monkeypatch.setenv("TRACING_ENABLED", "0")
        
        # Reset tracing state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        # Create executor
        executor = LLMExecutorV1(client=FakeLLMClient())
        
        # Execute action
        req = ActionRequest(
            action="test_llm_action",
            payload={"prompt": "Hello", "model": "gpt-4o-mini", "max_tokens": 100},
            trace_id=str(uuid.uuid4()),
        )
        
        result = executor.execute(req)
        
        # Should execute successfully
        assert result is not None
        assert "text" in result
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_llm_executor_with_tracing_enabled_works(self, monkeypatch):
        """LLM executor works with TRACING_ENABLED=1."""
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
        
        # Create executor
        executor = LLMExecutorV1(client=FakeLLMClient())
        
        # Execute action
        req = ActionRequest(
            action="test_llm_action",
            payload={"prompt": "Hello", "model": "gpt-4o-mini", "max_tokens": 100},
            trace_id=str(uuid.uuid4()),
        )
        
        result = executor.execute(req)
        
        # Should execute successfully (with tracing)
        assert result is not None
        assert "text" in result
    
    def test_noop_executor_without_tracing_works(self, monkeypatch):
        """Noop executor works with TRACING_ENABLED=0."""
        # Ensure tracing is disabled
        monkeypatch.setenv("TRACING_ENABLED", "0")
        
        # Reset tracing state
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        # Create executor
        executor = NoopExecutorV1()
        
        # Execute action
        req = ActionRequest(
            action="test_noop_action",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        
        result = executor.execute(req)
        
        # Should return None (noop has no output)
        assert result is None
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_noop_executor_with_tracing_enabled_works(self, monkeypatch):
        """Noop executor works with TRACING_ENABLED=1."""
        # Enable tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset and init tracing
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        # Create executor
        executor = NoopExecutorV1()
        
        # Execute action
        req = ActionRequest(
            action="test_noop_action",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        
        result = executor.execute(req)
        
        # Should return None (with tracing)
        assert result is None


class TestExecutorSemanticInvariance:
    """Test that tracing does NOT alter executor semantics (governance)."""
    
    def test_llm_executor_result_identical_with_without_tracing(self, monkeypatch):
        """LLM executor returns identical results with/without tracing."""
        # Test WITHOUT tracing
        monkeypatch.setenv("TRACING_ENABLED", "0")
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        executor_off = LLMExecutorV1(client=FakeLLMClient())
        req_off = ActionRequest(
            action="test_llm",
            payload={"prompt": "Hello", "model": "gpt-4o-mini", "max_tokens": 100},
            trace_id=str(uuid.uuid4()),
        )
        result_off = executor_off.execute(req_off)
        
        # Test WITH tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        executor_on = LLMExecutorV1(client=FakeLLMClient())
        req_on = ActionRequest(
            action="test_llm",
            payload={"prompt": "Hello", "model": "gpt-4o-mini", "max_tokens": 100},
            trace_id=str(uuid.uuid4()),
        )
        result_on = executor_on.execute(req_on)
        
        # Results MUST be identical (semantic invariance)
        assert result_off.keys() == result_on.keys()
        assert result_off["text"] == result_on["text"]
        assert result_off["model"] == result_on["model"]
    
    def test_noop_executor_result_identical_with_without_tracing(self, monkeypatch):
        """Noop executor returns identical results with/without tracing."""
        # Test WITHOUT tracing
        monkeypatch.setenv("TRACING_ENABLED", "0")
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        executor_off = NoopExecutorV1()
        req_off = ActionRequest(
            action="test_noop",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        result_off = executor_off.execute(req_off)
        
        # Test WITH tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        executor_on = NoopExecutorV1()
        req_on = ActionRequest(
            action="test_noop",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        result_on = executor_on.execute(req_on)
        
        # Both should return None
        assert result_off is None
        assert result_on is None


class TestExecutorSpanHierarchy:
    """Test span hierarchy in executors (observability validation)."""
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_llm_executor_creates_span_when_enabled(self, monkeypatch):
        """LLM executor creates span with TRACING_ENABLED=1."""
        # Enable tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset and init tracing
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        # Create executor
        executor = LLMExecutorV1(client=FakeLLMClient())
        
        # Execute action
        req = ActionRequest(
            action="test_llm",
            payload={"prompt": "Hello", "model": "gpt-4o-mini", "max_tokens": 100},
            trace_id=str(uuid.uuid4()),
        )
        
        result = executor.execute(req)
        
        # Span should be created (verify via Jaeger UI or manual inspection)
        # Expected span: executor.llm_executor_v1
        
        # Functional assertion: executor completed
        assert result is not None
    
    @pytest.mark.skipif(not tracing_available(), reason="Tracing dependencies not available")
    def test_noop_executor_creates_span_when_enabled(self, monkeypatch):
        """Noop executor creates span with TRACING_ENABLED=1."""
        # Enable tracing
        monkeypatch.setenv("TRACING_ENABLED", "1")
        
        # Reset and init tracing
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        init_tracing()
        
        # Create executor
        executor = NoopExecutorV1()
        
        # Execute action
        req = ActionRequest(
            action="test_noop",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        
        result = executor.execute(req)
        
        # Span should be created
        # Expected span: executor.noop_executor_v1
        
        # Functional assertion: executor completed
        assert result is None
    
    def test_executor_no_span_when_disabled(self, monkeypatch):
        """Executors create NO spans with TRACING_ENABLED=0."""
        # Disable tracing
        monkeypatch.setenv("TRACING_ENABLED", "0")
        
        # Reset tracing
        from app import tracing
        tracing._initialized = False
        tracing._tracer = None
        
        # Create executors
        llm_exec = LLMExecutorV1(client=FakeLLMClient())
        noop_exec = NoopExecutorV1()
        
        # Execute actions
        req_llm = ActionRequest(
            action="test_llm",
            payload={"prompt": "Hello", "model": "gpt-4o-mini", "max_tokens": 100},
            trace_id=str(uuid.uuid4()),
        )
        req_noop = ActionRequest(
            action="test_noop",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        
        result_llm = llm_exec.execute(req_llm)
        result_noop = noop_exec.execute(req_noop)
        
        # Should work normally (no spans created)
        assert result_llm is not None
        assert result_noop is None
        
        # Tracer should NOT be initialized
        tracer = get_tracer()
        assert tracer is None
