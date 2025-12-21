"""
TEST RED #1 — Action Versioning
Tests for mandatory version field in ActionRegistry.

THESE TESTS MUST FAIL (AG-03 logic not implemented yet).
"""
import pytest
from unittest.mock import MagicMock
from app.agentic_pipeline import run_agentic_action


@pytest.fixture
def mock_action_registry_no_version():
    """Create a mock ActionRegistry with action missing version."""
    registry = MagicMock()
    registry.actions = {
        "new_action": {
            "description": "Test action without version",
            "executor": "test_executor_v1",
            # action_version intentionally absent
        }
    }
    return registry


@pytest.fixture
def mock_action_registry_invalid_version():
    """Create a mock ActionRegistry with invalid version format."""
    registry = MagicMock()
    registry.actions = {
        "bad_version_action": {
            "description": "Action with invalid version",
            "executor": "test_executor_v1",
            "action_version": "v1",  # Invalid: should be 1.0.0
        }
    }
    return registry


@pytest.fixture
def mock_action_registry_valid_version():
    """Create a mock ActionRegistry with valid semver version."""
    registry = MagicMock()
    registry.actions = {
        "valid_version_action": {
            "description": "Action with valid version",
            "executor": "test_executor_v1",
            "action_version": "1.0.0",
        }
    }
    return registry


@pytest.fixture
def mock_executor_valid():
    """Create a mock executor with valid version."""
    executor = MagicMock()
    executor.executor_id = "test_executor_v1"
    executor.version = "1.0.0"
    executor.capabilities = ["TEXT_PROCESSING"]
    executor.limits = MagicMock()
    executor.limits.max_payload_bytes = 10_000
    executor.limits.max_depth = 10
    executor.limits.max_list_items = 100
    executor.execute = MagicMock(return_value={"result": "ok"})
    return executor


class TestActionVersioningRed:
    """RED tests for action version validation."""

    def test_action_without_version_blocked(self, monkeypatch, mock_action_registry_no_version):
        """
        2.1 Action new without explicit version MUST BLOCK.
        
        ActionRegistry registers action="new_action" without action_version.
        Expected:
        - ActionResult.status == "BLOCKED"
        - reason_codes contains "ACTION_VERSION_MISSING"
        """
        # Mock get_action_registry to return our no-version registry
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_registry_no_version
        )
        
        result, _ = run_agentic_action(
            action="new_action",
            payload={"data": "test"},
            trace_id="trace-version-001"
        )
        
        # MUST fail on version check
        assert result.status == "BLOCKED", f"Expected BLOCKED but got {result.status}"
        assert "ACTION_VERSION_MISSING" in result.reason_codes, \
            f"Expected ACTION_VERSION_MISSING in {result.reason_codes}"

    def test_action_with_invalid_version_blocked(self, monkeypatch, mock_action_registry_invalid_version):
        """
        2.2 Action new with invalid version format MUST BLOCK.
        
        action_version = "v1" (invalid, must be X.Y.Z).
        Expected:
        - BLOCKED + "ACTION_VERSION_INVALID"
        """
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_registry_invalid_version
        )
        
        result, _ = run_agentic_action(
            action="bad_version_action",
            payload={"data": "test"},
            trace_id="trace-version-002"
        )
        
        assert result.status == "BLOCKED"
        assert "ACTION_VERSION_INVALID" in result.reason_codes, \
            f"Expected ACTION_VERSION_INVALID in {result.reason_codes}"

    def test_action_with_valid_version_not_blocked_by_version(
        self, monkeypatch, mock_action_registry_valid_version, mock_executor_valid
    ):
        """
        2.3 Action new with valid version MUST NOT BLOCK due to version.
        
        action_version = "1.0.0" (valid semver).
        Expected:
        - SHOULD NOT be BLOCKED for version (may fail for other reasons)
        """
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_registry_valid_version
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "test_executor_v1"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor_valid
        )
        
        result, _ = run_agentic_action(
            action="valid_version_action",
            payload={"data": "test"},
            trace_id="trace-version-003"
        )
        
        # Should NOT block for version reason
        if result.status == "BLOCKED":
            # If blocked, it should NOT be because of version
            assert "ACTION_VERSION_MISSING" not in result.reason_codes
            assert "ACTION_VERSION_INVALID" not in result.reason_codes
