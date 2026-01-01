"""Audit log parser for admin summary (streaming, no explosion)."""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path


class AuditParser:
    """
    Parse audit.log (JSONL) with streaming to avoid memory issues.
    
    Limits:
    - Default: 24h OR 10,000 events (whichever is smaller)
    - Customizable via query params: days (1–7), limit (max 50,000)
    """
    
    @staticmethod
    def summarize(
        days: int = 1,
        limit: int = 10000,
        event_type: Optional[str] = None,  # None = all, else "decision_audit" or "action_audit"
    ) -> Dict[str, Any]:
        """
        Read audit.log and aggregate summary statistics.
        
        Args:
            days: Look back N days (default 1, max 7)
            limit: Max events to process (default 10k, max 50k)
            event_type: Filter by type (optional)
        
        Returns:
            Summary dict with aggregations
        """
        # Validate inputs
        days = min(max(days, 1), 7)  # Clamp to 1–7
        limit = min(max(limit, 100), 50000)  # Clamp to 100–50k
        
        audit_log_path = os.getenv("VERITTA_AUDIT_LOG_PATH", "./audit.log")
        
        if not Path(audit_log_path).exists():
            return {
                "window": {"days": days, "limit": limit},
                "decisions": {"allow": 0, "deny": 0},
                "deny_breakdown": {},
                "events_by_type": {"decision_audit": 0, "action_audit": 0},
                "ts_utc": datetime.now(timezone.utc).isoformat(),
                "note": "Audit log not found",
            }
        
        cutoff_time = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).replace(tzinfo=None)
        
        # Aggregate counters
        allow_count = 0
        deny_count = 0
        deny_breakdown: Dict[str, int] = {}
        events_by_type: Dict[str, int] = {"decision_audit": 0, "action_audit": 0}
        
        events_processed = 0
        parse_errors = 0
        
        # Stream parse (line by line)
        try:
            with open(audit_log_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if events_processed >= limit:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        parse_errors += 1
                        continue
                    
                    # Check timestamp
                    ts_str = event.get("ts_utc")
                    if not ts_str:
                        continue
                    
                    try:
                        # Parse ISO format timestamp
                        ts = datetime.fromisoformat(ts_str.replace("+00:00", ""))
                        if ts < cutoff_time:
                            continue  # Outside window
                    except (ValueError, AttributeError):
                        parse_errors += 1
                        continue
                    
                    # Filter by event type if specified
                    evt_type = event.get("event_type")
                    if event_type and evt_type != event_type:
                        continue
                    
                    events_processed += 1
                    
                    # Aggregate decision_audit
                    if evt_type == "decision_audit":
                        events_by_type["decision_audit"] += 1
                        decision = event.get("decision")
                        if decision == "ALLOW":
                            allow_count += 1
                        elif decision == "DENY":
                            deny_count += 1
                            # Breakdown by reason_code
                            reason_codes = event.get("reason_codes", [])
                            for code in reason_codes:
                                deny_breakdown[code] = deny_breakdown.get(code, 0) + 1
                    
                    # Aggregate action_audit
                    elif evt_type == "action_audit":
                        events_by_type["action_audit"] += 1
        
        except OSError as e:
            # File read error
            parse_errors += 1
        
        return {
            "window": {"days": days, "limit": limit},
            "decisions": {"allow": allow_count, "deny": deny_count},
            "deny_breakdown": deny_breakdown,
            "events_by_type": events_by_type,
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "events_processed": events_processed,
            "parse_errors": parse_errors,
        }
