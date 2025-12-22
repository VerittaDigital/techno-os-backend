"""
Tests for P2-EXEC-TIMEOUT: executor timeout enforcement (fail-safe).

Verify:
- Executor timeout triggers EXECUTOR_TIMEOUT reason code
- Fast executors complete without timeout
- Timeout is configurable via VERITTA_EXECUTOR_TIMEOUT_S
"""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from app.action_contracts import ActionRequest, ActionResult
from app.agentic_pipeline import run_agentic_action


class SlowExecutor:
    """Mock executor that sleeps longer than timeout."""
    
    executor_id = "test.slow"
    executor_version = "1.0.0"
    version = "1.0.0"  # Add version attribute for validation
    capabilities = []
    
    def __init__(self):
        self.limits = MagicMock()
        self.limits.max_payload_bytes = 1_000_000
        self.limits.max_depth = 10
        self.limits.max_list_items = 100
    
    def execute(self, action_req: ActionRequest):
        # Sleep longer than expected timeout
        time.sleep(1.0)
        return {"result": "too_slow"}


class FastExecutor:
    """Mock executor that completes quickly."""
    
    executor_id = "test.fast"
    executor_version = "1.0.0"
    version = "1.0.0"  # Add version attribute for validation
    capabilities = []
    
    def __init__(self):
        self.limits = MagicMock()
        self.limits.max_payload_bytes = 1_000_000
        self.limits.max_depth = 10
        self.limits.max_list_items = 100
    
    def execute(self, action_req: ActionRequest):
        # Complete immediately
        return {"result": "fast"}


class TestExecutorTimeout:
    """Test suite for P2-EXEC-TIMEOUT (executor timeout enforcement)."""

    def test_executor_timeout_blocks(self, monkeypatch):
        """
        Executor that exceeds timeout produces EXECUTOR_TIMEOUT.
        
        Scenario:
        - Mock executor that sleeps 1.0s
        - Set VERITTA_EXECUTOR_TIMEOUT_S to 0.05 (50ms)
        - Execute action via run_agentic_action
        - Expected: Returns with BLOCKED status and EXECUTOR_TIMEOUT reason code
        
        Note: With shutdown(wait=False), call returns quickly without waiting for orphan thread.
        """
        # Set very short timeout
        monkeypatch.setenv("VERITTA_EXECUTOR_TIMEOUT_S", "0.05")
        
        # Mock executor resolution to return slow executor
        slow_executor = SlowExecutor()
        
        # Mock action registry to provide valid action metadata
        mock_registry_obj = Mock()
        mock_registry_obj.actions = {
            "test_action": {
                "action_version": "1.0.0",
                "executor_id": "test.slow",
                "min_executor_version": "1.0.0",
                "required_capabilities": []
            }
        }
        
        with patch("app.agentic_pipeline.get_executor", return_value=slow_executor):
            with patch("app.agentic_pipeline.get_action_registry", return_value=mock_registry_obj):
                # Execute action
                start_time = time.time()
                result, output = run_agentic_action(
                    action="test_action",
                    payload={"test": "timeout"},
                    trace_id=str(uuid.uuid4())
                )
                elapsed = time.time() - start_time
                
                # Verify timeout returns reasonably fast (with shutdown(wait=False))
                # Allow generous margin (0.25s) since thread cleanup timing varies
                assert elapsed < 0.25, \
                    f"Expected fast timeout (<0.25s), took {elapsed:.2f}s"
                
                # Verify result is BLOCKED with EXECUTOR_TIMEOUT
                assert result.status == "BLOCKED", \
                    f"Expected status=BLOCKED, got {result.status}"
                
                assert "EXECUTOR_TIMEOUT" in result.reason_codes, \
                    f"Expected EXECUTOR_TIMEOUT in reason_codes, got {result.reason_codes}"
                
                # Verify output is None (no result from timed-out executor)
                assert output is None, \
                    f"Expected output=None for timeout, got {output}"

    def test_executor_no_timeout_passes(self, monkeypatch):
        """
        Fast executor completes without timeout.
        
        Scenario:
        - Mock executor that completes immediately
        - Set VERITTA_EXECUTOR_TIMEOUT_S to 5.0 (generous)
        - Execute action via run_agentic_action
        - Expected: SUCCESS status, no EXECUTOR_TIMEOUT
        
        Note: Privacy-by-design: raw output is not returned (output=None).
        """
        # Set generous timeout
        monkeypatch.setenv("VERITTA_EXECUTOR_TIMEOUT_S", "5.0")
        
        # Mock executor resolution to return fast executor
        fast_executor = FastExecutor()
        
        # Mock action registry to provide valid action metadata
        mock_registry_obj = Mock()
        mock_registry_obj.actions = {
            "test_action": {
                "action_version": "1.0.0",
                "executor_id": "test.fast",
                "min_executor_version": "1.0.0",
                "required_capabilities": []
            }
        }
        
        with patch("app.agentic_pipeline.get_executor", return_value=fast_executor):
            with patch("app.agentic_pipeline.get_action_registry", return_value=mock_registry_obj):
                # Execute action
                result, output = run_agentic_action(
                    action="test_action",
                    payload={"test": "fast"},
                    trace_id=str(uuid.uuid4())
                )
                
                # Verify result is SUCCESS
                assert result.status == "SUCCESS", \
                    f"Expected status=SUCCESS, got {result.status}"
                
                # Verify no timeout in reason_codes
                assert "EXECUTOR_TIMEOUT" not in result.reason_codes, \
                    f"Expected no EXECUTOR_TIMEOUT, got reason_codes={result.reason_codes}"
                
                # Privacy-by-design: raw output not returned
                assert output is None, \
                    f"Expected output=None (privacy-by-design), got {output}"
