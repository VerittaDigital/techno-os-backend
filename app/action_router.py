"""Action router mapping canonical actions to executor identifiers.

Static registry for deterministic routing. Changes to this mapping MUST be
tracked in governance (similar to gate profiles).
"""
from __future__ import annotations

# Static action-to-executor mapping
# Changes to this registry affect execution routing and MUST be audited.
ACTION_REGISTRY: dict[str, str] = {
    "process": "text_process_v1",
    "noop": "noop_executor_v1",
    "rule_evaluate": "rule_evaluator_v1",
    "llm_generate": "llm_executor_v1",
}


class UnknownActionError(Exception):
    """Raised when action is not found in ACTION_REGISTRY."""
    pass


def route_action(action: str) -> str:
    """Route an action to its executor_id deterministically.

    Args:
        action: canonical action identifier

    Returns:
        executor_id mapped to this action

    Raises:
        UnknownActionError: if action is not in ACTION_REGISTRY
    """
    if action not in ACTION_REGISTRY:
        raise UnknownActionError(f"Action '{action}' not found in registry")
    return ACTION_REGISTRY[action]
