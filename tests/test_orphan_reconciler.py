"""
Tests for ORPHAN RECONCILER — audit.log offline analysis.

Casos:
1. ALLOW + SUCCESS => OK
2. ALLOW sozinho, age > SLA => ORPHAN_ALLOW
3. ActionResult sem ALLOW => INCONSISTENT
4. DENY (com ou sem ActionResult) => OK
5. Múltiplos traces concorrentes
"""

import json
from datetime import datetime, timedelta, timezone


from app.tools.orphan_reconciler import OrphanReconciler, analyze_audit_log


def ts_utc(delta_s: int = 0) -> str:
    """
    Generate ISO 8601 timestamp at now + delta_s seconds.
    """
    now = datetime.now(timezone.utc)
    target = now + timedelta(seconds=delta_s)
    return target.isoformat(timespec='microseconds').replace('+00:00', 'Z')


class TestOrphanReconcilerBasics:
    """Basic functionality tests."""
    
    def test_allow_with_success_is_ok(self, tmp_path):
        """ALLOW + SUCCESS => OK."""
        audit_log = tmp_path / "audit.log"
        
        trace_id = "trace-001"
        base_ts = ts_utc(0)
        success_ts = ts_utc(5)
        
        # Write audit events
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id,
                "decision": "ALLOW",
                "ts_utc": base_ts,
            }) + "\n")
            f.write(json.dumps({
                "event_type": "action_audit",
                "trace_id": trace_id,
                "status": "SUCCESS",
                "ts_utc": success_ts,
            }) + "\n")
        
        # Reconcile
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert len(results) == 1
        assert results[0]["trace_id"] == trace_id
        assert results[0]["status"] == "OK"
    
    def test_allow_without_action_within_sla_is_ok(self, tmp_path):
        """ALLOW without ActionResult, age < SLA => OK."""
        audit_log = tmp_path / "audit.log"
        
        trace_id = "trace-002"
        ts = ts_utc(0)
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id,
                "decision": "ALLOW",
                "ts_utc": ts,
            }) + "\n")
        
        # Reconcile with 30s SLA (age is ~0)
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert len(results) == 1
        assert results[0]["status"] == "OK"  # Still within SLA
    
    def test_allow_without_action_exceeds_sla_is_orphan(self, tmp_path):
        """ALLOW without ActionResult, age > SLA => ORPHAN_ALLOW."""
        audit_log = tmp_path / "audit.log"
        
        trace_id = "trace-003"
        opened_ts = ts_utc(0)
        last_ts = ts_utc(45)  # 45 seconds later
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id,
                "decision": "ALLOW",
                "ts_utc": opened_ts,
            }) + "\n")
            # Add a dummy event to update last_ts_utc
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id,
                "ts_utc": last_ts,
            }) + "\n")
        
        # Reconcile with 30s SLA (age is ~45s > 30s)
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert len(results) == 1
        assert results[0]["status"] == "ORPHAN_ALLOW"
        assert results[0]["age_s"] > 30
    
    def test_action_result_without_allow_is_inconsistent(self, tmp_path):
        """ActionResult without ALLOW => INCONSISTENT."""
        audit_log = tmp_path / "audit.log"
        
        trace_id = "trace-004"
        ts = ts_utc(0)
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "action_audit",
                "trace_id": trace_id,
                "status": "SUCCESS",
                "ts_utc": ts,
            }) + "\n")
        
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert len(results) == 1
        assert results[0]["status"] == "INCONSISTENT"
    
    def test_deny_with_or_without_action_is_ok(self, tmp_path):
        """DENY (with or without ActionResult) => OK."""
        audit_log = tmp_path / "audit.log"
        
        # Trace 1: DENY only
        trace_id_1 = "trace-deny-001"
        ts = ts_utc(0)
        
        # Trace 2: DENY + ActionResult
        trace_id_2 = "trace-deny-002"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id_1,
                "decision": "DENY",
                "ts_utc": ts,
            }) + "\n")
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id_2,
                "decision": "DENY",
                "ts_utc": ts,
            }) + "\n")
            f.write(json.dumps({
                "event_type": "action_audit",
                "trace_id": trace_id_2,
                "status": "BLOCKED",
                "ts_utc": ts_utc(5),
            }) + "\n")
        
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert len(results) == 2
        for r in results:
            assert r["status"] == "OK"
    
    def test_file_not_found_returns_empty(self, tmp_path):
        """Non-existent file returns empty results."""
        missing_log = tmp_path / "missing.log"
        
        reconciler = OrphanReconciler(audit_log_path=str(missing_log), sla_s=30)
        result = reconciler.load_audit_log()
        
        assert result is False
        assert len(reconciler.reconcile()) == 0
    
    def test_multiple_concurrent_traces(self, tmp_path):
        """Multiple traces with mixed statuses."""
        audit_log = tmp_path / "audit.log"
        
        traces = {
            "trace-ok-001": {"decision": "ALLOW", "action": "SUCCESS"},
            "trace-orphan-002": {"decision": "ALLOW", "action": None},
            "trace-deny-003": {"decision": "DENY", "action": None},
            "trace-inconsistent-004": {"decision": None, "action": "FAILED"},
        }
        
        with open(audit_log, 'w') as f:
            for trace_id, spec in traces.items():
                opened_ts = ts_utc(0)
                
                # Decision event
                if spec["decision"]:
                    f.write(json.dumps({
                        "event_type": "decision_audit",
                        "trace_id": trace_id,
                        "decision": spec["decision"],
                        "ts_utc": opened_ts,
                    }) + "\n")
                
                # Action event (if exists)
                if spec["action"]:
                    action_ts = ts_utc(50) if "orphan" in trace_id else ts_utc(5)
                    f.write(json.dumps({
                        "event_type": "action_audit",
                        "trace_id": trace_id,
                        "status": spec["action"],
                        "ts_utc": action_ts,
                    }) + "\n")
                else:
                    # For orphan, add dummy event to push age > SLA
                    if "orphan" in trace_id:
                        f.write(json.dumps({
                            "event_type": "action_audit",
                            "trace_id": trace_id,
                            "ts_utc": ts_utc(50),
                        }) + "\n")
        
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert len(results) == 4
        
        # Check statuses
        status_by_id = {r["trace_id"]: r["status"] for r in results}
        assert status_by_id["trace-ok-001"] == "OK"
        assert status_by_id["trace-orphan-002"] == "ORPHAN_ALLOW"
        assert status_by_id["trace-deny-003"] == "OK"
        assert status_by_id["trace-inconsistent-004"] == "INCONSISTENT"


class TestOrphanReconcilerEdgeCases:
    """Edge cases and boundary conditions."""
    
    def test_empty_audit_log(self, tmp_path):
        """Empty file returns empty results."""
        audit_log = tmp_path / "audit.log"
        audit_log.write_text("")
        
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert len(results) == 0
    
    def test_malformed_json_lines_skipped(self, tmp_path):
        """Malformed JSON lines are skipped gracefully."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write("{ invalid json }\n")
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-001",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
            f.write("not json at all\n")
        
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        result = reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert result is True
        assert len(results) == 1  # Only valid event processed
    
    def test_missing_trace_id_ignored(self, tmp_path):
        """Events without trace_id are ignored."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-001",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
        
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert len(results) == 1
        assert results[0]["trace_id"] == "trace-001"
    
    def test_sla_boundary(self, tmp_path):
        """Test SLA boundary (at and just beyond threshold)."""
        audit_log = tmp_path / "audit.log"
        
        # Case 1: Just within SLA (29.9s)
        trace_id_within = "trace-sla-within"
        opened_ts_within = ts_utc(0)
        last_ts_within = ts_utc(29.9)
        
        # Case 2: Just beyond SLA (30.1s)
        trace_id_beyond = "trace-sla-beyond"
        opened_ts_beyond = ts_utc(100)
        last_ts_beyond = ts_utc(130.2)
        
        with open(audit_log, 'w') as f:
            # Within SLA
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id_within,
                "decision": "ALLOW",
                "ts_utc": opened_ts_within,
            }) + "\n")
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id_within,
                "ts_utc": last_ts_within,
            }) + "\n")
            
            # Beyond SLA
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id_beyond,
                "decision": "ALLOW",
                "ts_utc": opened_ts_beyond,
            }) + "\n")
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": trace_id_beyond,
                "ts_utc": last_ts_beyond,
            }) + "\n")
        
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        assert len(results) == 2
        status_by_id = {r["trace_id"]: r["status"] for r in results}
        
        # Within SLA → OK
        assert status_by_id[trace_id_within] == "OK"
        # Beyond SLA → ORPHAN_ALLOW
        assert status_by_id[trace_id_beyond] == "ORPHAN_ALLOW"
    
    def test_analyze_audit_log_function(self, tmp_path):
        """Test convenience function analyze_audit_log()."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-001",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
        
        results = analyze_audit_log(audit_log_path=str(audit_log), sla_s=30)
        
        assert len(results) == 1
        assert results[0]["trace_id"] == "trace-001"
    
    def test_deterministic_output_order(self, tmp_path):
        """Results are sorted by trace_id (deterministic)."""
        audit_log = tmp_path / "audit.log"
        
        trace_ids = ["trace-zzz", "trace-aaa", "trace-mmm"]
        
        with open(audit_log, 'w') as f:
            for trace_id in trace_ids:
                f.write(json.dumps({
                    "event_type": "decision_audit",
                    "trace_id": trace_id,
                    "decision": "ALLOW",
                    "ts_utc": ts_utc(0),
                }) + "\n")
        
        reconciler = OrphanReconciler(audit_log_path=str(audit_log), sla_s=30)
        reconciler.load_audit_log()
        results = reconciler.reconcile()
        
        result_ids = [r["trace_id"] for r in results]
        expected = sorted(trace_ids)
        assert result_ids == expected
