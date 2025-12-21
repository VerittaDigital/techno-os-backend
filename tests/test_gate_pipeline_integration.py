"""Integration tests for gate + pipeline interaction in HTTP layer.

Validates that gate DENY prevents pipeline execution (INEVITABILITY).
"""
import json
import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestGateDenyPreventsExecution:
    """Test INEVITABILITY: gate DENY must prevent pipeline execution."""

    def test_gate_deny_no_action_audit(self, client, caplog):
        """When gate denies, action_audit MUST NOT be emitted."""
        # Force gate to deny
        with patch("app.main.evaluate_gate") as mock_gate:
            from app.contracts.gate_v1 import GateDecision, GateResult

            mock_result = GateResult(
                decision=GateDecision.DENY,
                reasons=[],
                action="process",
                evaluated_keys=[],
            )
            mock_gate.return_value = mock_result

            with caplog.at_level(logging.INFO):
                response = client.post("/process", json={"text": "should deny"})

            assert response.status_code == 403

            # Check that gate_audit was logged
            gate_logs = [r.message for r in caplog.records if r.name == "gate_audit"]
            assert len(gate_logs) > 0
            gate_json = json.loads(gate_logs[0])
            assert gate_json["decision"] == "DENY"

            # Check that action_audit was NOT logged
            action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
            assert len(action_logs) == 0, "Action audit MUST NOT be emitted when gate denies"


class TestGateAllowThenExecute:
    """Test that gate ALLOW flows into pipeline execution."""

    def test_gate_allow_produces_both_audits(self, client, caplog):
        """Gate ALLOW produces gate_audit + action_audit (PENDING + SUCCESS)."""
        with caplog.at_level(logging.INFO):
            response = client.post("/process", json={"text": "hello"})

        assert response.status_code == 200

        # Check gate_audit
        gate_logs = [r.message for r in caplog.records if r.name == "gate_audit"]
        assert len(gate_logs) > 0
        gate_json = json.loads(gate_logs[0])
        assert gate_json["decision"] == "ALLOW"

        # Check action_audit (now should have PENDING + SUCCESS)
        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        assert len(action_logs) >= 2, f"Expected at least 2 action logs (PENDING + SUCCESS), got {len(action_logs)}"
        
        # First should be PENDING (pre-audit)
        first_action = json.loads(action_logs[0])
        assert first_action["status"] == "PENDING"
        
        # Last should be SUCCESS
        last_action = json.loads(action_logs[-1])
        assert last_action["status"] == "SUCCESS"

        # Same trace_id in all
        assert gate_json["trace_id"] == first_action["trace_id"]
        assert gate_json["trace_id"] == last_action["trace_id"]

    def test_response_minimal_no_raw_output(self, client):
        """Response contains only status, trace_id, action, output_digest."""
        response = client.post("/process", json={"text": "test"})
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "trace_id" in data
        assert "action" in data
        assert "output_digest" in data

        # Should NOT contain raw output
        assert "processed" not in data
        assert "HELLO" not in str(data)

    def test_health_still_public(self, client):
        """/health remains public and ungated."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSingleReadInvariant:
    """Test that request body is read exactly once."""

    def test_successful_request_uses_cached_payload(self, client, caplog):
        """Pipeline uses cached payload from gate, not re-reading body."""
        payload = {"text": "cached test"}

        with caplog.at_level(logging.INFO):
            response = client.post("/process", json=payload)

        assert response.status_code == 200

        # Verify action audit shows same input_digest as gate audit
        gate_logs = [r.message for r in caplog.records if r.name == "gate_audit"]
        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]

        gate_json = json.loads(gate_logs[0])
        action_json = json.loads(action_logs[0])

        # Same trace_id (proves correlation)
        assert gate_json["trace_id"] == action_json["trace_id"]

        # input_digest in both should match (same payload)
        assert gate_json["input_digest"] == action_json["input_digest"]


class TestExecutorFailure:
    """Test that executor failures produce proper HTTP responses."""

    def test_executor_exception_returns_200_with_failed_status(self, client):
        """Executor exception produces HTTP 200 with status=FAILED."""
        # Send payload with "text" as non-string to trigger ValueError in executor
        response = client.post("/process", json={"text": 123})  # text must be string

        # Pipeline handles exception gracefully (no HTTP 500)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "FAILED"
        assert data["action"] == "process"


class TestProfileActionMismatchHTTP:
    """Test that PROFILE_ACTION_MISMATCH produces HTTP 403 with action_audit emitted."""

    def test_mismatch_returns_403_and_logs_audit(self, client, caplog):
        """When action blocked due to PROFILE_ACTION_MISMATCH, HTTP 403 returned and action_audit emitted."""
        from app.action_matrix import ActionMatrix, set_action_matrix
        
        # Set matrix that forbids "process" action
        restricted_matrix = ActionMatrix(
            profile="default",
            allowed_actions=[]  # No actions allowed
        )
        set_action_matrix(restricted_matrix)

        with caplog.at_level(logging.INFO):
            response = client.post("/process", json={"text": "test"})

        # Must return HTTP 403
        assert response.status_code == 403

        # Must have emitted action_audit (before raising HTTPException)
        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        assert len(action_logs) > 0, "action_audit MUST be emitted before HTTP 403"
        
        action_json = json.loads(action_logs[0])
        assert action_json["status"] == "BLOCKED"
        assert "PROFILE_ACTION_MISMATCH" in action_json["reason_codes"]

    def test_mismatch_preserves_trace_id_correlation(self, client, caplog):
        """trace_id must be identical in gate_audit and action_audit even when PROFILE_ACTION_MISMATCH occurs."""
        from app.action_matrix import ActionMatrix, set_action_matrix
        
        # Set matrix that forbids "process" action
        restricted_matrix = ActionMatrix(
            profile="default",
            allowed_actions=[]  # No actions allowed
        )
        set_action_matrix(restricted_matrix)

        with caplog.at_level(logging.INFO):
            response = client.post("/process", json={"text": "test"})

        # Must return HTTP 403
        assert response.status_code == 403

        # Extract gate_audit and action_audit logs
        gate_logs = [r.message for r in caplog.records if r.name == "gate_audit"]
        action_logs = [r.message for r in caplog.records if r.name == "action_audit"]

        assert len(gate_logs) > 0, "gate_audit MUST be emitted"
        assert len(action_logs) > 0, "action_audit MUST be emitted"

        gate_json = json.loads(gate_logs[0])
        action_json = json.loads(action_logs[0])

        # Validate trace_id correlation
        assert gate_json["trace_id"] == action_json["trace_id"], "trace_id must be identical across audits"

        # Validate gate allowed (mismatch is in pipeline, not gate)
        assert gate_json["decision"] == "ALLOW"

        # Validate action blocked with mismatch
        assert action_json["status"] == "BLOCKED"
        assert "PROFILE_ACTION_MISMATCH" in action_json["reason_codes"]

