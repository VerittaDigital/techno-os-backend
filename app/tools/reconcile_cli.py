"""
RECONCILE CLI — Simple entrypoint for offline audit analysis.

Usage:
    python -m app.tools.reconcile_cli
    
or:
    python app/tools/reconcile_cli.py

Environment variables:
    VERITTA_AUDIT_LOG_PATH: Path to audit.log (default: audit.log)
    VERITTA_ORPHAN_SLA_S: SLA in seconds (default: 30)

Output:
    Summary of trace statuses (OK, ORPHAN_ALLOW, INCONSISTENT)
    List of problematic trace_ids
"""

import os
import sys
from pathlib import Path

# Add parent directories to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tools.orphan_reconciler import analyze_audit_log


def main():
    """
    Run reconciliation and print summary report.
    """
    # Read environment variables
    audit_log_path = os.getenv("VERITTA_AUDIT_LOG_PATH", "audit.log")
    sla_s = int(os.getenv("VERITTA_ORPHAN_SLA_S", "30"))
    
    # Analyze
    print(f"📋 ORPHAN RECONCILER REPORT")
    print(f"📂 Audit log: {audit_log_path}")
    print(f"⏱️  SLA threshold: {sla_s}s")
    print()
    
    # Check if file exists
    if not Path(audit_log_path).exists():
        print(f"⚠️  File not found: {audit_log_path}")
        print(f"Status: NO DATA")
        return 1
    
    results = analyze_audit_log(audit_log_path=audit_log_path, sla_s=sla_s)
    
    if not results:
        print(f"No traces found in audit.log")
        return 0
    
    # Count by status
    status_counts = {}
    orphans = []
    inconsistent = []
    
    for result in results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if status == "ORPHAN_ALLOW":
            orphans.append(result["trace_id"])
        elif status == "INCONSISTENT":
            inconsistent.append(result["trace_id"])
    
    # Print summary
    print(f"📊 SUMMARY")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Total traces:      {len(results)}")
    print(f"✅ OK:              {status_counts.get('OK', 0)}")
    print(f"⚠️  ORPHAN_ALLOW:    {status_counts.get('ORPHAN_ALLOW', 0)}")
    print(f"🚨 INCONSISTENT:    {status_counts.get('INCONSISTENT', 0)}")
    print()
    
    # Print details of non-OK traces
    if orphans or inconsistent:
        print(f"⚠️  NON-OK TRACES")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if orphans:
            print(f"\n🔴 ORPHAN_ALLOW (ALLOW without final ActionResult):")
            for trace_id in orphans:
                matching = next((r for r in results if r["trace_id"] == trace_id), None)
                if matching:
                    age = matching.get("age_s")
                    age_str = f"{age:.1f}s" if age is not None else "unknown"
                    print(f"   • {trace_id} (age: {age_str})")
        
        if inconsistent:
            print(f"\n🔶 INCONSISTENT (ActionResult without decision):")
            for trace_id in inconsistent:
                print(f"   • {trace_id}")
        
        print()
        return 1  # Non-zero exit code if problems found
    
    print(f"✅ All traces healthy!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
