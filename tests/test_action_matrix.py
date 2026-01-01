"""Tests for action profile matrix."""
from app.action_matrix import ActionMatrix, get_action_matrix, is_action_allowed_in_profile


class TestActionMatrixProfile:
    """Test action-profile matrix for governance."""

    def test_matrix_created(self):
        """Action matrix must exist and be creatable."""
        matrix = get_action_matrix()
        assert matrix is not None
        assert isinstance(matrix, ActionMatrix)

    def test_matrix_has_profile_field(self):
        """ActionMatrix must have profile field."""
        matrix = get_action_matrix()
        assert hasattr(matrix, "profile")
        assert isinstance(matrix.profile, str)

    def test_matrix_has_allowed_actions_field(self):
        """ActionMatrix must have allowed_actions field."""
        matrix = get_action_matrix()
        assert hasattr(matrix, "allowed_actions")
        assert isinstance(matrix.allowed_actions, (list, dict))

    def test_process_action_allowed_in_default_profile(self):
        """'process' action must be allowed in default profile."""
        matrix = get_action_matrix()
        is_allowed = is_action_allowed_in_profile("process", matrix.profile, matrix)
        assert is_allowed is True

    def test_unknown_action_not_allowed(self):
        """Unknown action must not be allowed."""
        matrix = get_action_matrix()
        is_allowed = is_action_allowed_in_profile("unknown_action", matrix.profile, matrix)
        assert is_allowed is False


class TestActionMatrixMismatch:
    """Test profile-action mismatch detection."""

    def test_mismatch_detected_when_action_not_in_profile(self):
        """Mismatch must be detected when action not in profile allowed list."""
        matrix = ActionMatrix(profile="restricted", allowed_actions=["other"])
        is_allowed = is_action_allowed_in_profile("process", "restricted", matrix)
        assert is_allowed is False

    def test_allowed_action_returns_true(self):
        """Allowed action must return True."""
        matrix = ActionMatrix(profile="default", allowed_actions=["process", "execute"])
        is_allowed = is_action_allowed_in_profile("process", "default", matrix)
        assert is_allowed is True
