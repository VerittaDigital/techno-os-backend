"""Tests for A4: rule_evaluator_v1 executor."""
import json
import logging
import uuid

import pytest

from app.agentic_pipeline import run_agentic_action
from app.action_contracts import ActionRequest
from app.executors.registry import get_executor


class TestRuleEvaluatorRegistry:
    def test_registered(self):
        executor = get_executor("rule_evaluator_v1")
        assert executor is not None
        assert executor.executor_id == "rule_evaluator_v1"


class TestRuleEvaluatorExecution:
    def test_execute_happy_path_direct(self):
        executor = get_executor("rule_evaluator_v1")
        req = ActionRequest(
            action="rule_evaluate",
            payload={
                "rules": [{"field": "amount", "op": ">", "value": 1000}],
                "input": {"amount": 1200},
            },
            trace_id=str(uuid.uuid4()),
        )
        output = executor.execute(req)
        assert isinstance(output, dict)
        assert output["matched"] is True
        assert len(output["matches"]) == 1

    def test_execute_no_matches_direct(self):
        executor = get_executor("rule_evaluator_v1")
        req = ActionRequest(
            action="rule_evaluate",
            payload={
                "rules": [{"field": "amount", "op": ">", "value": 1000}],
                "input": {"amount": 100},
            },
            trace_id=str(uuid.uuid4()),
        )
        output = executor.execute(req)
        assert output["matched"] is False
        assert output["matches"] == []

    def test_execute_invalid_payload_direct_raises(self):
        executor = get_executor("rule_evaluator_v1")
        req = ActionRequest(
            action="rule_evaluate",
            payload={
                # missing 'rules' key
                "input": {"amount": 100},
            },
            trace_id=str(uuid.uuid4()),
        )
        with pytest.raises(ValueError) as exc:
            executor.execute(req)
        assert str(exc.value) == "INVALID_PAYLOAD"


class TestRuleEvaluatorPipeline:
    def test_pipeline_happy_path_and_audit(self, caplog):
        payload = {
            "rules": [{"field": "amount", "op": ">", "value": 1000}],
            "input": {"amount": 1200},
        }
        trace_id = str(uuid.uuid4())
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="rule_evaluate",
                payload=payload,
                trace_id=trace_id,
            )

        assert result.status == "SUCCESS"
        assert result.executor_id == "rule_evaluator_v1"
        assert result.trace_id == trace_id
        # Output is not returned by pipeline (privacy)
        assert output is None

        # Check audit logs include executor_id and executor_version
        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        assert len(action_logs) >= 1
        # find success log
        success = None
        for msg in action_logs:
            j = json.loads(msg)
            if j.get("status") == "SUCCESS":
                success = j
                break
        assert success is not None
        assert success["executor_id"] == "rule_evaluator_v1"
        assert success["executor_version"] == "1.0.0"
        assert success["trace_id"] == trace_id

    def test_pipeline_invalid_payload_results_failed(self, caplog):
        payload = {"input": {"amount": 100}}  # missing rules
        trace_id = str(uuid.uuid4())
        with caplog.at_level(logging.INFO, logger="action_audit"):
            result, output = run_agentic_action(
                action="rule_evaluate",
                payload=payload,
                trace_id=trace_id,
            )

        assert result.status == "FAILED"
        assert "EXECUTOR_EXCEPTION" in result.reason_codes
        assert output is None

    def test_determinism_input_and_output_digest(self):
        payload = {
            "rules": [{"field": "amount", "op": ">", "value": 1000}],
            "input": {"amount": 1200},
        }
        r1, _ = run_agentic_action(action="rule_evaluate", payload=payload, trace_id=str(uuid.uuid4()))
        r2, _ = run_agentic_action(action="rule_evaluate", payload=payload, trace_id=str(uuid.uuid4()))
        assert r1.input_digest == r2.input_digest
        assert r1.output_digest == r2.output_digest