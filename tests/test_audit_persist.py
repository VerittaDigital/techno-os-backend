"""
Tests for P1-AUDIT-PERSIST: audit file sink (JSONL, fail-closed).

Verify:
- Successful audit writes to JSONL file
- File format is valid JSONL (one JSON per line)
- Audit contains expected fields (trace_id, decision/status, etc.)

Note: Fail-closed behavior (audit failure -> BLOCKED) is already tested in:
  - tests/test_audit_fail_closed.py
  - tests/test_concurrency_request_flow_p1_6_aggressive.py
"""

import json
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_audit_file(monkeypatch, tmp_path):
    """
    Fixture: TestClient with VERITTA_AUDIT_LOG_PATH set to temp file.
    Also set VERITTA_BETA_API_KEY for auth.
    """
    audit_file = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_file))
    monkeypatch.setenv("VERITTA_BETA_API_KEY", "test-key")
    
    from app.main import app
    return TestClient(app), audit_file


class TestAuditPersist:
    """Test suite for P1-AUDIT-PERSIST (file sink, append-only JSONL)."""

    def test_audit_persist_success_writes_jsonl(self, client_with_audit_file):
        """
        Successful request writes audit to JSONL file.
        
        Scenario:
        - VERITTA_AUDIT_LOG_PATH set to temp file
        - POST /process with valid payload and auth
        - Expected: audit.log created with at least one JSON line containing trace_id
        """
        client, audit_file = client_with_audit_file
        
        # Make request (should trigger gate_audit + action_audit)
        response = client.post(
            "/process",
            json={"text": "audit persist test"},
            headers={"X-API-Key": "test-key"}
        )
        
        # Request should succeed (not blocked by audit)
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        # Verify audit file was created
        assert audit_file.exists(), \
            f"Audit file {audit_file} was not created"
        
        # Read audit file lines
        lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
        
        # Should have at least one line (gate_audit and/or action_audit)
        assert len(lines) >= 1, \
            f"Expected at least 1 audit line, got {len(lines)}"
        
        # Verify first line is valid JSON and contains trace_id
        first_line = lines[0]
        audit_record = json.loads(first_line)
        
        assert "trace_id" in audit_record, \
            f"Audit record missing trace_id: {audit_record}"
        
        # Verify trace_id matches response
        response_data = response.json()
        assert audit_record["trace_id"] == response_data["trace_id"], \
            f"Audit trace_id mismatch: {audit_record['trace_id']} != {response_data['trace_id']}"
        
        # Verify all lines are valid JSON (JSONL format)
        for i, line in enumerate(lines):
            try:
                record = json.loads(line)
                assert isinstance(record, dict), \
                    f"Line {i+1} is not a JSON object: {line}"
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {i+1} is not valid JSON: {line}. Error: {e}")

    def test_audit_persist_failure_blocks(self, monkeypatch, tmp_path):
        """
        Audit write failure results in fail-closed behavior.
        
        Scenario:
        - VERITTA_AUDIT_LOG_PATH set to invalid path (non-existent directory)
        - POST /process with valid payload and auth
        - Expected: Gate audit fails -> exception raised by TestClient
        
        This test verifies that audit persistence failures trigger fail-closed behavior
        at the gate level (FastAPI dependency), preventing silent failures.
        
        Note: TestClient raises the exception directly since it's an unhandled dependency error.
        In production with a real HTTP client, this would manifest as HTTP 500.
        """
        # Set invalid audit path (directory doesn't exist, cannot be created)
        invalid_path = tmp_path / "no_such_dir" / "audit.log"
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(invalid_path))
        monkeypatch.setenv("VERITTA_BETA_API_KEY", "test-key")
        
        from app.main import app
        from app.audit_log import AuditLogError
        client = TestClient(app)
        
        # Make request (gate audit write will fail)
        # TestClient raises the exception directly (fail-closed verified)
        with pytest.raises(AuditLogError) as exc_info:
            response = client.post(
                "/process",
                json={"text": "audit fail test"},
                headers={"X-API-Key": "test-key"}
            )
        
        # Verify exception message contains trace_id and file error
        assert "Failed to log gate decision" in str(exc_info.value)
        assert "No such file or directory" in str(exc_info.value)
