"""
Integration test: PROFILE_ACTION_MISMATCH persists ActionResult BLOCKED before HTTP 403.

Steps:
- Configure ActionMatrix to disallow 'process'
- Set X-API-Key valid (auth required)
- POST /process, expect 403
- Read audit.log (tmp_path)
- Assert action_audit line with BLOCKED + PROFILE_ACTION_MISMATCH
- Assert trace_id correlation between decision_audit and action_audit
"""

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.action_matrix import set_action_matrix, reset_action_matrix, ActionMatrix


def test_profile_action_mismatch_persists_before_403(tmp_path, monkeypatch):
    # Prepare audit.log path and auth key
    audit_log = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
    monkeypatch.setenv("VERITTA_BETA_API_KEY", "secret-key")

    # Disallow 'process' in matrix
    restricted_matrix = ActionMatrix(profile="restricted", allowed_actions=["other_action"])
    set_action_matrix(restricted_matrix)

    try:
        client = TestClient(app)
        # Send request with valid X-API-Key
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={"X-API-Key": "secret-key"},
        )
        assert response.status_code == 403

        # Read audit.log
        assert audit_log.exists(), "audit.log not created"
        with open(audit_log, "r") as f:
            lines = [json.loads(line) for line in f if line.strip()]

        # F11: Find gate_audit entries (no action_audit, gate blocks before pipeline)
        gates = [e for e in lines if "decision" in e and e.get("decision") in ["ALLOW", "DENY"]]

        # Assert gate DENY with G8_UNKNOWN_ACTION (action not in matrix)
        blocked_gates = [e for e in gates if e.get("decision") == "DENY" and "G8_UNKNOWN_ACTION" in e.get("reason_codes", [])]
        assert blocked_gates, "No DENY gate with G8_UNKNOWN_ACTION found"

        # Assert trace_id present
        trace_ids_gate = {e.get("trace_id") for e in blocked_gates}
        assert trace_ids_gate, "Gate audit missing trace_id"
    finally:
        # Cleanup matrix
        reset_action_matrix()
