import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.action_audit_log import log_action_result
from app.audit_log import log_decision
from app.decision_record import DecisionRecord
from app.action_contracts import ActionResult
from app.tools.orphan_reconciler import analyze_audit_log, OrphanReconciler
from app.main import app
from app.action_matrix import set_action_matrix, reset_action_matrix, ActionMatrix


def _write_jsonl(path: Path, obj: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def test_audit_lines_include_event_type(tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_path))

    # Fixed timestamps for determinism
    ts_decision = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    ts_action = datetime(2025, 1, 1, 0, 0, 5, tzinfo=timezone.utc)

    trace_id = "00000000-0000-4000-8000-000000000001"

    decision = DecisionRecord(
        trace_id=trace_id,
        decision="ALLOW",
        reason_codes=[],
        profile_id="default",
        profile_hash="hash",
        matched_rules=["r1"],
        input_digest="id1",
        ts_utc=ts_decision,
    )
    log_decision(decision)

    action = ActionResult(
        action="process",
        executor_id="exec",
        executor_version="1.0.0",
        status="SUCCESS",
        reason_codes=[],
        input_digest="id1",
        output_digest="od1",
        trace_id=trace_id,
        ts_utc=ts_action,
    )
    log_action_result(action)

    assert audit_path.exists()
    with open(audit_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    event_types = {line.get("event_type") for line in lines}
    assert "decision_audit" in event_types
    assert "action_audit" in event_types


def test_reconcile_detects_orphan_allow_with_real_format(tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_path))

    # ALLOW decision with two timestamps to exceed SLA=30s and no action_audit
    _write_jsonl(
        audit_path,
        {
            "event_type": "decision_audit",
            "trace_id": "trace-orphan",
            "decision": "ALLOW",
            "ts_utc": "2025-01-01T00:00:00Z",
        },
    )
    _write_jsonl(
        audit_path,
        {
            "event_type": "decision_audit",
            "trace_id": "trace-orphan",
            "decision": "ALLOW",
            "ts_utc": "2025-01-01T00:01:00Z",
        },
    )

    results = analyze_audit_log(audit_log_path=str(audit_path), sla_s=30)
    statuses = {r["trace_id"]: r["status"] for r in results}
    assert statuses.get("trace-orphan") == "ORPHAN_ALLOW"


def test_reconcile_detects_inconsistent_with_real_format(tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_path))

    _write_jsonl(
        audit_path,
        {
            "event_type": "action_audit",
            "trace_id": "trace-inconsistent",
            "status": "SUCCESS",
            "ts_utc": "2025-01-01T00:00:10Z",
        },
    )

    results = analyze_audit_log(audit_log_path=str(audit_path), sla_s=30)
    statuses = {r["trace_id"]: r["status"] for r in results}
    assert statuses.get("trace-inconsistent") == "INCONSISTENT"


def test_parse_ts_accepts_rfc3339_offset():
    dt_z = OrphanReconciler._parse_ts("2025-12-22T15:30:45Z")
    dt_plus = OrphanReconciler._parse_ts("2025-12-22T15:30:45+00:00")
    dt_minus = OrphanReconciler._parse_ts("2025-12-22T12:30:45-03:00")

    assert dt_z == dt_plus
    assert dt_z == dt_minus
    assert dt_z.tzinfo is not None
    assert dt_z.utcoffset() == timedelta(0)


def test_profile_action_mismatch_persists_action_before_403(tmp_path, monkeypatch):
    audit_log = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
    monkeypatch.setenv("VERITTA_BETA_API_KEY", "secret-key")

    restricted_matrix = ActionMatrix(profile="restricted", allowed_actions=["other_action"])
    set_action_matrix(restricted_matrix)

    try:
        client = TestClient(app)
        response = client.post(
            "/process",
            json={"text": "hello"},
            headers={"X-API-Key": "secret-key"},
        )
        assert response.status_code == 403

        assert audit_log.exists(), "audit.log not created"
        with open(audit_log, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]

        # F11: Find gate_audit DENY (no action_audit, gate blocks before pipeline)
        gates = [e for e in lines if "decision" in e and e.get("decision") in ["ALLOW", "DENY"]]

        blocked_gates = [e for e in gates if e.get("decision") == "DENY" and "G8_UNKNOWN_ACTION" in e.get("reason_codes", [])]
        assert blocked_gates, "No DENY gate with G8_UNKNOWN_ACTION found"

        trace_ids_gate = {e.get("trace_id") for e in blocked_gates}
        assert trace_ids_gate, "Gate audit missing trace_id"
    finally:
        reset_action_matrix()
