"""
ORPHAN RECONCILER — Offline audit.log analysis tool.

Objetivo:
Detectar "ALLOW órfão" (gate ALLOW sem ActionResult final) no audit.log
e gerar um relatório determinístico.

Não importa Notion. Não faz chamadas externas. Funciona 100% offline.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional


# Environment variables
VERITTA_AUDIT_LOG_PATH = os.getenv("VERITTA_AUDIT_LOG_PATH", "audit.log")
VERITTA_ORPHAN_SLA_S = int(os.getenv("VERITTA_ORPHAN_SLA_S", "30"))


class OrphanReconciler:
    """
    Analyze audit.log for orphaned ALLOWs and inconsistencies.
    
    Workflow:
    1. Read audit.log (JSON lines)
    2. Group by trace_id
    3. Identify:
       - ALLOW without final ActionResult (ORPHAN_ALLOW)
       - ActionResult without ALLOW (INCONSISTENT)
       - Complete traces (OK)
    4. Calculate age_s from opened_ts_utc to last_ts_utc
    5. Mark as ORPHAN_ALLOW if age > SLA
    """
    
    def __init__(self, audit_log_path: str = VERITTA_AUDIT_LOG_PATH, sla_s: int = VERITTA_ORPHAN_SLA_S):
        """
        Initialize reconciler.
        
        Args:
            audit_log_path: Path to audit.log file (JSON lines)
            sla_s: SLA in seconds for orphan detection (default 30)
        """
        self.audit_log_path = audit_log_path
        self.sla_s = sla_s
        self.traces: Dict[str, dict] = {}  # trace_id → {opened_ts, events, etc}
    
    def load_audit_log(self) -> bool:
        """
        Load and parse audit.log.
        
        Returns:
            True if successful, False if file not found or empty.
        """
        path = Path(self.audit_log_path)
        
        if not path.exists():
            return False
        
        self.traces = {}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event = json.loads(line)
                        self._process_event(event)
                    except json.JSONDecodeError as e:
                        # Silently skip malformed lines (audit.log may have mixed content)
                        pass
        except Exception as e:
            # If file can't be read, return False
            return False
        
        return True
    
    def _process_event(self, event: dict) -> None:
        """
        Process a single audit event (JSON).
        
        Supported event types:
        - decision_audit: Gate decision (ALLOW/DENY)
        - action_audit: Action result (SUCCESS/FAILED/BLOCKED)
        """
        trace_id = event.get("trace_id")
        event_type = event.get("event_type")
        ts_utc = event.get("ts_utc")
        
        if not trace_id:
            return
        
        # Initialize trace entry if needed
        if trace_id not in self.traces:
            self.traces[trace_id] = {
                "trace_id": trace_id,
                "opened_ts_utc": ts_utc,
                "last_ts_utc": ts_utc,
                "decision": None,
                "action_result": None,
                "events": [],
            }
        
        # Update timestamps
        if ts_utc:
            if not self.traces[trace_id]["opened_ts_utc"]:
                self.traces[trace_id]["opened_ts_utc"] = ts_utc
            self.traces[trace_id]["last_ts_utc"] = ts_utc
        
        # Record event
        self.traces[trace_id]["events"].append({
            "event_type": event_type,
            "ts_utc": ts_utc,
            "decision": event.get("decision"),
            "status": event.get("status"),
        })
        
        # Extract decision and action result
        if event_type == "decision_audit":
            decision = event.get("decision")  # ALLOW, DENY, etc
            if decision:
                self.traces[trace_id]["decision"] = decision
        
        elif event_type == "action_audit":
            status = event.get("status")  # SUCCESS, FAILED, BLOCKED
            if status:
                self.traces[trace_id]["action_result"] = status
    
    def reconcile(self) -> List[Dict]:
        """
        Reconcile traces and identify orphans/inconsistencies.
        
        Returns:
            List of trace status dicts with fields:
            - trace_id
            - opened_ts_utc
            - last_ts_utc
            - age_s
            - status ("OK" | "ORPHAN_ALLOW" | "INCONSISTENT")
        """
        results = []
        
        for trace_id, trace_data in self.traces.items():
            result = {
                "trace_id": trace_id,
                "opened_ts_utc": trace_data["opened_ts_utc"],
                "last_ts_utc": trace_data["last_ts_utc"],
                "age_s": None,
                "status": "OK",
            }
            
            # Calculate age
            if trace_data["opened_ts_utc"] and trace_data["last_ts_utc"]:
                try:
                    opened = self._parse_ts(trace_data["opened_ts_utc"])
                    last = self._parse_ts(trace_data["last_ts_utc"])
                    age = (last - opened).total_seconds()
                    result["age_s"] = max(0, age)
                except (ValueError, TypeError):
                    result["age_s"] = None
            
            # Classify trace
            decision = trace_data["decision"]
            action_result = trace_data["action_result"]
            
            if decision == "DENY":
                # DENY traces are not orphans (no action expected)
                result["status"] = "OK"
            elif decision == "ALLOW":
                if action_result:
                    # ALLOW + ActionResult → OK
                    result["status"] = "OK"
                else:
                    # ALLOW without ActionResult → potential orphan
                    age_s = result.get("age_s")
                    if age_s is None:
                        # Inconclusive timestamp parsing → mark as INCONCLUSIVE
                        result["status"] = "INCONCLUSIVE"
                    elif age_s > self.sla_s:
                        result["status"] = "ORPHAN_ALLOW"
                    else:
                        # Still within SLA, mark as OK (may complete later)
                        result["status"] = "OK"
            elif action_result and not decision:
                # ActionResult without decision → inconsistent
                result["status"] = "INCONSISTENT"
            
            results.append(result)
        
        # Sort by trace_id for deterministic output
        results.sort(key=lambda x: x["trace_id"])
        return results
    
    @staticmethod
    def _parse_ts(ts_str: str) -> Optional[datetime]:
        """
        Parse ISO 8601 / RFC 3339 timestamp to datetime (UTC) using stdlib.

        Rules:
        - Accepts Z suffix and +/-HH:MM offsets
        - On failure, returns None (caller treats as INCONCLUSIVE)
        """
        if not ts_str:
            return None

        s = ts_str.strip()
        # Normalize Z to +00:00 for fromisoformat
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            return None

        # Ensure timezone-aware; if naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Return in UTC
        return dt.astimezone(timezone.utc)


def analyze_audit_log(
    audit_log_path: str = VERITTA_AUDIT_LOG_PATH,
    sla_s: int = VERITTA_ORPHAN_SLA_S,
) -> List[Dict]:
    """
    Analyze audit.log and return reconciliation report.
    
    Args:
        audit_log_path: Path to audit.log
        sla_s: SLA in seconds for orphan detection
    
    Returns:
        List of trace status dicts
    """
    reconciler = OrphanReconciler(audit_log_path=audit_log_path, sla_s=sla_s)
    reconciler.load_audit_log()
    return reconciler.reconcile()
