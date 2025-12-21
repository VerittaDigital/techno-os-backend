"""
P1.1: Fail-closed audit logging tests.

Tests ensure that audit logging failures result in BLOCKED status,
never silent SUCCESS.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.agentic_pipeline import run_agentic_action
from app.audit_log import AuditLogError


def test_pre_audit_failure_blocks_execution(monkeypatch):
    """
    Test that PRE-AUDIT failure (before executor runs) blocks and prevents execution.
    
    Scenario:
    - log_action_result() raises AuditLogError
    - Expected: PRE-AUDIT result is converted to BLOCKED
    - Executor should never be called
    """
    # Force log_action_result to fail with AuditLogError
    def mock_log_fail(*args, **kwargs):
        raise AuditLogError("Simulated audit log failure")
    
    mock = MagicMock(side_effect=mock_log_fail)
    monkeypatch.setattr(
        "app.agentic_pipeline.log_action_result",
        mock
    )
    
    # Run action
    result, output = run_agentic_action(
        action="process",
        payload={"text": "test input"},
        trace_id="test-trace-001",
    )
    
    # Verify result is BLOCKED with AUDIT_LOG_FAILED reason
    assert result.status == "BLOCKED"
    assert "AUDIT_LOG_FAILED" in result.reason_codes
    
    # Verify output was not returned
    assert output is None


def test_post_audit_failure_blocks_even_after_execution(monkeypatch):
    """
    Test that POST-AUDIT failure (after executor runs) still blocks result.
    
    Scenario:
    - Executor runs and returns SUCCESS
    - log_action_result() raises AuditLogError during POST-AUDIT
    - Expected: Result is converted to BLOCKED despite success
    - Audit trail is protected (no silent SUCCESS)
    """
    call_count = {"count": 0}
    
    def mock_log_fail_on_success(*args, **kwargs):
        """Fail only on SUCCESS result (post-audit)."""
        call_count["count"] += 1
        result = args[0]
        
        # Allow PRE-AUDIT (PENDING status) to succeed
        if result.status == "PENDING":
            return  # Success
        
        # Fail on SUCCESS or other final statuses
        if result.status in ["SUCCESS", "FAILED"]:
            raise AuditLogError("Simulated post-audit logging failure")
    
    mock = MagicMock(side_effect=mock_log_fail_on_success)
    monkeypatch.setattr(
        "app.agentic_pipeline.log_action_result",
        mock
    )
    
    # Run action
    result, output = run_agentic_action(
        action="process",
        payload={"text": "test input"},
        trace_id="test-trace-002",
    )
    
    # Verify result is BLOCKED (not SUCCESS)
    assert result.status == "BLOCKED"
    assert "AUDIT_LOG_FAILED" in result.reason_codes
    
    # Verify output was not returned
    assert output is None
    
    # Verify log_action_result was called multiple times:
    # 1. PRE-AUDIT (PENDING) — succeeds
    # 2. POST-AUDIT (SUCCESS) — fails, triggers _safe_log conversion
    # 3. Fallback attempt to log BLOCKED result
    assert call_count["count"] >= 2


def test_successful_logging_returns_original_result(monkeypatch):
    """
    Test that when logging succeeds, original result is returned unchanged.
    
    Scenario:
    - log_action_result() succeeds (default behavior)
    - Expected: Original result returned, status unchanged
    """
    original_call_count = {"count": 0}
    
    def mock_log_success(*args, **kwargs):
        """Track that logging was called."""
        original_call_count["count"] += 1
    
    mock = MagicMock(side_effect=mock_log_success)
    monkeypatch.setattr(
        "app.agentic_pipeline.log_action_result",
        mock
    )
    
    # Run action with valid inputs
    result, output = run_agentic_action(
        action="process",
        payload={"text": "test input"},
        trace_id="test-trace-003",
    )
    
    # Verify result is SUCCESS (not BLOCKED)
    assert result.status == "SUCCESS"
    assert "AUDIT_LOG_FAILED" not in result.reason_codes
    
    # Output should still be None (privacy by design)
    assert output is None
    
    # Verify logging was called (PRE-AUDIT + POST-AUDIT)
    assert original_call_count["count"] >= 2
