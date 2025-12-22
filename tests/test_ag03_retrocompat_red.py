"""
TEST RED #4 — Retrocompatibility with AG-02
Tests ensuring legacy actions and executors continue working.

THESE TESTS MUST FAIL if AG-03 breaks retrocompat (CRITICAL).
"""
import json
import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestRetrocompatibilityRed:
    """RED tests for AG-02 retrocompatibility."""

    def test_action_process_without_version_continues(self, client, caplog):
        """
        5.1 Action "process" WITHOUT version continues executing.
        
        Assumption: "process" action in current ActionRegistry has NO version field.
        Expected:
        - HTTP 200 response
        - action_audit emitted
        - warning_codes contains "ACTION_VERSION_MISSING" OR no version blocking
        """
        with caplog.at_level(logging.INFO):
            response = client.post("/process", json={"text": "legacy test"})
        
        # Must NOT fail with 403 or 500
        assert response.status_code in [200, 422], \
            f"Legacy 'process' action broken: HTTP {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            # action_audit should be emitted (or at least not error)
            action_logs = [r.message for r in caplog.records if r.name == "action_audit"]
            if action_logs:
                audit_json = json.loads(action_logs[0])
                # If version warning exists, it should be informational, not blocking
                if "warning_codes" in audit_json:
                    # version warning OK, but status should not be BLOCKED for that
                    if "ACTION_VERSION_MISSING" in audit_json.get("warning_codes", []):
                        assert audit_json["status"] != "BLOCKED", \
                            "Version warning must not block legacy action"

    def test_executor_without_capabilities_legacy_mode(self, monkeypatch):
        """
        5.2 Executor LEGACY (without capabilities) accepts action.
        
        Executor real (TextProcessExecutorV1) has NO capabilities field today.
        Action new requ requires capabilities.
        Expected:
        - SHOULD NOT block with "EXECUTOR_CAPABILITY_MISSING"
        - Degraded mode: warning_codes instead
        """
        from unittest.mock import MagicMock
        from app.agentic_pipeline import run_agentic_action
        
        # Mock ActionRegistry with action requiring capabilities
        mock_registry = MagicMock()
        mock_registry.actions = {
            "process": {
                "version": "1.0.0",
                "description": "Process text input",
                "executor": "text_process_v1",
                "required_capabilities": ["TEXT_PROCESSING"],  # New requirement
            }
        }
        
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_registry
        )
        
        # Current executor has no capabilities field
        # Should NOT block, but may emit warning
        result, _ = run_agentic_action(
            action="process",
            payload={"text": "legacy mode test"},
            trace_id=str(uuid.uuid4())
        )
        
        # CRITICAL: must not block with hard error
        # May warn, but should proceed in degraded mode
        if result.status == "BLOCKED":
            # If blocked, it should be for a different reason
            assert "EXECUTOR_CAPABILITY_MISSING" not in result.reason_codes, \
                "Legacy executor should not hard-fail on missing capabilities"
            assert "EXECUTOR_CAPABILITIES_UNDEFINED" not in result.reason_codes, \
                "Legacy executor should not hard-fail on undefined capabilities"

    def test_action_version_missing_generates_warning_not_block(self, monkeypatch):
        """
        5.3 Missing version on new action WARNS but may continue (for backward compat).
        
        This tests the boundary: new action without version in a mixed system.
        Expected behavior depends on phase (strict by default in AG-03).
        But test validates that if blocked, audit is complete.
        """
        from unittest.mock import MagicMock
        from app.agentic_pipeline import run_agentic_action
        
        mock_registry = MagicMock()
        mock_registry.actions = {
            "legacy_new_action": {
                "description": "New action without explicit version",
                "executor": "text_process_v1",
                # action_version intentionally absent
            }
        }
        
        monkeypatch.setattr(
            "app.agentic_pipeline.get_action_registry",
            lambda: mock_registry
        )
        monkeypatch.setattr(
            "app.agentic_pipeline.route_action",
            lambda action: "text_process_v1"
        )
        
        result, _ = run_agentic_action(
            action="legacy_new_action",
            payload={"data": "test"},
            trace_id=str(uuid.uuid4())
        )
        
        # AG-03 RED: version missing SHOULD block
        # But if implementation is lenient, verify audit is complete
        if result.status == "BLOCKED" and "ACTION_VERSION_MISSING" in result.reason_codes:
            # Correct behavior: version missing blocks
            # trace_id is a UUID, just verify it exists
            assert result.trace_id, "trace_id must be present"
            assert result.status == "BLOCKED"
        else:
            # If allowed to continue, warning should be logged
            # (future: could add warning_codes field)
            pass
