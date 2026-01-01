import json
from pathlib import Path

import importlib


def write_jsonl(path: Path, obj: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def test_reconcile_cli_reports_inconclusive_in_summary(tmp_path, monkeypatch, capsys):
    # Prepare a temporary audit.log with one ALLOW decision and no timestamp
    audit_path = tmp_path / "audit.log"

    # decision_audit ALLOW without ts_utc to force age_s=None → INCONCLUSIVE
    write_jsonl(
        audit_path,
        {
            "event_type": "decision_audit",
            "trace_id": "trace-inconclusive-1",
            "decision": "ALLOW",
            # intentionally no ts_utc
        },
    )

    # Point CLI to our temp audit.log and use plain output
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_path))
    monkeypatch.setenv("VERITTA_ORPHAN_SLA_S", "30")

    # Reload module to ensure a clean import context
    module = importlib.import_module("app.tools.reconcile_cli")

    # Simulate CLI arguments
    monkeypatch.setenv("PYTHONWARNINGS", "ignore")
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    monkeypatch.setenv("LC_ALL", "C")

    # Set argv for --plain
    monkeypatch.setattr("sys.argv", ["reconcile_cli", "--plain"])

    # Run CLI main
    exit_code = module.main()

    # Capture output
    out = capsys.readouterr().out

    # Summary should include INCONCLUSIVE: 1 and exit code should be 0
    assert exit_code == 0
    assert "INCONCLUSIVE:" in out
    assert "INCONCLUSIVE:      1" in out
    assert "Total traces:      1" in out
