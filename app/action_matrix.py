"""Action-profile matrix for governance enforcement."""
from __future__ import annotations

import os
import threading
from typing import List
from pydantic import BaseModel, ConfigDict


class ActionMatrix(BaseModel):
    """Matrix defining which actions are allowed in which profiles.
    
    Fields:
    - profile: profile identifier (e.g., "default", "restricted")
    - allowed_actions: list of action_ids permitted in this profile
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    profile: str
    allowed_actions: List[str]


_global_matrix = None
_global_matrix_lock = threading.RLock()


def get_action_matrix() -> ActionMatrix:
    """Return the canonical action-profile matrix.
    
    Defines which actions can be executed within each governance profile.
    In testing, allows dynamic addition of test actions via set_action_matrix().
    
    Thread-safe: acquires _global_matrix_lock for consistent read.
    """
    global _global_matrix
    
    with _global_matrix_lock:
        if _global_matrix is not None:
            return _global_matrix
        
        return ActionMatrix(
            profile="default",
            allowed_actions=["process"],
        )


def set_action_matrix(matrix: ActionMatrix) -> None:
    """Override action matrix (for testing only).
    
    This is used in tests to temporarily add test actions to the allowed list.
    
    Thread-safe: acquires _global_matrix_lock for exclusive write.
    """
    global _global_matrix
    
    with _global_matrix_lock:
        _global_matrix = matrix


def reset_action_matrix() -> None:
    """Reset action matrix to default (for testing cleanup).
    
    Thread-safe: acquires _global_matrix_lock for exclusive write.
    """
    global _global_matrix
    
    with _global_matrix_lock:
        _global_matrix = None


def is_action_allowed_in_profile(
    action: str,
    profile: str,
    matrix: ActionMatrix,
) -> bool:
    """Check if action is allowed in profile according to matrix.
    
    Args:
        action: action_id to check
        profile: profile_id context
        matrix: action-profile matrix
    
    Returns:
        True if action is in matrix.allowed_actions for this profile, False otherwise
    """
    if matrix.profile != profile:
        return False
    return action in matrix.allowed_actions
