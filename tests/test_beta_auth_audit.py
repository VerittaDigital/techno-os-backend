"""
Tests for auditable auth in gate_request (app/main.py).

These tests verify:
1. Missing X-API-Key header -> 401 + audit entry with AUTH_MISSING_KEY
2. Invalid X-API-Key -> 401 + audit entry with AUTH_INVALID_KEY
3. Valid X-API-Key -> not 401 + audit entry reflects gate decision (no AUTH_*)
"""

import json
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_audit(tmp_path, monkeypatch):
    """
    Fixture: TestClient with VERITTA_BETA_API_KEY and VERITTA_AUDIT_LOG_PATH set.
    
    Returns tuple (client, audit_log_path) for audit verification.
    """
    audit_log_path = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_BETA_API_KEY", "test-secret")
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log_path))
    
    from app.main import app
    client = TestClient(app)
    return client, audit_log_path


class TestBetaAuthAudit:
    """Test suite for auditable auth in gate_request."""

    def test_missing_key_audit_logged(self, client_with_audit):
        """
        POST /process without X-API-Key header must return 401 and log DENY with AUTH_MISSING_KEY.
        
        Scenario:
        - VERITTA_BETA_API_KEY="test-secret" (key is configured)
        - No X-API-Key header in request
        - Expected: 401 Unauthorized (fail-closed)
        - Audit: Last line in audit.log contains DENY + AUTH_MISSING_KEY + trace_id
        """
        client, audit_log_path = client_with_audit
        
        # Call /process without header
        response = client.post(
            "/process",
            json={"text": "hello"}
        )
        
        # Must return 401
        assert response.status_code == 401, \
            f"Expected 401, got {response.status_code}. Response: {response.text}"
        
        # Verify audit entry was logged
        assert audit_log_path.exists(), "Audit log file not created"
        
        # Read last line of audit log
        with open(audit_log_path, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0, "Audit log is empty"
            last_line = lines[-1].strip()
        
        # Parse JSON and verify fields
        audit_entry = json.loads(last_line)
        assert audit_entry["decision"] == "DENY", \
            f"Expected decision=DENY, got {audit_entry.get('decision')}"
        assert "AUTH_MISSING_KEY" in audit_entry["reason_codes"], \
            f"Expected AUTH_MISSING_KEY in reason_codes, got {audit_entry.get('reason_codes')}"
        assert "trace_id" in audit_entry, "Audit entry missing trace_id"
        assert audit_entry["trace_id"], "trace_id is empty"

    def test_invalid_key_audit_logged(self, client_with_audit):
        """
        POST /process with wrong X-API-Key value must return 401 and log DENY with AUTH_INVALID_KEY.
        
        Scenario:
        - VERITTA_BETA_API_KEY="test-secret" (expected key)
        - X-API-Key="wrong" (invalid key)
        - Expected: 401 Unauthorized (fail-closed)
        - Audit: Last line in audit.log contains DENY + AUTH_INVALID_KEY + trace_id
        """
        client, audit_log_path = client_with_audit
        
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={"X-API-Key": "wrong"}
        )
        
        # Must return 401
        assert response.status_code == 401, \
            f"Expected 401, got {response.status_code}. Response: {response.text}"
        
        # Verify audit entry was logged
        assert audit_log_path.exists(), "Audit log file not created"
        
        # Read last line of audit log
        with open(audit_log_path, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0, "Audit log is empty"
            last_line = lines[-1].strip()
        
        # Parse JSON and verify fields
        audit_entry = json.loads(last_line)
        assert audit_entry["decision"] == "DENY", \
            f"Expected decision=DENY, got {audit_entry.get('decision')}"
        assert "AUTH_INVALID_KEY" in audit_entry["reason_codes"], \
            f"Expected AUTH_INVALID_KEY in reason_codes, got {audit_entry.get('reason_codes')}"
        assert "trace_id" in audit_entry, "Audit entry missing trace_id"
        assert audit_entry["trace_id"], "trace_id is empty"

    def test_valid_key_audit_is_gate_decision(self, client_with_audit):
        """
        POST /process with valid X-API-Key must NOT return 401 and audit reflects gate decision (not AUTH_*).
        
        Scenario:
        - VERITTA_BETA_API_KEY="test-secret" (expected key)
        - X-API-Key="test-secret" (valid key)
        - payload: {"text":"hello"} (valid request)
        - Expected: Not 401; endpoint processes normally
        - Audit: Gate decision line (first line for this trace_id) does NOT contain AUTH_MISSING_KEY or AUTH_INVALID_KEY
                 (should be ALLOW or DENY from gate evaluation)
        """
        client, audit_log_path = client_with_audit
        
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={"X-API-Key": "test-secret"}
        )
        
        # Must NOT be 401 (should be 200 or other success code if gate/pipeline pass)
        assert response.status_code != 401, \
            f"Expected non-401, got {response.status_code}. Response: {response.text}"
        
        # Verify audit entry was logged
        assert audit_log_path.exists(), "Audit log file not created"
        
        # Read all lines and find gate decision (first line with "decision" field)
        with open(audit_log_path, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0, "Audit log is empty"
        
        # Parse lines and find gate decision (has "decision" field, not "status" field)
        gate_entry = None
        for line in lines:
            entry = json.loads(line.strip())
            if "decision" in entry and "status" not in entry:
                gate_entry = entry
                break
        
        assert gate_entry is not None, "Gate decision entry not found in audit log"
        
        # Audit entry should NOT contain AUTH_* reason codes (gate decision instead)
        reason_codes = gate_entry.get("reason_codes", [])
        assert "AUTH_MISSING_KEY" not in reason_codes, \
            f"Unexpected AUTH_MISSING_KEY in reason_codes: {reason_codes}"
        assert "AUTH_INVALID_KEY" not in reason_codes, \
            f"Unexpected AUTH_INVALID_KEY in reason_codes: {reason_codes}"
        
        # Verify trace_id exists
        assert "trace_id" in gate_entry, "Audit entry missing trace_id"
        assert gate_entry["trace_id"], "trace_id is empty"
        
        # Decision should be ALLOW or DENY (from gate)
        assert gate_entry["decision"] in ["ALLOW", "DENY"], \
            f"Expected decision from gate (ALLOW/DENY), got {gate_entry.get('decision')}"
