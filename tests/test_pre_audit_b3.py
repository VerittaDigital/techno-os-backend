"""Test pre-audit logging before executor execution (B3 blocker fix)."""
from unittest.mock import MagicMock
import uuid

from app.agentic_pipeline import run_agentic_action


class TestPreAuditLogging:
    """Verify pre-audit logs are emitted before executor.execute() runs."""

    def test_pre_audit_logged_before_execution(self, monkeypatch):
        """Verify ActionResult with status=PENDING is logged before execute()."""
        logged_results = []

        def mock_log(result):
            logged_results.append(result)

        # Mock log_action_result to capture what gets logged
        monkeypatch.setattr("app.agentic_pipeline.log_action_result", mock_log)

        # Create a simple action via action_matrix
        from app.action_matrix import set_action_matrix, ActionMatrix

        set_action_matrix(ActionMatrix(
            profile="default",
            allowed_actions=["test_action"]
        ))

        # Mock action registry

        mock_registry = MagicMock()
        mock_registry.actions = {
            "test_action": {
                "description": "Test",
                "executor": "text_process_v1",
                "action_version": "1.0.0",
                "required_capabilities": [],
            }
        }
        monkeypatch.setattr("app.agentic_pipeline.get_action_registry", lambda: mock_registry)

        # Run action
        result, output = run_agentic_action(
            action="test_action",
            payload={"text": "hello"},
            trace_id=str(uuid.uuid4()),
            executor_id="text_process_v1",
        )

        # Verify:
        # 1. At least 2 logs: PRE-AUDIT (PENDING) + POST-AUDIT (SUCCESS/FAILED/BLOCKED)
        assert len(logged_results) >= 2, f"Expected at least 2 audit logs, got {len(logged_results)}"

        # 2. First log should be status=PENDING with EXECUTION_ATTEMPT marker
        pre_audit = logged_results[0]
        assert pre_audit.status == "PENDING", f"First log should be PENDING, got {pre_audit.status}"
        assert "EXECUTION_ATTEMPT" in pre_audit.reason_codes, \
            f"First log should have EXECUTION_ATTEMPT marker, got {pre_audit.reason_codes}"

        # 3. Final log should be the actual result
        final_result = logged_results[-1]
        assert final_result.status in ("SUCCESS", "FAILED", "BLOCKED"), \
            f"Final log should be SUCCESS/FAILED/BLOCKED, got {final_result.status}"
        # trace_id is a UUID generated, just verify it exists
        assert final_result.trace_id

    def test_pre_audit_logged_even_on_executor_exception(self, monkeypatch):
        """Verify pre-audit is logged even if executor.execute() throws exception."""
        logged_results = []

        def mock_log(result):
            logged_results.append(result)

        monkeypatch.setattr("app.agentic_pipeline.log_action_result", mock_log)

        # Mock executor that raises exception
        def mock_executor_execute(req):
            raise ValueError("Simulated executor error")

        mock_executor = MagicMock()
        mock_executor.executor_id = "failing_executor"
        mock_executor.version = "1.0.0"
        mock_executor.capabilities = ["TEST"]
        mock_executor.limits = MagicMock()
        mock_executor.limits.max_payload_bytes = 1_000_000
        mock_executor.limits.max_depth = 10
        mock_executor.limits.max_list_items = 100
        mock_executor.execute = mock_executor_execute

        def mock_get_executor(executor_id):
            return mock_executor

        monkeypatch.setattr("app.agentic_pipeline.get_executor", mock_get_executor)

        # Mock action registry
        mock_registry = MagicMock()
        mock_registry.actions = {
            "failing_test": {
                "description": "Test",
                "executor": "failing_executor",
                "action_version": "1.0.0",
                "required_capabilities": ["TEST"],
            }
        }
        monkeypatch.setattr("app.agentic_pipeline.get_action_registry", lambda: mock_registry)

        # Mock action matrix
        from app.action_matrix import set_action_matrix, ActionMatrix
        set_action_matrix(ActionMatrix(
            profile="default",
            allowed_actions=["failing_test"]
        ))

        # Run action (will fail)
        result, output = run_agentic_action(
            action="failing_test",
            payload={"text": "test"},
            trace_id=str(uuid.uuid4()),
            executor_id="failing_executor",
        )

        # Verify pre-audit was logged BEFORE exception was caught
        assert len(logged_results) >= 2, f"Expected at least 2 audit logs, got {len(logged_results)}"
        
        pre_audit = logged_results[0]
        assert pre_audit.status == "PENDING"
        assert "EXECUTION_ATTEMPT" in pre_audit.reason_codes

        # Final result should be FAILED (exception caught)
        final = logged_results[-1]
        assert final.status == "FAILED"

