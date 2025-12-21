"""Pytest configuration and fixtures."""
import pytest
from app.action_matrix import reset_action_matrix


@pytest.fixture(autouse=True)
def reset_action_matrix_after_test():
    """Reset action matrix after each test."""
    yield
    reset_action_matrix()
