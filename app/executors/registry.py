"""Executor registry and implementations.

Provides executor instances by executor_id. All executors are deterministic.
Thread-safe access via threading.RLock().
"""
from __future__ import annotations

import threading
from typing import Any

from app.action_contracts import ActionRequest
from app.executors.base import Executor, ExecutorLimits



class TextProcessExecutorV1:
    """Simple text processing executor (deterministic, side-effect free).

    Uppercases text field from payload. Used for testing and demonstration.
    """

    def __init__(self):
        self.executor_id = "text_process_v1"
        self.version = "1.0.0"
        self.capabilities = ["TEXT_PROCESSING"]  # AG-03: declare capabilities
        self.limits = ExecutorLimits(
            timeout_ms=1000,
            max_payload_bytes=10_000,
            max_depth=10,
            max_list_items=100,
        )

    def execute(self, req: ActionRequest) -> Any:
        """Execute text processing (uppercase).

        Args:
            req: ActionRequest with payload containing "text" field

        Returns:
            dict with "processed" field containing uppercased text

        Raises:
            KeyError: if "text" field is missing
            ValueError: if text is not a string
        """
        text = req.payload.get("text")
        if text is None:
            raise KeyError("Missing required field: text")
        if not isinstance(text, str):
            raise ValueError("Field 'text' must be a string")

        processed = text.upper()
        return {"processed": processed, "length": len(processed)}


# Executor registry: executor_id -> Executor instance
_EXECUTORS: dict[str, Executor] = {
    "text_process_v1": TextProcessExecutorV1(),
}

# Thread-safe lock for executor registry access
_EXECUTORS_LOCK = threading.RLock()


class UnknownExecutorError(Exception):
    """Raised when executor_id is not found in registry."""
    pass


def get_executor(executor_id: str) -> Executor:
    """Retrieve executor by executor_id (thread-safe).

    Args:
        executor_id: unique identifier for executor

    Returns:
        Executor instance

    Raises:
        UnknownExecutorError: if executor_id not in registry
    """
    with _EXECUTORS_LOCK:
        if executor_id not in _EXECUTORS:
            raise UnknownExecutorError(f"Executor '{executor_id}' not found in registry")
        return _EXECUTORS[executor_id]
