"""Action-profile matrix for governance enforcement.

This module defines which action_ids are permitted under each governance profile.

Design goals:
- Fail-closed: unknown actions must be denied elsewhere (gate), and the matrix is explicit.
- Thread-safe: reads/writes guarded by a re-entrant lock.
- Test-friendly: tests may override the global matrix via set_action_matrix()/reset_action_matrix().
"""

from __future__ import annotations

import threading
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ActionMatrix(BaseModel):
    """Matrix defining which actions are allowed in which profiles.

    Fields:
    - profile: profile identifier (e.g., "default", "restricted")
    - allowed_actions: list of action_ids permitted in this profile
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    profile: str
    allowed_actions: list[str]


_global_matrix: Optional[ActionMatrix] = None
_global_matrix_lock = threading.RLock()


def get_action_matrix() -> ActionMatrix:
    """Return the canonical action-profile matrix.

    If a matrix was set via set_action_matrix(), it is returned.
    Otherwise, returns the built-in default matrix (canonical runtime baseline).

    Thread-safe: guarded by _global_matrix_lock for consistent read.
    """
    with _global_matrix_lock:
        if _global_matrix is not None:
            return _global_matrix

        return ActionMatrix(
            profile="default",
            allowed_actions=[
                "process",
                "preferences.delete",
                "preferences.get",
                "preferences.put",
                "llm_generate",
            ],
        )

def is_action_allowed_in_profile(
    action: str,
    profile: str,
    matrix: Optional[ActionMatrix] = None,
) -> bool:
    """Return True if `action` is allowed in the given profile.

    Fail-closed: unknown actions are treated as not allowed.
    If `matrix` is not provided, uses the current global/canonical matrix.
    """
    if matrix is None:
        matrix = get_action_matrix()

    if matrix.profile != profile:
        return False

    return action in matrix.allowed_actions
def set_action_matrix(matrix: ActionMatrix) -> None:
    """Override the global action matrix (primarily for tests)."""
    global _global_matrix
    with _global_matrix_lock:
        _global_matrix = matrix


def reset_action_matrix() -> None:
    """Reset the global override so get_action_matrix() returns the canonical baseline."""
    global _global_matrix
    with _global_matrix_lock:
        _global_matrix = None
