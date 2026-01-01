"""Tests for profile-action mismatch in pipeline."""
import json
import uuid
from app.action_contracts import ActionResult


class TestProfileActionMismatchReason:
    """Test that PROFILE_ACTION_MISMATCH reason_code is generated."""

    def test_action_result_can_have_profile_action_mismatch_reason(self):
        """ActionResult must accept PROFILE_ACTION_MISMATCH reason_code."""
        from datetime import datetime, timezone
        
        result = ActionResult(
            action="process",
            executor_id="test",
            executor_version="1.0",
            status="BLOCKED",
            reason_codes=["PROFILE_ACTION_MISMATCH"],
            input_digest="abc",
            output_digest=None,
            trace_id=str(uuid.uuid4()),
            ts_utc=datetime.now(timezone.utc),
        )
        
        assert "PROFILE_ACTION_MISMATCH" in result.reason_codes
        assert result.status == "BLOCKED"

    def test_mismatch_appears_in_audit_log(self, caplog):
        """PROFILE_ACTION_MISMATCH must appear in action_audit log."""
        from datetime import datetime, timezone
        import logging
        
        with caplog.at_level(logging.INFO):
            result = ActionResult(
                action="process",
                executor_id="test",
                executor_version="1.0",
                status="BLOCKED",
                reason_codes=["PROFILE_ACTION_MISMATCH"],
                input_digest="abc",
                output_digest=None,
                trace_id=str(uuid.uuid4()),
                ts_utc=datetime.now(timezone.utc),
            )
            
            from app.action_audit_log import log_action_result
            log_action_result(result)
        
        audit_logs = [r.message for r in caplog.records if r.name == "action_audit"]
        assert len(audit_logs) > 0
        logged = json.loads(audit_logs[0])
        assert "PROFILE_ACTION_MISMATCH" in logged["reason_codes"]


class TestDriftDetection:
    """Test that registry changes trigger test failures (drift detection)."""

    def test_registry_fingerprint_can_detect_drift(self):
        """Fingerprint comparison must detect any registry change."""
        from app.action_registry import compute_registry_fingerprint, ActionRegistry
        
        registry_before = ActionRegistry(actions={"process": {"version": "1.0"}})
        fingerprint_before = compute_registry_fingerprint(registry_before)
        
        registry_after = ActionRegistry(actions={"process": {"version": "2.0"}})
        fingerprint_after = compute_registry_fingerprint(registry_after)
        
        assert fingerprint_before != fingerprint_after, "Drift not detected!"
