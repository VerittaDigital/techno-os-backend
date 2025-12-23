# Audit Log Specification (JSONL)

Append-only JSONL audit trail with cryptographic invariants.

## File Location

Environment variable: `VERITTA_AUDIT_LOG_PATH`

Default: `./audit.log`

Recommended production: Absolute path with log rotation.

## Format

Each line is a complete JSON object (JSONL):

```
{"event_type":"decision_audit","decision":"ALLOW",...}
{"event_type":"action_audit","status":"SUCCESS",...}
```

No partial records. Each write is atomic (fail-closed: exception propagates).

## Event Types

### 1. `decision_audit` — Gate Decision Record

Emitted by: `log_decision(DecisionRecord)`

Represents an authentication/authorization gate evaluation.

#### Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `event_type` | string | YES | Always `"decision_audit"` |
| `decision` | enum | YES | `"ALLOW"` \| `"DENY"` |
| `profile_id` | string | YES | Gate/phase ID (e.g., `"G2"`, `"F2.1"`) |
| `profile_hash` | string | YES | **Non-empty** SHA256 fingerprint (P1.1 invariant) |
| `matched_rules` | array | YES | Rules evaluated (even if denied) |
| `reason_codes` | array | YES | Stable codes; non-empty when decision=DENY |
| `input_digest` | string\|null | YES | SHA256 of canonical input or `null` (privacy-first) |
| `trace_id` | string | YES | UUID; matches HTTP response header |
| `ts_utc` | string | YES | ISO 8601 timestamp (UTC) |

#### Example (DENY)

```json
{
  "event_type": "decision_audit",
  "decision": "DENY",
  "profile_id": "G2",
  "profile_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "matched_rules": ["API key mismatch"],
  "reason_codes": ["G2_invalid_api_key"],
  "input_digest": null,
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts_utc": "2025-12-23T00:48:00.123456+00:00"
}
```

#### Example (ALLOW)

```json
{
  "event_type": "decision_audit",
  "decision": "ALLOW",
  "profile_id": "F2.1",
  "profile_hash": "a9993e364706816aba3e25717850c26c9cd0d89d",
  "matched_rules": ["API key valid", "Payload within limits", "Action allowed"],
  "reason_codes": [],
  "input_digest": "abcd1234...",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts_utc": "2025-12-23T00:48:00.123456+00:00"
}
```

### 2. `action_audit` — Execution Result Record

Emitted by: `log_action_result(ActionResult)`

Represents the outcome of pipeline execution.

#### Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `event_type` | string | YES | Always `"action_audit"` |
| `action` | string | YES | Action identifier (e.g., `"process"`) |
| `executor_id` | string | YES | Which executor ran (e.g., `"text_process_v1"`) |
| `executor_version` | string | YES | Immutable version of executor code |
| `status` | enum | YES | `"SUCCESS"` \| `"FAILED"` \| `"BLOCKED"` \| `"PENDING"` |
| `reason_codes` | array | YES | Non-empty when status ≠ SUCCESS |
| `input_digest` | string | YES | SHA256 of canonical input (never raw payload) |
| `output_digest` | string\|null | YES | SHA256 of output or `null` (privacy-first) |
| `trace_id` | string | YES | UUID; links to decision_audit |
| `ts_utc` | string | YES | ISO 8601 timestamp (UTC) |

#### Example (SUCCESS)

```json
{
  "event_type": "action_audit",
  "action": "process",
  "executor_id": "text_process_v1",
  "executor_version": "1.0.0",
  "status": "SUCCESS",
  "reason_codes": [],
  "input_digest": "abcd1234...",
  "output_digest": "efgh5678...",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts_utc": "2025-12-23T00:48:00.123456+00:00"
}
```

#### Example (BLOCKED)

```json
{
  "event_type": "action_audit",
  "action": "process",
  "executor_id": "unknown",
  "executor_version": "unknown",
  "status": "BLOCKED",
  "reason_codes": ["PROFILE_ACTION_MISMATCH"],
  "input_digest": "",
  "output_digest": null,
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts_utc": "2025-12-23T00:48:00.123456+00:00"
}
```

## Invariants

### DecisionRecord Invariants

1. **`profile_hash` never empty:**
   - If DecisionRecord created with `profile_hash=""`, audit sink replaces with `profiles_fingerprint_sha256()` (P1.1)
   - Offline tools can fingerprint and verify policy provenance

2. **`reason_codes` non-empty when DENY:**
   - DENY without reason codes is audit violation
   - Validator enforces in DecisionRecord.__init__

3. **`trace_id` always UUID:**
   - Validated format; links to HTTP response header `X-TRACE-ID`
   - Enables request → audit trail correlation

4. **`ts_utc` always UTC:**
   - Timezone-aware; allows chronological ordering across systems

### ActionResult Invariants

1. **`reason_codes` non-empty when status ≠ (SUCCESS | PENDING):**
   - FAILED/BLOCKED must explain why
   - Validator enforces in ActionResult.__init__

2. **`input_digest` always present:**
   - SHA256 of canonical input
   - Enables verification that executor processed expected input

3. **`output_digest` may be null:**
   - Privacy-by-design: non-serializable outputs → null
   - Never exposes raw execution results

## Privacy Constraints

All audit records MUST NOT contain:

- Raw request payloads
- Raw response/execution outputs
- API keys, tokens, credentials
- Personally identifiable information (PII)
- Stack traces
- Internal configuration details

**Approved fields:**

- Digests (SHA256 hex)
- Metadata (trace_id, ts_utc, action names)
- Stable reason codes
- Boolean flags (decision, status)

## Reading & Validation

### List Recent Records

```bash
# Windows (tail-like):
type audit.log | tail -n 10

# Linux:
tail -n 10 audit.log
```

### Pretty-Print (requires jq)

```bash
cat audit.log | jq .
```

### Verify Profile Hash Invariant (P1.1)

Check that no record has empty `profile_hash`:

```bash
# Should return no results (empty expected):
grep '"profile_hash":""' audit.log
grep '"profile_hash":null' audit.log
```

### Count by Event Type

```bash
# decision_audit count:
grep -c '"event_type":"decision_audit"' audit.log

# action_audit count:
grep -c '"event_type":"action_audit"' audit.log
```

### Filter by Reason Code

Find all DENY decisions with specific reason:

```bash
grep "P2_invalid_json" audit.log | jq .
```

## Integration with Monitoring

Use audit.log as input for:

- **SIEM systems:** Real-time anomaly detection
- **Compliance audits:** Offline trace verification
- **Debugging:** Correlate HTTP trace_id to full gate sequence
- **Performance analysis:** Compute decision latency from ts_utc

## Rotation & Retention

For production deployments:

1. **Log rotation:** Use logrotate (Linux) or Windows event log to manage size
2. **Retention policy:** Archive by date; minimum 90 days
3. **Offsite backup:** Copy to S3 or secure store for compliance

Example logrotate config:

```
/path/to/audit.log {
  daily
  rotate 90
  compress
  gzip
  missingok
  notifempty
}
```

## Offline Audit Tools

Use audit.log for:

```bash
# Aggregate by reason_code:
cat audit.log | jq -r '.reason_codes[]' | sort | uniq -c | sort -rn

# Find longest session (max ts_utc - min ts_utc):
cat audit.log | jq -s 'map(.ts_utc) | sort | .[0], .[-1]'

# Verify profile_hash is never empty:
cat audit.log | jq -c 'select(.profile_hash == "" or .profile_hash == null)' | wc -l
# Should output: 0
```
