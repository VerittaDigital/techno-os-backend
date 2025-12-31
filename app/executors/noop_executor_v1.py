"""Noop executor v1 — minimal real executor for A3 testing.

Implements deterministic, side-effect-free executor that simulates
successful execution with no output. Used for testing pipeline integration,
auditability, and fail-closed semantics without business logic.

AG-03 compatible: declares capabilities and version.
"""
from __future__ import annotations

from typing import Any

from app.action_contracts import ActionRequest
from app.executors.base import ExecutorLimits
from app.tracing import observed_span


class NoopExecutorV1:
    """Minimal executor that simulates successful execution.
    
    - executor_id: "noop_executor_v1"
    - version: "1.0.0" (semver)
    - capabilities: [] (no special capabilities required)
    - behavior: Always returns None (no output)
    - status: Always SUCCESS
    - no side effects: no I/O, no mutation
    """

    def __init__(self):
        self.executor_id = "noop_executor_v1"
        self.version = "1.0.0"
        self.capabilities = []  # No special capabilities
        self.limits = ExecutorLimits(
            timeout_ms=1000,
            max_payload_bytes=10_000,
            max_depth=10,
            max_list_items=100,
        )

    def execute(self, req: ActionRequest) -> Any:
        """Execute noop action (no-operation).

        Args:
            req: ActionRequest with action, payload, trace_id

        Returns:
            None (noop has no output)

        Raises:
            Nothing — always succeeds deterministically
        """
        # F8.6.1 FASE 3: Instrument executor at boundaries (fail-closed, wrapper-only)
        with observed_span(
            f"executor.{self.executor_id}",
            attributes={
                "executor_name": self.executor_id,
                "action": getattr(req, "action", "unknown"),
                "trace_id": getattr(req, "trace_id", "unknown"),
            }
        ):
            # Consume request to verify it was passed correctly
            # (use for validation but produce no side effects)
            _ = (req.action, req.payload, req.trace_id)
            
            # Return None to indicate no output
            return None
