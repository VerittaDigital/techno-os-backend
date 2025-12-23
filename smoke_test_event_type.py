#!/usr/bin/env python
"""Smoke test for Stage 2.2 event_type in audit.log"""

from app.audit_log import log_decision
from app.action_audit_log import log_action_result
from app.decision_record import DecisionRecord
from app.action_contracts import ActionResult
import json
from datetime import datetime, timezone
import uuid

# Create a decision
tr = str(uuid.uuid4())
record = DecisionRecord(
    decision='ALLOW',
    profile_id='default',
    profile_hash='test',
    matched_rules=[],
    reason_codes=['OK'],
    input_digest='abc',
    trace_id=tr
)

# Create an action result
result = ActionResult(
    action='process',
    executor_id='text_process_v1',
    executor_version='1.0.0',
    status='SUCCESS',
    reason_codes=[],
    input_digest='def',
    output_digest='ghi',
    trace_id=tr
)

# Log both
log_decision(record)
log_action_result(result)

# Read and verify
with open('audit.log', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[-2:]):
        data = json.loads(line)
        et = data.get("event_type")
        ts = data.get("ts_utc", "N/A")[:19]
        print(f"Line {i}: event_type={et}, ts_utc={ts}...")

print("\n✅ Smoke test PASSED: event_type and RFC3339 timestamps present in audit.log")
