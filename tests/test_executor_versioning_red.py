"""
TEST RED #3 — Executor Versioning
Tests for executor version validation and compatibility checks.

THESE TESTS MUST FAIL (AG-03 logic not implemented yet).
"""
import pytest
from unittest.mock import MagicMock
from app.agentic_pipeline import run_agentic_action


@pytest.fixture
def mock_action_requiring_min_version():
    """Create a mock ActionRegistry with action requiring min executor version."""
    registry = MagicMock()
    registry.actions = {
        "version_test_action": {
            "description": "Action requiring executor >= 1.1.0",
            "executor": "test_executor_versioning",
            "action_version": "1.0.0",
            "required_capabilities": [],
            "min_executor_version": "1.1.0",
        }
    }
    return registry


@pytest.fixture
def mock_executor_no_version():
    """Create a mock executor without version attribute."""
    executor = MagicMock()
    executor.executor_id = "test_executor_versioning"
    # version intentionally absent
    executor.capabilities = []
    executor.limits = MagicMock()
    executor.limits.max_payload_bytes = 10_000
    executor.limits.max_depth = 10
    executor.limits.max_list_items = 100
    executor.execute = MagicMock(return_value={"result": "ok"})
    return executor


@pytest.fixture
def mock_executor_old_version():
    """Create a mock executor with old version (incompatible)."""
    executor = MagicMock()
    executor.executor_id = "test_executor_versioning"
    executor.version = "1.0.0"  # Less than required 1.1.0
    executor.capabilities = []
    executor.limits = MagicMock()
    executor.limits.max_payload_bytes = 10_000
    executor.limits.max_depth = 10
    executor.limits.max_list_items = 100
    executor.execute = MagicMock(return_value={"result": "ok"})
    return executor


@pytest.fixture
def mock_executor_compatible_version():
    """Create a mock executor with compatible version."""
    executor = MagicMock()
    executor.executor_id = "test_executor_versioning"
    executor.version = "1.1.0"  # Equal to required 1.1.0
    executor.capabilities = []
    executor.limits = MagicMock()
    executor.limits.max_payload_bytes = 10_000
    executor.limits.max_depth = 10
    executor.limits.max_list_items = 100
    executor.execute = MagicMock(return_value={"result": "ok"})
    return executor


@pytest.fixture
def mock_executor_newer_version():
    """Create a mock executor with newer compatible version."""
    executor = MagicMock()
    executor.executor_id = "test_executor_versioning"
    executor.version = "1.2.0"  # Greater than required 1.1.0
    executor.capabilities = []
    executor.limits = MagicMock()
    executor.limits.max_payload_bytes = 10_000
    executor.limits.max_depth = 10
    executor.limits.max_list_items = 100
    executor.execute = MagicMock(return_value={"result": "ok"})
    return executor


class TestExecutorVersioningRed:
    """RED tests for executor version validation."""

    def test_executor_without_version_blocked(
        self, monkeypatch, mock_action_requiring_min_version, mock_executor_no_version
    ):
        """
        4.1 Executor MOCK without version MUST BLOCK.
        
        Action requires min_executor_version="1.1.0".
        Executor has no version attribute.
        Expected:
        - BLOCKED + "EXECUTOR_VERSION_MISSING"
        """
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_requiring_min_version
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "test_executor_versioning"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor_no_version
        )
        
        result, _ = run_agentic_action(
            action="version_test_action",
            payload={"data": "test"},
            trace_id="trace-execver-001"
        )
        
        assert result.status == "BLOCKED"
        assert "EXECUTOR_VERSION_MISSING" in result.reason_codes, \
            f"Expected EXECUTOR_VERSION_MISSING in {result.reason_codes}"

    def test_executor_with_incompatible_version_blocked(
        self, monkeypatch, mock_action_requiring_min_version, mock_executor_old_version
    ):
        """
        4.2 Executor with version incompatible (too old).
        
        Action requires min_executor_version="1.1.0".
        Executor.version="1.0.0" (lexicographically < "1.1.0").
        Expected:
        - BLOCKED + "EXECUTOR_VERSION_INCOMPATIBLE"
        """
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_requiring_min_version
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "test_executor_versioning"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor_old_version
        )
        
        result, _ = run_agentic_action(
            action="version_test_action",
            payload={"data": "test"},
            trace_id="trace-execver-002"
        )
        
        assert result.status == "BLOCKED"
        assert "EXECUTOR_VERSION_INCOMPATIBLE" in result.reason_codes, \
            f"Expected EXECUTOR_VERSION_INCOMPATIBLE in {result.reason_codes}"

    def test_executor_with_compatible_version_not_blocked(
        self, monkeypatch, mock_action_requiring_min_version, mock_executor_compatible_version
    ):
        """
        4.3a Executor with compatible version (equal).
        
        Action requires min_executor_version="1.1.0".
        Executor.version="1.1.0" (equal).
        Expected:
        - SHOULD NOT block for version
        """
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_requiring_min_version
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "test_executor_versioning"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor_compatible_version
        )
        
        result, _ = run_agentic_action(
            action="version_test_action",
            payload={"data": "test"},
            trace_id="trace-execver-003"
        )
        
        if result.status == "BLOCKED":
            assert "EXECUTOR_VERSION_MISSING" not in result.reason_codes
            assert "EXECUTOR_VERSION_INCOMPATIBLE" not in result.reason_codes

    def test_executor_with_newer_version_not_blocked(
        self, monkeypatch, mock_action_requiring_min_version, mock_executor_newer_version
    ):
        """
        4.3b Executor with compatible version (newer).
        
        Action requires min_executor_version="1.1.0".
        Executor.version="1.2.0" (greater).
        Expected:
        - SHOULD NOT block for version
        """
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_requiring_min_version
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "test_executor_versioning"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor_newer_version
        )
        
        result, _ = run_agentic_action(
            action="version_test_action",
            payload={"data": "test"},
            trace_id="trace-execver-004"
        )
        
        if result.status == "BLOCKED":
            assert "EXECUTOR_VERSION_MISSING" not in result.reason_codes
            assert "EXECUTOR_VERSION_INCOMPATIBLE" not in result.reason_codes
