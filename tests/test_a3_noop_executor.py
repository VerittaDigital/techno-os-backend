"""Tests for A3 noop executor.

Validates:
- Executor returns SUCCESS status
- No output is produced
- No exceptions are raised
- Pipeline calls executor correctly
- Audit logs contain correct executor_id
- No regressions in existing tests
"""
import json
import logging
import uuid

import pytest

from app.agentic_pipeline import run_agentic_action
from app.action_audit_log import log_action_result
from app.action_contracts import ActionResult
from app.executors.registry import get_executor, UnknownExecutorError


class TestNoopExecutorRegistry:
    """Test noop_executor_v1 is registered and retrievable."""

    def test_executor_registered(self):
        """Verify noop_executor_v1 exists in registry."""
        executor = get_executor("noop_executor_v1")
        assert executor is not None
        assert executor.executor_id == "noop_executor_v1"

    def test_executor_has_correct_version(self):
        """Verify executor version is semantic version."""
        executor = get_executor("noop_executor_v1")
        assert executor.version == "1.0.0"

    def test_executor_has_capabilities(self):
        """Verify executor declares capabilities (even if empty)."""
        executor = get_executor("noop_executor_v1")
        assert hasattr(executor, "capabilities")
        # noop has no required capabilities
        assert executor.capabilities == []

    def test_executor_has_limits(self):
        """Verify executor declares limits."""
        executor = get_executor("noop_executor_v1")
        assert hasattr(executor, "limits")
        assert executor.limits.timeout_ms == 1000
        assert executor.limits.max_payload_bytes == 10_000


class TestNoopExecutorExecution:
    """Test noop executor execution behavior."""

    def test_executor_returns_none(self):
        """Noop executor returns None (no output)."""
        from app.action_contracts import ActionRequest
        
        executor = get_executor("noop_executor_v1")
        req = ActionRequest(
            action="noop",
            payload={"test": "data"},
            trace_id=str(uuid.uuid4()),
        )
        
        output = executor.execute(req)
        assert output is None

    def test_executor_does_not_raise(self):
        """Noop executor never raises exceptions."""
        from app.action_contracts import ActionRequest
        
        executor = get_executor("noop_executor_v1")
        
        # Test various payloads
        test_payloads = [
            {},
            {"empty": "payload"},
            {"nested": {"deep": {"structure": "value"}}},
            {"list": [1, 2, 3]},
        ]
        
        for payload in test_payloads:
            req = ActionRequest(
                action="noop",
                payload=payload,
                trace_id=str(uuid.uuid4()),
            )
            # Should not raise
            output = executor.execute(req)
            assert output is None


class TestNoopExecutorPipeline:
    """Test noop action through full pipeline."""

    def test_pipeline_noop_action_returns_success(self, caplog):
        """Pipeline resolves noop action, executes, and returns SUCCESS."""
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="noop",
                payload={"test": "data"},
                trace_id=str(uuid.uuid4()),
            )

        assert result.status == "SUCCESS"
        assert result.reason_codes == []
        assert result.executor_id == "noop_executor_v1"
        assert output is None

    def test_pipeline_noop_no_output_digest(self, caplog):
        """Noop action produces output_digest of None (no output)."""
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="noop",
                payload={},
                trace_id=str(uuid.uuid4()),
            )

        assert result.output_digest is None
        assert result.status == "SUCCESS"

    def test_pipeline_noop_has_input_digest(self, caplog):
        """Noop action still computes input_digest (payload is JSON-serializable)."""
        payload = {"test": "data"}
        
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="noop",
                payload=payload,
                trace_id=str(uuid.uuid4()),
            )

        assert result.input_digest is not None
        assert result.status == "SUCCESS"

    def test_pipeline_noop_preserves_trace_id(self, caplog):
        """Noop action preserves trace_id from request."""
        trace_id = str(uuid.uuid4())
        
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="noop",
                payload={},
                trace_id=trace_id,
            )

        assert result.trace_id == trace_id


class TestNoopExecutorAudit:
    """Test audit logging for noop executor."""

    def test_audit_log_contains_executor_id(self, caplog):
        """Audit log includes correct executor_id."""
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="noop",
                payload={},
                trace_id=str(uuid.uuid4()),
            )

        # Extract audit logs
        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        assert len(action_logs) >= 1, "No audit logs found"
        
        # Find success log (may have EXECUTION_ATTEMPT first)
        logged_data = None
        for log_msg in action_logs:
            logged = json.loads(log_msg)
            if logged.get("status") == "SUCCESS":
                logged_data = logged
                break
        
        assert logged_data is not None, "No SUCCESS audit log found"
        assert logged_data["executor_id"] == "noop_executor_v1"
        assert logged_data["action"] == "noop"

    def test_audit_log_has_status_success(self, caplog):
        """Audit log status is SUCCESS."""
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="noop",
                payload={},
                trace_id=str(uuid.uuid4()),
            )

        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        
        # Find success log
        success_logs = [json.loads(log_msg) for log_msg in action_logs if json.loads(log_msg).get("status") == "SUCCESS"]
        assert len(success_logs) >= 1, "No SUCCESS audit log found"
        
        logged = success_logs[0]
        assert logged["status"] == "SUCCESS"
        assert logged["reason_codes"] == []

    def test_audit_log_has_version(self, caplog):
        """Audit log includes executor version."""
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="noop",
                payload={},
                trace_id=str(uuid.uuid4()),
            )

        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        success_logs = [json.loads(log_msg) for log_msg in action_logs if json.loads(log_msg).get("status") == "SUCCESS"]
        
        logged = success_logs[0]
        assert logged["executor_version"] == "1.0.0"


class TestNoopExecutorDeterminism:
    """Test noop executor is deterministic and side-effect free."""

    def test_multiple_executions_identical(self):
        """Multiple executions with same input produce identical results."""
        trace_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        results = []
        for trace_id in trace_ids:
            result, output = run_agentic_action(
                action="noop",
                payload={"test": "data"},
                trace_id=trace_id,
            )
            results.append(result)
        
        # All should have SUCCESS status
        assert all(r.status == "SUCCESS" for r in results)
        
        # All should have same executor_id
        assert all(r.executor_id == "noop_executor_v1" for r in results)
        
        # All should have same input_digest (same payload)
        assert len(set(r.input_digest for r in results)) == 1
        
        # All should have None output_digest
        assert all(r.output_digest is None for r in results)

    def test_different_payloads_different_digest(self):
        """Different payloads produce different input digests."""
        payload1 = {"a": "1"}
        payload2 = {"b": "2"}
        
        result1, _ = run_agentic_action(
            action="noop",
            payload=payload1,
            trace_id=str(uuid.uuid4()),
        )
        result2, _ = run_agentic_action(
            action="noop",
            payload=payload2,
            trace_id=str(uuid.uuid4()),
        )
        
        # Both succeed
        assert result1.status == "SUCCESS"
        assert result2.status == "SUCCESS"
        
        # But have different digests
        assert result1.input_digest != result2.input_digest
