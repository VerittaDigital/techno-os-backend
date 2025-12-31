"""
OpenTelemetry tracing initialization (F8.6.1).

GOVERNANCE:
- Manual instrumentation only (no auto-instrumentation)
- Fail-closed: If tracing fails, app continues without tracing
- Privacy: No PII in span attributes
- TRACING_ENABLED=0 por padrão (env var)
"""

import os
from typing import Optional
from contextlib import nullcontext
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

_tracer: Optional[trace.Tracer] = None
_initialized = False


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled via env var (fail-closed)."""
    return os.getenv("TRACING_ENABLED", "0") == "1"


def init_tracing(service_name: str = "techno-os-backend") -> Optional[trace.Tracer]:
    """
    Initialize OpenTelemetry tracing (fail-closed).
    
    Returns None if:
    - TRACING_ENABLED=0 (default)
    - Initialization fails
    
    App continues normally in both cases.
    """
    global _tracer, _initialized
    
    if _initialized:
        return _tracer
    
    # Check env var FIRST (fail-closed)
    if not is_tracing_enabled():
        print("ℹ️ Tracing disabled (TRACING_ENABLED=0)")
        _tracer = None
        _initialized = True
        return None
    
    try:
        # Create resource with service name
        resource = Resource.create({"service.name": service_name})
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Create Jaeger exporter (agent on localhost:6831) - isolated under TRACING_ENABLED
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )
        
        # Add span processor (batch mode for performance)
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        
        # Set as global tracer provider
        trace.set_tracer_provider(provider)
        
        # Get tracer instance
        _tracer = trace.get_tracer(__name__)
        _initialized = True
        
        print("✅ Tracing initialized (Jaeger at localhost:6831)")
        return _tracer
    
    except Exception as e:
        # Fail-closed: If tracing init fails, continue without tracing
        print(f"⚠️ Tracing initialization failed (app continues): {e}")
        _tracer = None
        _initialized = True  # Mark as attempted to avoid retry loops
        return None


def get_tracer() -> Optional[trace.Tracer]:
    """Get tracer instance (None if tracing not initialized)."""
    return _tracer


def observed_span(name: str, attributes: dict = None):
    """
    Context manager for creating observed spans (WRAPPER-ONLY, fail-closed).
    
    GOVERNANCE:
    - This is the ONLY way to create spans (wrapper-only rule)
    - If tracing not enabled/initialized, returns no-op context
    - Never throws exceptions (fail-closed)
    - Does NOT alter function semantics
    
    Usage:
        with observed_span("operation_name", {"key": "value"}):
            # Your code here (semantics unchanged)
            result = do_work()
        return result
    """
    # Fail-closed: If tracing not available, no-op
    tracer = get_tracer()
    if tracer is None:
        return nullcontext()
    
    try:
        # Real span
        span = tracer.start_as_current_span(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        return span
    except Exception as e:
        # Fail-closed: If span creation fails, no-op
        print(f"⚠️ Span creation failed (continuing): {e}")
        return nullcontext()
