"""
TEST RED #5 — Audit Integrity & Trace ID Preservation
Tests ensuring AG-03 version/capability checks preserve audit trail.

THESE TESTS MUST FAIL (AG-03 logic not implemented yet).
"""
import json
import uuid
import logging
import pytest
from unittest.mock import MagicMock
from app.agentic_pipeline import run_agentic_action


@pytest.fixture
def caplog_configured(caplog):
    """Configure caplog to capture audit loggers."""
    with caplog.at_level(logging.INFO):
        yield caplog


class TestAg03AuditIntegrityRed:
    """RED tests for audit preservation in AG-03 checks."""

    def test_capability_mismatch_preserves_auditability(
        self, monkeypatch, caplog_configured
    ):
        """
        6.1 Capability mismatch preserves auditability.
        
        Gate allows, pipeline checks capabilities and blocks.
        Expected:
        - action_audit emitted (BEFORE any HTTP exception)
        - action_audit.status == "BLOCKED"
        - reason_codes contains mismatch
        - trace_id preserved
        """
        from unittest.mock import MagicMock
        
        mock_registry = MagicMock()
        mock_registry.actions = {
            "audit_cap_action": {
                "description": "Action requiring IMAGE_PROCESSING",
                "executor": "audit_test_executor",
                "action_version": "1.0.0",
                "required_capabilities": ["IMAGE_PROCESSING"],
            }
        }
        
        mock_executor = MagicMock()
        mock_executor.executor_id = "audit_test_executor"
        mock_executor.version = "1.0.0"
        mock_executor.capabilities = ["TEXT_PROCESSING"]  # Missing IMAGE
        mock_executor.limits = MagicMock()
        mock_executor.limits.max_payload_bytes = 10_000
        mock_executor.limits.max_depth = 10
        mock_executor.limits.max_list_items = 100
        
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_registry
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "audit_test_executor"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor
        )
        
        result, _ = run_agentic_action(
            action="audit_cap_action",
            payload={"data": "audit test"},
            trace_id=str(uuid.uuid4())
        )
        
        # Must block with capability mismatch
        assert result.status == "BLOCKED"
        assert "EXECUTOR_CAPABILITY_MISMATCH" in result.reason_codes
        
        # action_audit MUST be emitted
        action_logs = [
            (r.getMessage() if hasattr(r, 'getMessage') else r.message)
            for r in caplog_configured.records
            if "action_audit" in r.name or "action_audit" in (r.getMessage() if hasattr(r, 'getMessage') else r.message)
        ]
        assert len(action_logs) > 0, "action_audit MUST be emitted on capability mismatch"
        
        audit_json = json.loads(action_logs[0])
        assert audit_json["status"] == "BLOCKED"
        assert "EXECUTOR_CAPABILITY_MISMATCH" in audit_json["reason_codes"]
        # trace_id is UUID, verify it exists
        assert "trace_id" in audit_json and audit_json["trace_id"]

    def test_version_mismatch_preserves_auditability(
        self, monkeypatch, caplog_configured
    ):
        """
        6.2 Version mismatch preserves auditability.
        
        Gate allows, pipeline checks executor version and blocks.
        Expected:
        - action_audit emitted (BEFORE any HTTP exception)
        - action_audit.status == "BLOCKED"
        - reason_codes contains version mismatch
        - trace_id preserved
        """
        from unittest.mock import MagicMock
        
        mock_registry = MagicMock()
        mock_registry.actions = {
            "audit_ver_action": {
                "description": "Action requiring executor >= 1.5.0",
                "executor": "audit_test_executor_v",
                "action_version": "1.0.0",
                "required_capabilities": [],
                "min_executor_version": "1.5.0",
            }
        }
        
        mock_executor = MagicMock()
        mock_executor.executor_id = "audit_test_executor_v"
        mock_executor.version = "1.0.0"  # Too old
        mock_executor.capabilities = []
        mock_executor.limits = MagicMock()
        mock_executor.limits.max_payload_bytes = 10_000
        mock_executor.limits.max_depth = 10
        mock_executor.limits.max_list_items = 100
        
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_registry
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "audit_test_executor_v"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor
        )
        
        result, _ = run_agentic_action(
            action="audit_ver_action",
            payload={"data": "audit test"},
            trace_id=str(uuid.uuid4())
        )
        
        # Must block with version incompatibility
        assert result.status == "BLOCKED"
        assert "EXECUTOR_VERSION_INCOMPATIBLE" in result.reason_codes
        
        # action_audit MUST be emitted
        action_logs = [
            (r.getMessage() if hasattr(r, 'getMessage') else r.message)
            for r in caplog_configured.records
            if "action_audit" in r.name or "action_audit" in (r.getMessage() if hasattr(r, 'getMessage') else r.message)
        ]
        assert len(action_logs) > 0, "action_audit MUST be emitted on version mismatch"
        
        audit_json = json.loads(action_logs[0])
        assert audit_json["status"] == "BLOCKED"
        assert "EXECUTOR_VERSION_INCOMPATIBLE" in audit_json["reason_codes"]
        # trace_id is UUID, verify it exists
        assert "trace_id" in audit_json and audit_json["trace_id"]

    def test_trace_id_correlation_across_audits(
        self, monkeypatch, caplog_configured
    ):
        """
        6.3 trace_id must be identical across gate_audit and action_audit.
        
        Even when action is blocked in pipeline, trace_id must match.
        Expected:
        - gate_audit.trace_id == action_audit.trace_id
        """
        from unittest.mock import MagicMock
        
        mock_registry = MagicMock()
        mock_registry.actions = {
            "audit_trace_action": {
                "description": "Action for trace test",
                "executor": "audit_trace_executor",
                "action_version": "1.0.0",
                "required_capabilities": ["MISSING_CAP"],  # Will block
            }
        }
        
        mock_executor = MagicMock()
        mock_executor.executor_id = "audit_trace_executor"
        mock_executor.version = "1.0.0"
        mock_executor.capabilities = []  # Missing required capability
        mock_executor.limits = MagicMock()
        mock_executor.limits.max_payload_bytes = 10_000
        mock_executor.limits.max_depth = 10
        mock_executor.limits.max_list_items = 100
        
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_registry
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "audit_trace_executor"
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.get_executor",
            lambda executor_id: mock_executor
        )
        
        trace_id = str(uuid.uuid4())
        result, _ = run_agentic_action(
            action="audit_trace_action",
            payload={"data": "trace test"},
            trace_id=trace_id
        )
        
        # Extract audit logs
        action_logs = [
            (r.getMessage() if hasattr(r, 'getMessage') else r.message)
            for r in caplog_configured.records
            if "action_audit" in r.name or "action_audit" in (r.getMessage() if hasattr(r, 'getMessage') else r.message)
        ]
        assert len(action_logs) > 0, "action_audit must be emitted"
        
        action_audit = json.loads(action_logs[0])
        
        # trace_id must match (correlation across gate_audit and action_audit)
        assert action_audit["trace_id"] == trace_id, \
            f"trace_id mismatch: action_audit={action_audit['trace_id']} vs result={result.trace_id}"
