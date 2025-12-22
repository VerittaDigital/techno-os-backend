"""
TEST RED #2 — Executor Capabilities
Tests for mandatory capability declaration and enforcement.

THESE TESTS MUST FAIL (AG-03 logic not implemented yet).
"""
import pytest
from unittest.mock import MagicMock
from app.agentic_pipeline import run_agentic_action
import uuid


@pytest.fixture
def mock_action_requiring_capabilities():
    """Create a mock ActionRegistry with action requiring capabilities."""
    registry = MagicMock()
    registry.actions = {
        "capability_test_action": {
            "description": "Action requiring TEXT_PROCESSING",
            "executor": "test_executor_captest",
            "action_version": "1.0.0",
            "required_capabilities": ["TEXT_PROCESSING"],
        }
    }
    return registry


@pytest.fixture
def mock_action_requiring_multiple_capabilities():
    """Create a mock ActionRegistry with action requiring multiple capabilities."""
    registry = MagicMock()
    registry.actions = {
        "multi_capability_action": {
            "description": "Action requiring TEXT and LOGGING",
            "executor": "test_executor_multi",
            "action_version": "1.0.0",
            "required_capabilities": ["LOGGING", "TEXT_PROCESSING"],  # ORDERED
        }
    }
    return registry


@pytest.fixture
def mock_executor_no_capabilities():
    """Create a mock executor without capabilities attribute."""
    executor = MagicMock()
    executor.executor_id = "test_executor_captest"
    executor.version = "1.0.0"
    # capabilities intentionally absent
    executor.limits = MagicMock()
    executor.limits.max_payload_bytes = 10_000
    executor.limits.max_depth = 10
    executor.limits.max_list_items = 100
    executor.execute = MagicMock(return_value={"result": "ok"})
    return executor


@pytest.fixture
def mock_executor_partial_capabilities():
    """Create a mock executor with only partial required capabilities."""
    executor = MagicMock()
    executor.executor_id = "test_executor_multi"
    executor.version = "1.0.0"
    executor.capabilities = ["TEXT_PROCESSING"]  # Missing LOGGING
    executor.limits = MagicMock()
    executor.limits.max_payload_bytes = 10_000
    executor.limits.max_depth = 10
    executor.limits.max_list_items = 100
    executor.execute = MagicMock(return_value={"result": "ok"})
    return executor


@pytest.fixture
def mock_executor_full_capabilities():
    """Create a mock executor with all required capabilities (and more)."""
    executor = MagicMock()
    executor.executor_id = "test_executor_multi"
    executor.version = "1.0.0"
    executor.capabilities = ["AUDIT_LOGGING", "LOGGING", "TEXT_PROCESSING"]  # ORDERED
    executor.limits = MagicMock()
    executor.limits.max_payload_bytes = 10_000
    executor.limits.max_depth = 10
    executor.limits.max_list_items = 100
    executor.execute = MagicMock(return_value={"result": "ok"})
    return executor


class TestExecutorCapabilitiesRed:
    """RED tests for executor capability validation."""

    def test_executor_without_capabilities_blocked(
        self, monkeypatch, mock_action_requiring_capabilities, mock_executor_no_capabilities
    ):
        """
        3.1 Executor declares capabilities=None/absent.
        
        Action requires ["TEXT_PROCESSING"].
        Expected:
        - BLOCKED + "EXECUTOR_CAPABILITY_MISSING"
        """
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_requiring_capabilities
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "test_executor_captest"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor_no_capabilities
        )
        
        result, _ = run_agentic_action(
            action="capability_test_action",
            payload={"data": "test"},
            trace_id=str(uuid.uuid4())
        )
        
        assert result.status == "BLOCKED"
        assert "EXECUTOR_CAPABILITY_MISSING" in result.reason_codes, \
            f"Expected EXECUTOR_CAPABILITY_MISSING in {result.reason_codes}"

    def test_executor_with_insufficient_capabilities_blocked(
        self, monkeypatch, mock_action_requiring_multiple_capabilities, 
        mock_executor_partial_capabilities
    ):
        """
        3.2 Executor with insufficient capabilities.
        
        Action requires ["TEXT_PROCESSING", "LOGGING"].
        Executor has ["TEXT_PROCESSING"] only.
        Expected:
        - BLOCKED + "EXECUTOR_CAPABILITY_MISMATCH"
        """
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_requiring_multiple_capabilities
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "test_executor_multi"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor_partial_capabilities
        )
        
        result, _ = run_agentic_action(
            action="multi_capability_action",
            payload={"data": "test"},
            trace_id=str(uuid.uuid4())
        )
        
        assert result.status == "BLOCKED"
        assert "EXECUTOR_CAPABILITY_MISMATCH" in result.reason_codes, \
            f"Expected EXECUTOR_CAPABILITY_MISMATCH in {result.reason_codes}"

    def test_executor_compatible_not_blocked_by_capabilities(
        self, monkeypatch, mock_action_requiring_multiple_capabilities,
        mock_executor_full_capabilities
    ):
        """
        3.3 Executor compatible (has all required capabilities and more).
        
        Action requires ["TEXT_PROCESSING", "LOGGING"].
        Executor has ["AUDIT_LOGGING", "LOGGING", "TEXT_PROCESSING"].
        Expected:
        - SHOULD NOT be BLOCKED for capability reason
        """
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_action_requiring_multiple_capabilities
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "test_executor_multi"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor_full_capabilities
        )
        
        result, _ = run_agentic_action(
            action="multi_capability_action",
            payload={"data": "test"},
            trace_id=str(uuid.uuid4())
        )
        
        # Should NOT block for capability reason
        if result.status == "BLOCKED":
            assert "EXECUTOR_CAPABILITY_MISSING" not in result.reason_codes
            assert "EXECUTOR_CAPABILITY_MISMATCH" not in result.reason_codes
