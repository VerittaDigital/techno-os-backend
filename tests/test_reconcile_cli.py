"""
Tests for RECONCILE CLI — Simple audit analysis entrypoint.

Testa:
- Output format com dados OK
- Output com ORPHAN_ALLOW
- Output com INCONSISTENT
- Exit codes (0 para clean, 1 para problemas)
- File not found
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from app.tools.reconcile_cli import main


def ts_utc(delta_s: int = 0) -> str:
    """Generate ISO 8601 timestamp at now + delta_s seconds."""
    now = datetime.now(timezone.utc)
    target = now + timedelta(seconds=delta_s)
    return target.isoformat(timespec='microseconds').replace('+00:00', 'Z')


class TestReconcileCliOutput:
    """Test CLI output and exit codes."""
    
    def test_cli_all_ok(self, tmp_path, monkeypatch, capsys):
        """CLI with all traces OK."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-001",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
            f.write(json.dumps({
                "event_type": "action_audit",
                "trace_id": "trace-001",
                "status": "SUCCESS",
                "ts_utc": ts_utc(5),
            }) + "\n")
        
        # Set env var and run main
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        exit_code = main()
        
        captured = capsys.readouterr()
        
        # Check exit code
        assert exit_code == 0
        
        # Check output contains summary
        assert "ORPHAN RECONCILER REPORT" in captured.out
        assert "Total traces:      1" in captured.out
        assert "✅ OK:              1" in captured.out
        assert "All traces healthy!" in captured.out
    
    def test_cli_with_orphan(self, tmp_path, monkeypatch, capsys):
        """CLI with ORPHAN_ALLOW."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-orphan-001",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
            # Add dummy event to push age > SLA
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-orphan-001",
                "ts_utc": ts_utc(50),
            }) + "\n")
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        monkeypatch.setenv("VERITTA_ORPHAN_SLA_S", "30")
        exit_code = main()
        
        captured = capsys.readouterr()
        
        # Check exit code (1 for problems)
        assert exit_code == 1
        
        # Check output contains orphan info
        assert "⚠️  ORPHAN_ALLOW:    1" in captured.out
        assert "🔴 ORPHAN_ALLOW" in captured.out
        assert "trace-orphan-001" in captured.out
    
    def test_cli_with_inconsistent(self, tmp_path, monkeypatch, capsys):
        """CLI with INCONSISTENT."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "action_audit",
                "trace_id": "trace-inconsistent-001",
                "status": "FAILED",
                "ts_utc": ts_utc(0),
            }) + "\n")
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        exit_code = main()
        
        captured = capsys.readouterr()
        
        # Check exit code
        assert exit_code == 1
        
        # Check output
        assert "🚨 INCONSISTENT:    1" in captured.out
        assert "🔶 INCONSISTENT" in captured.out
        assert "trace-inconsistent-001" in captured.out
    
    def test_cli_mixed_statuses(self, tmp_path, monkeypatch, capsys):
        """CLI with mixed OK, ORPHAN, and INCONSISTENT."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            # OK trace
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-ok-001",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
            f.write(json.dumps({
                "event_type": "action_audit",
                "trace_id": "trace-ok-001",
                "status": "SUCCESS",
                "ts_utc": ts_utc(5),
            }) + "\n")
            
            # Orphan trace
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-orphan-002",
                "decision": "ALLOW",
                "ts_utc": ts_utc(10),
            }) + "\n")
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-orphan-002",
                "ts_utc": ts_utc(60),
            }) + "\n")
            
            # Inconsistent trace
            f.write(json.dumps({
                "event_type": "action_audit",
                "trace_id": "trace-inconsistent-003",
                "status": "BLOCKED",
                "ts_utc": ts_utc(20),
            }) + "\n")
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        monkeypatch.setenv("VERITTA_ORPHAN_SLA_S", "30")
        exit_code = main()
        
        captured = capsys.readouterr()
        
        # Check exit code
        assert exit_code == 1
        
        # Check counts
        assert "Total traces:      3" in captured.out
        assert "✅ OK:              1" in captured.out
        assert "⚠️  ORPHAN_ALLOW:    1" in captured.out
        assert "🚨 INCONSISTENT:    1" in captured.out
        
        # Check non-OK section
        assert "⚠️  NON-OK TRACES" in captured.out
        assert "trace-orphan-002" in captured.out
        assert "trace-inconsistent-003" in captured.out
    
    def test_cli_file_not_found(self, tmp_path, monkeypatch, capsys):
        """CLI with missing audit.log."""
        missing_log = tmp_path / "missing.log"
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(missing_log))
        exit_code = main()
        
        captured = capsys.readouterr()
        
        # Should handle gracefully
        assert "File not found" in captured.out
        assert exit_code == 1
    
    def test_cli_empty_audit_log(self, tmp_path, monkeypatch, capsys):
        """CLI with empty audit.log."""
        audit_log = tmp_path / "audit.log"
        audit_log.write_text("")
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        exit_code = main()
        
        captured = capsys.readouterr()
        
        # Should handle gracefully
        assert "No traces found" in captured.out or "Total traces:      0" in captured.out
        assert exit_code == 0
    
    def test_cli_env_var_sla(self, tmp_path, monkeypatch, capsys):
        """CLI respects VERITTA_ORPHAN_SLA_S env var."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-tight-sla",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-tight-sla",
                "ts_utc": ts_utc(15),  # 15s > 10s SLA
            }) + "\n")
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        monkeypatch.setenv("VERITTA_ORPHAN_SLA_S", "10")  # Tight SLA
        exit_code = main()
        
        captured = capsys.readouterr()
        
        # With tight SLA, should be orphan
        assert "⚠️  ORPHAN_ALLOW:    1" in captured.out
        assert exit_code == 1


class TestReconcileCliIntegration:
    """Integration tests."""
    
    def test_cli_default_env_vars(self, tmp_path, monkeypatch, capsys):
        """CLI uses default env vars."""
        # Create audit.log in current directory for default lookup
        audit_log = Path("audit.log")
        
        # Only create if it doesn't exist to avoid contamination
        if not audit_log.exists():
            pytest.skip("audit.log exists in working directory (integration test skipped)")
        
        # Just verify it loads without crashing
        exit_code = main()
        
        captured = capsys.readouterr()
        assert "ORPHAN RECONCILER REPORT" in captured.out
    
    def test_cli_output_format(self, tmp_path, monkeypatch, capsys):
        """CLI output format is readable."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-ux-test",
                "decision": "DENY",
                "ts_utc": ts_utc(0),
            }) + "\n")
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        main()
        
        captured = capsys.readouterr()
        
        # Check for readable markers
        assert "📋" in captured.out or "REPORT" in captured.out
        assert "📊" in captured.out or "SUMMARY" in captured.out
        assert "━━" in captured.out or "Total" in captured.out
