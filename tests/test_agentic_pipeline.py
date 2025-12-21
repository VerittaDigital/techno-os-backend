"""Tests for agentic pipeline execution layer.

Validates determinism, fail-closed behavior, audit logging, and privacy.
Tests pipeline WITHOUT FastAPI integration.
"""
import json
import logging

import pytest

from app.agentic_pipeline import run_agentic_action
from app.executors.base import ExecutorLimits
from app.executors.registry import _EXECUTORS


class TestPipelineUnknownAction:
    """Test pipeline behavior with unknown actions."""

    def test_unknown_action_blocked(self, caplog):
        """Unknown action produces BLOCKED + ACTION_UNKNOWN + audit log."""
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="nonexistent_action",
                payload={"test": "data"},
                trace_id="trace-unknown",
            )

        assert result.status == "BLOCKED"
        assert "ACTION_UNKNOWN" in result.reason_codes
        assert output is None

        # Check audit log was emitted
        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        assert len(action_logs) > 0
        logged = json.loads(action_logs[0])
        assert logged["status"] == "BLOCKED"
        assert "ACTION_UNKNOWN" in logged["reason_codes"]


class TestPipelineNonJSONPayload:
    """Test pipeline behavior with non-JSON-serializable payloads."""

    def test_non_json_payload_blocked(self, caplog):
        """Non-JSON payload produces BLOCKED + NON_JSON_PAYLOAD."""

        class NonSerializable:
            pass

        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="process",
                payload={"obj": NonSerializable()},
                trace_id="trace-nonjson",
            )

        assert result.status == "BLOCKED"
        assert "NON_JSON_PAYLOAD" in result.reason_codes
        assert output is None


class TestPipelineLimits:
    """Test payload limits enforcement."""

    def test_limit_exceeded_bytes(self, caplog):
        """Payload exceeding max_bytes produces BLOCKED + LIMIT_EXCEEDED."""
        large_payload = {"data": "x" * 20_000}  # Exceeds 10KB limit

        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="process",
                payload=large_payload,
                trace_id="trace-limit-bytes",
            )

        assert result.status == "BLOCKED"
        assert "LIMIT_EXCEEDED" in result.reason_codes
        assert output is None

    def test_limit_exceeded_depth(self, caplog):
        """Payload exceeding max_depth produces BLOCKED + LIMIT_EXCEEDED."""
        # Create deeply nested dict (depth > 10)
        nested = {"a": "value"}
        for i in range(15):
            nested = {"level": nested}

        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="process",
                payload=nested,
                trace_id="trace-limit-depth",
            )

        assert result.status == "BLOCKED"
        assert "LIMIT_EXCEEDED" in result.reason_codes

    def test_limit_exceeded_list_items(self, caplog):
        """Payload with large list produces BLOCKED + LIMIT_EXCEEDED."""
        payload = {"items": list(range(200))}  # Exceeds 100 items limit

        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="process",
                payload=payload,
                trace_id="trace-limit-list",
            )

        assert result.status == "BLOCKED"
        assert "LIMIT_EXCEEDED" in result.reason_codes


class TestPipelineExecutorException:
    """Test pipeline behavior when executor raises exceptions."""

    def test_executor_exception_failed(self, caplog):
        """Executor exception produces FAILED + EXECUTOR_EXCEPTION."""
        # Missing "text" field will cause KeyError in executor
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="process",
                payload={"wrong_field": "value"},
                trace_id="trace-exception",
            )

        assert result.status == "FAILED"
        assert "EXECUTOR_EXCEPTION" in result.reason_codes
        assert output is None


class TestPipelineTimeout:
    """Test simulated timeout mapping."""

    def test_timeout_error_mapped_to_failed(self, caplog):
        """TimeoutError from executor produces FAILED + EXECUTOR_TIMEOUT."""

        # Create a mock executor that raises TimeoutError
        class TimeoutExecutor:
            def __init__(self):
                self.executor_id = "timeout_test_v1"
                self.version = "1.0.0"
                self.limits = ExecutorLimits(
                    timeout_ms=100,
                    max_payload_bytes=1000,
                    max_depth=10,
                    max_list_items=50,
                )

            def execute(self, req):
                raise TimeoutError("Simulated timeout")

        # Temporarily register timeout executor
        _EXECUTORS["timeout_test_v1"] = TimeoutExecutor()

        try:
            # Temporarily add to action registry
            from app.action_router import ACTION_REGISTRY
            ACTION_REGISTRY["timeout_action"] = "timeout_test_v1"

            # Temporarily allow this action in matrix for testing
            from app.action_matrix import ActionMatrix, set_action_matrix
            set_action_matrix(ActionMatrix(
                profile="default",
                allowed_actions=["process", "timeout_action"]
            ))

            with caplog.at_level(logging.INFO, logger="action_audit"):
                result, output = run_agentic_action(
                    action="timeout_action",
                    payload={"test": "data"},
                    trace_id="trace-timeout",
                )

            assert result.status == "FAILED"
            assert "EXECUTOR_TIMEOUT" in result.reason_codes
            assert output is None

        finally:
            # Cleanup
            del _EXECUTORS["timeout_test_v1"]
            del ACTION_REGISTRY["timeout_action"]


class TestPipelinePrivacy:
    """Test that audit logs do NOT contain raw payloads."""

    def test_action_audit_no_raw_payload(self, caplog):
        """Action audit logs contain only digests, not raw payloads."""
        secret_payload = {"text": "secret sensitive data"}

        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="process",
                payload=secret_payload,
                trace_id="trace-privacy",
            )

        assert result.status == "SUCCESS"

        # Extract audit log
        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        assert len(action_logs) > 0
        audit_output = " ".join(action_logs)

        # Should NOT contain raw payload text
        assert "secret sensitive data" not in audit_output

        # Should contain digests
        assert "input_digest" in audit_output
        assert "output_digest" in audit_output


class TestPipelineDeterminism:
    """Test deterministic routing and digest stability."""

    def test_input_digest_stable_across_key_order(self):
        """input_digest is stable regardless of dict key order."""
        payload_1 = {"b": 2, "a": 1, "text": "hello"}
        payload_2 = {"text": "hello", "a": 1, "b": 2}

        result_1, _ = run_agentic_action(
            action="process",
            payload=payload_1,
            trace_id="trace-digest-1",
        )
        result_2, _ = run_agentic_action(
            action="process",
            payload=payload_2,
            trace_id="trace-digest-2",
        )

        # Same semantic payload -> same input_digest
        assert result_1.input_digest == result_2.input_digest

    def test_router_determinism(self):
        """Same action always routes to same executor."""
        result_1, _ = run_agentic_action(
            action="process",
            payload={"text": "test1"},
            trace_id="trace-route-1",
        )
        result_2, _ = run_agentic_action(
            action="process",
            payload={"text": "test2"},
            trace_id="trace-route-2",
        )

        assert result_1.executor_id == result_2.executor_id
        assert result_1.executor_id == "text_process_v1"


class TestPipelineSuccess:
    """Test successful execution path."""

    def test_successful_execution(self, caplog):
        """Successful execution produces SUCCESS with output_digest (after pre-audit PENDING)."""
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="process",
                payload={"text": "hello world"},
                trace_id="trace-success",
            )

        assert result.status == "SUCCESS"
        assert result.reason_codes == []
        assert result.output_digest is not None
        assert output is None  # Raw output NEVER returned

        # Check audit logs (should be 2: PENDING + SUCCESS)
        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        assert len(action_logs) >= 2, f"Expected at least 2 audit logs (PRE + POST), got {len(action_logs)}"
        
        # First log should be PENDING (pre-audit)
        pre_audit = json.loads(action_logs[0])
        assert pre_audit["status"] == "PENDING"
        assert "EXECUTION_ATTEMPT" in pre_audit["reason_codes"]
        
        # Last log should be SUCCESS
        logged = json.loads(action_logs[-1])
        assert logged["status"] == "SUCCESS"
        assert logged["output_digest"] is not None

    def test_output_digest_deterministic(self):
        """Same output produces same output_digest."""
        result_1, _ = run_agentic_action(
            action="process",
            payload={"text": "test"},
            trace_id="trace-out-1",
        )
        result_2, _ = run_agentic_action(
            action="process",
            payload={"text": "test"},
            trace_id="trace-out-2",
        )

        # Same input -> same output -> same output_digest
        assert result_1.output_digest == result_2.output_digest
        assert result_1.output_digest is not None
