"""
RECONCILE CLI — Simple entrypoint for offline audit analysis.

Usage:
    python -m app.tools.reconcile_cli
    python app/tools/reconcile_cli.py
    python app/tools/reconcile_cli.py --plain
    
Environment variables:
    VERITTA_AUDIT_LOG_PATH: Path to audit.log (default: audit.log)
    VERITTA_ORPHAN_SLA_S: SLA in seconds (default: 30)

Output:
    Summary of trace statuses (OK, ORPHAN_ALLOW, INCONSISTENT)
    List of problematic trace_ids
    
    --plain: Text-only output (no emojis or decorative chars)
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directories to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tools.orphan_reconciler import analyze_audit_log


def _format_report(results, sla_s, audit_log_path, plain=False):
    """
    Format reconciliation report.
    
    Args:
        results: List of trace status dicts from reconcile()
        sla_s: SLA threshold in seconds
        audit_log_path: Path to audit log
        plain: If True, use text-only format (no emojis)
    
    Returns:
        Tuple of (formatted_output, should_exit_1)
    """
    lines = []
    
    # Header
    if plain:
        lines.append("ORPHAN RECONCILER REPORT")
        lines.append(f"Audit log: {audit_log_path}")
        lines.append(f"SLA threshold: {sla_s}s")
    else:
        lines.append("📋 ORPHAN RECONCILER REPORT")
        lines.append(f"📂 Audit log: {audit_log_path}")
        lines.append(f"⏱️  SLA threshold: {sla_s}s")
    
    lines.append("")
    
    if not results:
        lines.append("No traces found in audit.log")
        return "\n".join(lines), False
    
    # Count by status
    status_counts = {}
    orphans = []
    inconsistent = []
    inconclusive = []
    
    for result in results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if status == "ORPHAN_ALLOW":
            orphans.append(result)
        elif status == "INCONSISTENT":
            inconsistent.append(result)
        elif status == "INCONCLUSIVE":
            inconclusive.append(result)
    
    # Summary section
    if plain:
        lines.append("SUMMARY")
        lines.append("-" * 40)
    else:
        lines.append("📊 SUMMARY")
        lines.append("━" * 40)
    
    lines.append(f"Total traces:      {len(results)}")
    
    if plain:
        lines.append(f"OK:                {status_counts.get('OK', 0)}")
        lines.append(f"ORPHAN_ALLOW:      {status_counts.get('ORPHAN_ALLOW', 0)}")
        lines.append(f"INCONSISTENT:      {status_counts.get('INCONSISTENT', 0)}")
        lines.append(f"INCONCLUSIVE:      {status_counts.get('INCONCLUSIVE', 0)}")
    else:
        lines.append(f"✅ OK:              {status_counts.get('OK', 0)}")
        lines.append(f"⚠️  ORPHAN_ALLOW:    {status_counts.get('ORPHAN_ALLOW', 0)}")
        lines.append(f"🚨 INCONSISTENT:    {status_counts.get('INCONSISTENT', 0)}")
        lines.append(f"❔ INCONCLUSIVE:    {status_counts.get('INCONCLUSIVE', 0)}")
    
    lines.append("")
    
    # Non-OK traces section (only if there are issues)
    if orphans or inconsistent:
        if plain:
            lines.append("NON-OK TRACES")
            lines.append("-" * 40)
        else:
            lines.append("⚠️  NON-OK TRACES")
            lines.append("━" * 40)
        
        if orphans:
            if plain:
                lines.append("")
                lines.append("ORPHAN_ALLOW (ALLOW without final ActionResult):")
            else:
                lines.append("")
                lines.append("🔴 ORPHAN_ALLOW (ALLOW without final ActionResult):")
            
            for result in orphans:
                trace_id = result["trace_id"]
                age = result.get("age_s")
                age_str = f"{age:.1f}s" if age is not None else "unknown"
                lines.append(f"   • {trace_id} (age: {age_str})")
        
        if inconsistent:
            if plain:
                lines.append("")
                lines.append("INCONSISTENT (ActionResult without decision):")
            else:
                lines.append("")
                lines.append("🔶 INCONSISTENT (ActionResult without decision):")
            
            for result in inconsistent:
                trace_id = result["trace_id"]
                lines.append(f"   • {trace_id}")
        
        # Optional: list inconclusive in plain mode (operational visibility only)
        if plain and inconclusive:
            lines.append("")
            lines.append("INCONCLUSIVE (age unknown or unparsable):")
            for result in inconclusive:
                trace_id = result["trace_id"]
                age = result.get("age_s")
                age_str = "unknown" if age is None else f"{age:.1f}s"
                lines.append(f"   • {trace_id} (age: {age_str})")
        
        lines.append("")
        return "\n".join(lines), True  # Exit code 1 for problems
    
    # All healthy
    if plain:
        lines.append("All traces healthy!")
    else:
        lines.append("✅ All traces healthy!")
    
    return "\n".join(lines), False  # Exit code 0


def main():
    """
    Run reconciliation and print summary report.
    """
    parser = argparse.ArgumentParser(
        description="Analyze audit.log for orphaned ALLOW decisions"
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Text-only output (no emojis or decorative characters)"
    )
    args = parser.parse_args()
    
    # Read environment variables
    audit_log_path = os.getenv("VERITTA_AUDIT_LOG_PATH", "audit.log")
    sla_s = int(os.getenv("VERITTA_ORPHAN_SLA_S", "30"))
    
    # Check if file exists
    if not Path(audit_log_path).exists():
        if args.plain:
            print(f"File not found: {audit_log_path}")
            print(f"Status: NO DATA")
        else:
            print(f"⚠️  File not found: {audit_log_path}")
            print(f"Status: NO DATA")
        return 1
    
    # Analyze
    results = analyze_audit_log(audit_log_path=audit_log_path, sla_s=sla_s)
    
    # Format and print
    output, should_exit_1 = _format_report(results, sla_s, audit_log_path, plain=args.plain)
    print(output)
    
    return 1 if should_exit_1 else 0


if __name__ == "__main__":
    sys.exit(main())
