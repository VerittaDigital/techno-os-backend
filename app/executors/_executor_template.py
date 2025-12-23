"""Executor template (P3+ sealed scaffold).

This file is a normative scaffold for implementing real executors (A4+).
It intentionally contains comments that map directly to `EXECUTOR_CONTRACT.md`.

Guidelines:
- Start by copying this file into `your_executor.py` and update identifiers.
- Keep this file named with a leading underscore so it is not automatically registered.
- Do NOT import this template into runtime registries.
"""
from __future__ import annotations

from typing import Any, Optional
from app.action_contracts import ActionRequest
from app.executors.base import ExecutorLimits


class TemplateExecutor:
    """Minimal executor scaffold.

    Replace `TemplateExecutor` and attributes with real values when implementing.
    Follow the contract: deterministic, side-effect free, no I/O, no env reads.
    """

    def __init__(self):
        # Update these fields for your executor
        self.executor_id: str = "template_executor_v1"  # lowercase_with_underscores
        self.version: str = "0.1.0"  # semver X.Y.Z
        self.capabilities: list[str] = []  # e.g. ["TEXT_PROCESSING"]
        self.limits = ExecutorLimits(
            timeout_ms=1000,
            max_payload_bytes=10_000,
            max_depth=10,
            max_list_items=100,
        )

    def execute(self, req: ActionRequest) -> Optional[Any]:
        """Execute deterministically and side-effect free.

        Guidelines for implementation:
        - Do not perform I/O, network, or DB access.
        - Do not read environment variables.
        - Keep computations pure and deterministic.
        - If no meaningful output, return `None` explicitly.

        Args:
            req: ActionRequest with `action`, `payload`, `trace_id`.

        Returns:
            Any JSON-serializable object, or `None` when no output.
        """
        # Example: simple, deterministic transformation (pure computation only)
        # payload = req.payload  # Use payload as needed

        # Validate expected fields in payload explicitly, raise if invalid
        # (pipeline will map exceptions to FAILED)
        # if "required_field" not in payload:
        #     raise KeyError("Missing required_field")

        # Implement deterministic logic here and return result or None
        # result = {"ok": True}  # example deterministic output

        return None
