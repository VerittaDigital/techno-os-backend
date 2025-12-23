"""
Tests for RECONCILE CLI — Simple audit analysis entrypoint.

Testa:
- Output format com dados OK
- Output com ORPHAN_ALLOW
- Output com INCONSISTENT
- Exit codes (0 para clean, 1 para problemas)
- File not found
- --plain mode (text-only, sem emojis)
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from app.tools.reconcile_cli import main, _format_report


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
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py"])
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
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py"])
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
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py"])
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
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py"])
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
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py"])
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
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py"])
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
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py"])
        exit_code = main()
        
        captured = capsys.readouterr()
        
        # With tight SLA, should be orphan
        assert "⚠️  ORPHAN_ALLOW:    1" in captured.out
        assert exit_code == 1


class TestReconcileCliIntegration:
    """Integration tests."""
    
    def test_cli_default_env_vars(self, tmp_path, monkeypatch, capsys):
        """CLI uses default env vars via tmp_path setup (robust to environment)."""
        # Create a minimal audit.log in tmp_path
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-default-test",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
            f.write(json.dumps({
                "event_type": "action_audit",
                "trace_id": "trace-default-test",
                "status": "SUCCESS",
                "ts_utc": ts_utc(1),
            }) + "\n")
        
        # Set environment to use tmp_path audit log
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py"])
        exit_code = main()
        
        captured = capsys.readouterr()
        # Verify reconciler executed successfully
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}. Output: {captured.out}"
        
        # Canonical output assertion: check for ORPHAN header or trace count
        import re
        has_orphan = "ORPHAN" in captured.out.upper()
        has_traces = re.search(r"Total\s+traces\s*:\s*\d+", captured.out, re.IGNORECASE) is not None
        assert has_orphan or has_traces, \
            f"CLI output missing ORPHAN header or trace count. Got: {captured.out}"
    
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
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py"])
        main()
        
        captured = capsys.readouterr()
        
        # Check for readable markers
        assert "📋" in captured.out or "REPORT" in captured.out
        assert "📊" in captured.out or "SUMMARY" in captured.out
        assert "━━" in captured.out or "Total" in captured.out


class TestReconcileCliPlainMode:
    """Tests for --plain text-only output mode."""
    
    def test_plain_mode_no_emojis(self, tmp_path, monkeypatch, capsys):
        """--plain mode removes all emojis."""
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
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py", "--plain"])
        main()
        
        captured = capsys.readouterr()
        
        # Check for emojis NOT present
        assert "📋" not in captured.out
        assert "📂" not in captured.out
        assert "⏱️" not in captured.out
        assert "📊" not in captured.out
        assert "✅" not in captured.out
        assert "⚠️" not in captured.out
        assert "🚨" not in captured.out
        assert "🔴" not in captured.out
        assert "🔶" not in captured.out
        
        # Check for text present
        assert "ORPHAN RECONCILER REPORT" in captured.out
        assert "SUMMARY" in captured.out
        assert "Total traces:" in captured.out
        assert "OK:" in captured.out
    
    def test_plain_mode_uses_dashes(self, tmp_path, monkeypatch, capsys):
        """--plain mode uses dashes instead of box drawing."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-001",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py", "--plain"])
        main()
        
        captured = capsys.readouterr()
        
        # Check dashes instead of box drawing
        assert "--------" in captured.out
        # Should NOT have box drawing chars
        assert "━" not in captured.out
    
    def test_plain_mode_with_orphan(self, tmp_path, monkeypatch, capsys):
        """--plain mode with ORPHAN_ALLOW."""
        audit_log = tmp_path / "audit.log"
        
        with open(audit_log, 'w') as f:
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-orphan-001",
                "decision": "ALLOW",
                "ts_utc": ts_utc(0),
            }) + "\n")
            f.write(json.dumps({
                "event_type": "decision_audit",
                "trace_id": "trace-orphan-001",
                "ts_utc": ts_utc(50),
            }) + "\n")
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        monkeypatch.setenv("VERITTA_ORPHAN_SLA_S", "30")
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py", "--plain"])
        exit_code = main()
        
        captured = capsys.readouterr()
        
        assert exit_code == 1
        # Check no emojis
        assert "🔴" not in captured.out
        assert "🔶" not in captured.out
        # Check content still present
        assert "ORPHAN_ALLOW" in captured.out
        assert "trace-orphan-001" in captured.out
        assert "age:" in captured.out
    
    def test_plain_mode_all_ok(self, tmp_path, monkeypatch, capsys):
        """--plain mode with all OK."""
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
        
        monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_log))
        monkeypatch.setattr("sys.argv", ["reconcile_cli.py", "--plain"])
        exit_code = main()
        
        captured = capsys.readouterr()
        
        assert exit_code == 0
        assert "All traces healthy!" in captured.out
        # Should NOT contain emoji checkmark
        assert "✅ All" not in captured.out
        # Should contain plain text
        assert "All traces healthy!" in captured.out


class TestFormatReportFunction:
    """Unit tests for _format_report function."""
    
    def test_format_report_with_emoji(self):
        """_format_report with emoji mode."""
        results = [
            {
                "trace_id": "trace-001",
                "opened_ts_utc": "2025-12-22T12:00:00Z",
                "last_ts_utc": "2025-12-22T12:00:05Z",
                "age_s": 5.0,
                "status": "OK",
            }
        ]
        
        output, exit_1 = _format_report(results, 30, "audit.log", plain=False)
        
        assert "📋" in output
        assert "📊" in output
        assert "✅ OK" in output
        assert exit_1 is False
    
    def test_format_report_plain_text(self):
        """_format_report with plain text mode."""
        results = [
            {
                "trace_id": "trace-001",
                "opened_ts_utc": "2025-12-22T12:00:00Z",
                "last_ts_utc": "2025-12-22T12:00:05Z",
                "age_s": 5.0,
                "status": "OK",
            }
        ]
        
        output, exit_1 = _format_report(results, 30, "audit.log", plain=True)
        
        # Check no emojis
        assert "📋" not in output
        assert "📊" not in output
        assert "✅" not in output
        # Check dashes
        assert "--------" in output
        # Check content
        assert "ORPHAN RECONCILER REPORT" in output
        assert "OK:" in output
        assert exit_1 is False
    
    def test_format_report_orphan_in_plain(self):
        """_format_report with orphan in plain mode."""
        results = [
            {
                "trace_id": "trace-orphan",
                "opened_ts_utc": "2025-12-22T12:00:00Z",
                "last_ts_utc": "2025-12-22T12:01:00Z",
                "age_s": 60.0,
                "status": "ORPHAN_ALLOW",
            }
        ]
        
        output, exit_1 = _format_report(results, 30, "audit.log", plain=True)
        
        # Check no emojis
        assert "🔴" not in output
        # Check content
        assert "ORPHAN_ALLOW" in output
        assert "trace-orphan" in output
        assert "age: 60.0s" in output
        assert exit_1 is True
