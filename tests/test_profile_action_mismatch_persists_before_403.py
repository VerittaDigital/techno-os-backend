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

        # Find decision and action events
        decisions = [e for e in lines if e.get("event_type") == "decision_audit"]
        actions = [e for e in lines if e.get("event_type") == "action_audit"]

        # Assert blocked action present with mismatch reason
        blocked = [e for e in actions if e.get("status") == "BLOCKED" and "PROFILE_ACTION_MISMATCH" in e.get("reason_codes", [])]
        assert blocked, "No BLOCKED ActionResult with PROFILE_ACTION_MISMATCH found"

        # Assert trace_id correlation: decision and action share same trace_id
        trace_ids_decision = {e.get("trace_id") for e in decisions}
        trace_ids_action = {e.get("trace_id") for e in blocked}
        assert trace_ids_decision & trace_ids_action, "Trace ID not correlated between decision and action"
    finally:
        # Cleanup matrix
        reset_action_matrix()
