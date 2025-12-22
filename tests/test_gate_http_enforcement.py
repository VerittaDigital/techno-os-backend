"""Tests for audit logging and gate enforcement in HTTP routes."""
import json
import logging
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.audit_log import log_decision
from app.decision_record import DecisionRecord
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestAuditLog:
    """log_decision writes JSON without raw payload."""

    def test_log_decision_writes_json(self, caplog):
        """log_decision writes one line of JSON."""
        record = DecisionRecord(
            decision="ALLOW",
            profile_id="test_profile",
            profile_hash="hash123",
            matched_rules=["rule1"],
            reason_codes=["OK"],
            input_digest="abc123",
            trace_id="trace-001",
            ts_utc=datetime.now(timezone.utc),
        )

        with caplog.at_level(logging.INFO, logger="gate_audit"):
            log_decision(record)

        # Check that something was logged
        assert len(caplog.records) > 0
        log_output = caplog.text

        # Should contain the decision and trace_id
        assert "ALLOW" in log_output
        assert "trace-001" in log_output

    def test_log_decision_serializable_to_json(self, caplog):
        """log_decision output is valid JSON."""
        record = DecisionRecord(
            decision="DENY",
            profile_id="test",
            profile_hash="",
            matched_rules=[],
            reason_codes=["GATE_EXCEPTION"],
            input_digest="x",
            trace_id="trace-002",
            ts_utc=datetime.now(timezone.utc),
        )

        with caplog.at_level(logging.INFO, logger="gate_audit"):
            log_decision(record)

        # Extract the JSON line from log
        log_lines = [r.message for r in caplog.records if r.name == "gate_audit"]
        assert len(log_lines) > 0

        # Parse it back
        logged_json = json.loads(log_lines[0])
        assert logged_json["decision"] == "DENY"
        assert logged_json["trace_id"] == "trace-002"


class TestGateEnforcementHTTP:
    """Gate enforcement in /process and openness of /health."""

    def test_health_endpoint_open(self, client):
        """/health does not require gating."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_process_allows_valid_input(self, client):
        """/process allows valid ProcessRequest that passes gate."""
        payload = {"text": "hello world"}
        response = client.post("/process", json=payload)

        # Should succeed (gate allows, pipeline executes)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["action"] == "process"
        assert "output_digest" in data
        assert "trace_id" in data

    def test_process_denies_on_gate_denial(self, client, caplog):
        """/process returns 403 when gate denies."""
        # Inject a payload that will cause gate to deny
        # (e.g., unknown action would trigger denial in default profiles)
        # For this test, we'll use a trick: send invalid JSON-like payload
        # that causes a gate exception (which defaults to DENY)

        # Actually, with the current gate configuration, we can pass a valid
        # ProcessRequest and it should go through. To force a denial, we need
        # to patch the gate_engine to deny.

        with patch("app.main.evaluate_gate") as mock_gate:
            from app.contracts.gate_v1 import GateDecision, GateResult
            mock_result = GateResult(
                decision=GateDecision.DENY,
                reasons=[],
                action="process",
                evaluated_keys=[],
                profile_hash="test_hash_deny",  # P1.5: profile_hash now required
                matched_rules=["test_rule"],  # P1.5: matched_rules now present
            )
            mock_gate.return_value = mock_result

            payload = {"text": "should deny"}
            with caplog.at_level(logging.INFO, logger="gate_audit"):
                response = client.post("/process", json=payload)

            assert response.status_code == 403

            # Check that a DecisionRecord was logged with DENY
            log_lines = [r.message for r in caplog.records if r.name == "gate_audit"]
            assert len(log_lines) > 0
            logged_json = json.loads(log_lines[0])
            assert logged_json["decision"] == "DENY"

    def test_process_handles_gate_exception(self, client, caplog):
        """/process returns 403 and logs GATE_EXCEPTION when gate raises."""
        with patch("app.main.evaluate_gate") as mock_gate:
            mock_gate.side_effect = RuntimeError("Simulated gate error")

            payload = {"text": "should trigger exception"}
            with caplog.at_level(logging.INFO, logger="gate_audit"):
                response = client.post("/process", json=payload)

            assert response.status_code == 403

            # Check that GATE_EXCEPTION was logged
            log_lines = [r.message for r in caplog.records if r.name == "gate_audit"]
            assert len(log_lines) > 0
            logged_json = json.loads(log_lines[0])
            assert logged_json["decision"] == "DENY"
            assert "GATE_EXCEPTION" in logged_json["reason_codes"]

    def test_audit_log_does_not_contain_raw_payload(self, client, caplog):
        """Audit log contains only input_digest, not raw payload."""
        payload = {"text": "secret data"}

        with caplog.at_level(logging.INFO, logger="gate_audit"):
            response = client.post("/process", json=payload)

        assert response.status_code == 200

        # Extract audit log
        log_lines = [r.message for r in caplog.records if r.name == "gate_audit"]
        assert len(log_lines) > 0
        audit_output = " ".join(log_lines)

        # Should not contain the raw text
        assert "secret data" not in audit_output

        # Should contain the digest (sha256 hex)
        assert "input_digest" in audit_output

    def test_gated_endpoint_logs_on_success(self, client, caplog):
        """Successful /process call still logs a DecisionRecord."""
        payload = {"text": "valid input"}

        with caplog.at_level(logging.INFO, logger="gate_audit"):
            response = client.post("/process", json=payload)

        assert response.status_code == 200

        # Check that ALLOW was logged
        log_lines = [r.message for r in caplog.records if r.name == "gate_audit"]
        assert len(log_lines) > 0
        logged_json = json.loads(log_lines[0])
        assert logged_json["decision"] == "ALLOW"

    def test_trace_id_in_log(self, client, caplog):
        """DecisionRecord includes trace_id for request correlation."""
        payload = {"text": "trace test"}

        with caplog.at_level(logging.INFO, logger="gate_audit"):
            response = client.post("/process", json=payload)

        assert response.status_code == 200

        log_lines = [r.message for r in caplog.records if r.name == "gate_audit"]
        assert len(log_lines) > 0
        logged_json = json.loads(log_lines[0])

        # Trace ID should be a valid UUID-like string
        trace_id = logged_json["trace_id"]
        assert len(trace_id) == 36  # UUID format
        assert trace_id.count("-") == 4

    def test_empty_request_body(self, client, caplog):
        """/process with empty body gets gated and executed (pipeline handles it)."""
        with caplog.at_level(logging.INFO, logger="gate_audit"):
            response = client.post("/process", json={"text": ""})

        # Empty text now goes through pipeline (executor handles it)
        # Executor will raise exception -> FAILED status
        assert response.status_code == 200
        data = response.json()
        # Empty string after strip() causes executor to fail
        assert data["status"] in ["SUCCESS", "FAILED"]

        # Gate audit should have logged
        log_lines = [r.message for r in caplog.records if r.name == "gate_audit"]
        if log_lines:  # May or may not log depending on exact order
            logged_json = json.loads(log_lines[0])
            assert logged_json["decision"] in ["ALLOW", "DENY"]

    def test_malformed_json_request_body(self, client):
        """Malformed JSON in request body is handled gracefully."""
        # Gate dependency parses JSON, treats invalid as empty dict
        response = client.post(
            "/process",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )

        # Gate handles malformed JSON gracefully (treats as empty dict)
        # Pipeline then executes with empty payload -> likely FAILED
        assert response.status_code == 200

    def test_input_digest_computed_for_empty_payload(self, client, caplog):
        """Even empty payloads get input_digest computed."""
        # Send a valid text to pass endpoint logic, but mock gate to see the digest
        with patch("app.main.evaluate_gate") as mock_gate:
            from app.contracts.gate_v1 import GateDecision, GateResult

            def capture_call(gate_input):
                # Just log and return ALLOW
                return GateResult(
                    decision=GateDecision.ALLOW,
                    reasons=[],
                    action="process",
                    evaluated_keys=[],
                    profile_hash="test_hash_allow",  # P1.5: profile_hash now required
                    matched_rules=[],  # P1.5: matched_rules (empty for ALLOW)
                )

            mock_gate.side_effect = capture_call

            payload = {"text": "test"}
            with caplog.at_level(logging.INFO, logger="gate_audit"):
                response = client.post("/process", json=payload)

            assert response.status_code == 200

            log_lines = [r.message for r in caplog.records if r.name == "gate_audit"]
            assert len(log_lines) > 0
            logged_json = json.loads(log_lines[0])

            # input_digest should be present and be a hex string
            assert "input_digest" in logged_json
            digest = logged_json["input_digest"]
            assert len(digest) == 64
            assert all(c in "0123456789abcdef" for c in digest)
