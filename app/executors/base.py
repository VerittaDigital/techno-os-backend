"""Executor base protocol and contracts.

All executors MUST be deterministic and side-effect free.
Executors MAY raise exceptions; the pipeline maps them to FAILED status.
"""
from __future__ import annotations

from typing import Any, List, Optional, Protocol

from app.action_contracts import ActionRequest


class ExecutorLimits:
    """Immutable limits configuration for an executor.

    - timeout_ms: simulated timeout (not enforced in AG-01, future: async)
    - max_payload_bytes: max size of canonical JSON payload
    - max_depth: max nesting depth of payload structures
    - max_list_items: max items in any list within payload
    """

    def __init__(
        self,
        timeout_ms: int,
        max_payload_bytes: int,
        max_depth: int,
        max_list_items: int,
    ):
        self.timeout_ms = timeout_ms
        self.max_payload_bytes = max_payload_bytes
        self.max_depth = max_depth
        self.max_list_items = max_list_items


class Executor(Protocol):
    """Protocol defining the executor contract.

    All executors MUST:
    - Have immutable executor_id and version
    - Define limits for safety checks
    - Implement deterministic execute() method
    - Be side-effect free (no I/O, no mutation)
    
    AG-03 addition:
    - capabilities: Optional[List[str]] for capability declaration
    """

    executor_id: str
    version: str
    limits: ExecutorLimits
    capabilities: Optional[List[str]]  # AG-03: optional, for backward compat

    def execute(self, req: ActionRequest) -> Any:
        """Execute the action deterministically.

        Args:
            req: ActionRequest with action, payload, trace_id

        Returns:
            Any deterministic output (preferably JSON-serializable)

        Raises:
            TimeoutError: if execution exceeds simulated timeout (for tests)
            Any other exception: mapped to FAILED by pipeline

        """
        ...
