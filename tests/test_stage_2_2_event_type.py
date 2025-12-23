"""
Stage 2.2 Tests — Event Type Discrimination in Audit Log.

Validates:
- P2.2-A: decision_audit events have event_type field
- P2.2-A: action_audit events have event_type field
- P2.2-C: PROFILE_ACTION_MISMATCH generates BLOCKED ActionResult with event_type
- P2.2-D: RFC3339 timestamps (+00:00, -03:00, Z) are parsed correctly
- P2.2-D: Reconciler detects ORPHAN_ALLOW with real audit.log format
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from app.decision_record import DecisionRecord
from app.action_contracts import ActionResult
from app.audit_log import log_decision
from app.action_audit_log import log_action_result
from app.tools.orphan_reconciler import OrphanReconciler


class TestEventTypeInDecisionAudit:
    """Test P2.2-A: decision_audit includes event_type."""
    
    def test_decision_audit_has_event_type(self, tmp_path, monkeypatch):
        """DecisionRecord persisted includes event_type: decision_audit."""
        audit_log = tmp_path / "audit.log"
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        
        record = DecisionRecord(
            decision="ALLOW",
            profile_id="default",
            profile_hash="abc123",
            matched_rules=[],
            reason_codes=["OK"],
            input_digest="def456",
            trace_id="550e8400-e29b-41d4-a716-446655440000",
        )
        
        log_decision(record)
        
        # Read audit.log line
        with open(audit_log, 'r') as f:
            line = f.readline()
            data = json.loads(line)
        
        # Assert event_type present and correct
        assert "event_type" in data
        assert data["event_type"] == "decision_audit"
        assert data["decision"] == "ALLOW"
        assert data["trace_id"] == "550e8400-e29b-41d4-a716-446655440000"


class TestEventTypeInActionAudit:
    """Test P2.2-A: action_audit includes event_type."""
    
    def test_action_audit_has_event_type(self, tmp_path, monkeypatch):
        """ActionResult persisted includes event_type: action_audit."""
        audit_log = tmp_path / "audit.log"
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        
        result = ActionResult(
            action="process",
            executor_id="text_process_v1",
            executor_version="1.0.0",
            status="SUCCESS",
            reason_codes=[],
            input_digest="xyz789",
            output_digest="uvw123",
            trace_id="660f9500-f39c-52e5-b826-557766551111",
        )
        
        log_action_result(result)
        
        # Read audit.log line
        with open(audit_log, 'r') as f:
            line = f.readline()
            data = json.loads(line)
        
        # Assert event_type present and correct
        assert "event_type" in data
        assert data["event_type"] == "action_audit"
        assert data["status"] == "SUCCESS"
        assert data["trace_id"] == "660f9500-f39c-52e5-b826-557766551111"


class TestProfileActionMismatchPersisted:
    """Test P2.2-C: PROFILE_ACTION_MISMATCH generates BLOCKED ActionResult."""
    
    def test_mismatch_blocked_in_audit_log(self, client, tmp_path, monkeypatch):
        """HTTP 403 mismatch generates ActionResult BLOCKED in audit.log."""
        from app.action_matrix import set_action_matrix, reset_action_matrix, ActionMatrix
        
        audit_log = tmp_path / "audit.log"
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        
        # Set action matrix without "process" action
        restricted_matrix = ActionMatrix(profile="restricted", allowed_actions=["other_action"])
        set_action_matrix(restricted_matrix)
        
        try:
            # Use client fixture from conftest (has authenticated_request with valid auth)
            response = client.authenticated_request(
                "POST",
                "/process",
                json={"text": "test"},
            )
            
            # Assert 403: policy mismatch (auth is guaranteed valid by fixture)
            assert response.status_code == 403, \
                f"Expected 403 (policy mismatch), got {response.status_code}: {response.json()}"
            
            # Read audit.log for ActionResult with PROFILE_ACTION_MISMATCH
            with open(audit_log, 'r') as f:
                lines = f.readlines()
            
            # Find action_audit entry with PROFILE_ACTION_MISMATCH
            found = False
            for line in lines:
                data = json.loads(line)
                if data.get("event_type") == "action_audit" and "PROFILE_ACTION_MISMATCH" in data.get("reason_codes", []):
                    found = True
                    assert data["status"] == "BLOCKED"
                    assert data["action"] == "process"
                    break
            
            assert found, "PROFILE_ACTION_MISMATCH ActionResult not found in audit.log"
        finally:
            reset_action_matrix()


class TestRFC3339TimestampParsing:
    """Test P2.2-D: RFC3339 offset timestamps (+00:00, -03:00) are parsed."""
    
    def test_parse_ts_with_plus_offset(self):
        """_parse_ts handles +HH:MM timezone offset."""
        from app.tools.orphan_reconciler import OrphanReconciler
        
        ts_str = "2025-12-22T15:30:45.123456+00:00"
        dt = OrphanReconciler._parse_ts(ts_str)
        
        assert dt is not None
        assert dt.tzinfo == timezone.utc
        # Check the parsed time is correct (15:30:45 UTC)
        assert dt.hour == 15
        assert dt.minute == 30
    
    def test_parse_ts_with_minus_offset(self):
        """_parse_ts handles -HH:MM timezone offset."""
        from app.tools.orphan_reconciler import OrphanReconciler
        
        # 13:30:45-03:00 = 16:30:45 UTC
        ts_str = "2025-12-22T13:30:45.123456-03:00"
        dt = OrphanReconciler._parse_ts(ts_str)
        
        assert dt is not None
        assert dt.tzinfo == timezone.utc
        # After conversion to UTC
        assert dt.hour == 16
        assert dt.minute == 30
    
    def test_parse_ts_with_z_suffix(self):
        """_parse_ts handles Z timezone suffix."""
        from app.tools.orphan_reconciler import OrphanReconciler
        
        ts_str = "2025-12-22T15:30:45.123456Z"
        dt = OrphanReconciler._parse_ts(ts_str)
        
        assert dt is not None
        assert dt.tzinfo == timezone.utc
        assert dt.hour == 15
        assert dt.minute == 30


class TestReconcileWithRealFormat:
    """Test P2.2-D: Reconciler detects ORPHAN_ALLOW with real audit.log format (with event_type)."""
    
    def test_reconcile_detects_orphan_with_event_type(self, tmp_path):
        """Reconciler detects ORPHAN_ALLOW when audit.log has event_type and RFC3339 timestamps."""
        audit_log = tmp_path / "audit.log"
        
        # Create audit.log with real format (event_type + RFC3339 timestamps)
        now_utc = datetime.now(timezone.utc)
        ts_decision = now_utc.isoformat()  # Pydantic emits +00:00
        ts_action = (now_utc + timedelta(seconds=50)).isoformat()  # After SLA
        
        with open(audit_log, 'w') as f:
            # Write decision_audit
            f.write(json.dumps({
                "event_type": "decision_audit",
                "decision": "ALLOW",
                "profile_id": "default",
                "profile_hash": "hash123",
                "matched_rules": [],
                "reason_codes": ["OK"],
                "input_digest": "digest123",
                "trace_id": "770g0600-g40d-63f6-c937-668877662222",
                "ts_utc": ts_decision,
            }) + "\n")
            
            # Write a dummy event (not another decision, to leave orphan)
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "770g0600-g40d-63f6-c937-668877662222",
                "ts_utc": ts_action,
            }) + "\n")
        
        # Reconcile with SLA 30s
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        # Find orphan result
        orphan = [r for r in results if r["trace_id"] == "770g0600-g40d-63f6-c937-668877662222"]
        assert len(orphan) == 1
        assert orphan[0]["status"] == "ORPHAN_ALLOW"
        assert orphan[0]["age_s"] is not None
        assert orphan[0]["age_s"] > 30
