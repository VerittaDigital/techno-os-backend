# Error Envelope Specification

Canonical error response contract for all Techno OS Backend endpoints.

## Motivation

Human-in-the-loop requires:
- **Clarity:** Error reasons are explicit, not cryptic
- **Auditability:** Every error is logged with full context
- **Privacy:** No sensitive data in error responses
- **Stability:** Client can build robust integrations

## Response Format

All error responses follow this envelope:

```json
{
  "status_code": 400,
  "reason_codes": ["VALIDATION_ERROR"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Request validation failed",
  "details": null
}
```

## Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status_code` | integer | YES | HTTP status code (200-599) |
| `reason_codes` | array[string] | YES | Machine-readable error codes; non-empty |
| `trace_id` | string | YES | UUID for log correlation |
| `message` | string | YES | Human-readable summary (max 200 chars) |
| `details` | object\|null | YES | Structured details (privacy-filtered) or null |

### Rule: reason_codes is Always Non-Empty

**NEVER** return `reason_codes: []` in an error response.

Each error status must include at least one stable, predictable reason code.

---

## Standard HTTP Status Codes & Reason Codes

### 400 Bad Request

**When:** Request structure or validation failed (recoverable).

#### Cause: Missing/Invalid Header

```json
{
  "status_code": 400,
  "reason_codes": ["MISSING_API_KEY"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Missing required header: X-API-Key",
  "details": {
    "header": "X-API-Key"
  }
}
```

#### Cause: Invalid JSON Body

```json
{
  "status_code": 400,
  "reason_codes": ["INVALID_JSON"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Request body is not valid JSON",
  "details": {
    "line": 5,
    "char": 12,
    "context": "unexpected token }"
  }
}
```

#### Cause: Pydantic Validation Error

```json
{
  "status_code": 400,
  "reason_codes": ["VALIDATION_ERROR"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Request validation failed",
  "details": {
    "field": "action",
    "constraint": "type",
    "expected": "string",
    "got": "int"
  }
}
```

#### Cause: Payload Too Large

```json
{
  "status_code": 400,
  "reason_codes": ["PAYLOAD_TOO_LARGE"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Request payload exceeds maximum size (8KB)",
  "details": {
    "limit_bytes": 8192,
    "received_bytes": 12456
  }
}
```

---

### 403 Forbidden

**When:** Authentication/authorization gate denied access.

#### Cause: Invalid API Key

```json
{
  "status_code": 403,
  "reason_codes": ["GATE_DENIED_INVALID_API_KEY"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Authentication failed",
  "details": null
}
```

#### Cause: Gate Decision Denied

```json
{
  "status_code": 403,
  "reason_codes": ["G2_INVALID_INPUT", "F2_PROFILE_VIOLATION"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Request denied by governance gate",
  "details": {
    "gate_id": "G2",
    "matched_rules": ["API key mismatch", "Action not allowed"]
  }
}
```

---

### 404 Not Found

**When:** Resource does not exist.

#### Cause: Unknown Action

```json
{
  "status_code": 404,
  "reason_codes": ["ACTION_NOT_FOUND"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Action 'invalid_action' not registered",
  "details": {
    "action": "invalid_action",
    "available_actions": ["process", "analyze", "validate"]
  }
}
```

---

### 429 Too Many Requests

**When:** Rate limit exceeded.

```json
{
  "status_code": 429,
  "reason_codes": ["RATE_LIMIT_EXCEEDED"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Rate limit exceeded: 100 requests per minute",
  "details": {
    "limit": 100,
    "window_seconds": 60,
    "reset_after_seconds": 12
  }
}
```

---

### 500 Internal Server Error

**When:** Unrecoverable server fault.

#### Cause: Executor Timeout

```json
{
  "status_code": 500,
  "reason_codes": ["EXECUTOR_TIMEOUT"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Action execution timed out (10s)",
  "details": {
    "timeout_seconds": 10,
    "executor_id": "text_process_v1"
  }
}
```

#### Cause: Executor Crash

```json
{
  "status_code": 500,
  "reason_codes": ["EXECUTOR_FAILED"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Action execution failed",
  "details": {
    "executor_id": "text_process_v1",
    "executor_version": "1.0.0"
  }
}
```

#### Cause: Audit Sink Write Failure

```json
{
  "status_code": 500,
  "reason_codes": ["AUDIT_SINK_FAILED"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Failed to write audit record",
  "details": null
}
```

---

### 503 Service Unavailable

**When:** Dependency (LLM, storage) is offline.

```json
{
  "status_code": 503,
  "reason_codes": ["LLM_PROVIDER_UNAVAILABLE"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "LLM provider is unreachable",
  "details": {
    "provider": "openai",
    "retry_after_seconds": 60
  }
}
```

---

## Privacy Rules (LGPD by Design)

### MUST NOT include in `details`:
- Raw request/response payloads
- Stack traces or source code paths
- Internal IP addresses or hostnames
- Database connection strings
- API keys or secrets
- PII (names, emails, addresses, phone numbers)
- Sensitive business logic

### MAY include in `details`:
- Field names (sanitized)
- Type mismatches (`expected: string, got: int`)
- Numeric limits (`limit_bytes: 8192`)
- Enumerated options (`available_actions: [...]`)
- Metadata (gate ID, executor version, retry hints)

---

## Client Integration Patterns

### 1. Retry Logic

```python
import time
import requests

def call_api_with_retry(endpoint, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            resp = requests.post(endpoint, json=payload)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            error = e.response.json()
            
            # Extract reason codes
            reason_codes = error.get("reason_codes", [])
            
            # Determine if retriable
            retriable = any(code in reason_codes for code in [
                "RATE_LIMIT_EXCEEDED",
                "EXECUTOR_TIMEOUT",
                "LLM_PROVIDER_UNAVAILABLE"
            ])
            
            if retriable and attempt < max_retries - 1:
                # Extract retry_after from details if available
                retry_after = error.get("details", {}).get("retry_after_seconds", 2 ** attempt)
                time.sleep(retry_after)
                continue
            else:
                # Non-retriable or max retries reached
                trace_id = error.get("trace_id")
                print(f"Request failed (trace: {trace_id})")
                print(f"Reasons: {', '.join(reason_codes)}")
                raise
```

### 2. Error Aggregation

```python
# Collect all reason codes from a session
errors = []

for payload in payloads:
    try:
        response = call_api(payload)
    except requests.exceptions.HTTPError as e:
        error_envelope = e.response.json()
        errors.append({
            "trace_id": error_envelope["trace_id"],
            "reason_codes": error_envelope["reason_codes"],
            "status_code": error_envelope["status_code"]
        })

# Analyze patterns
error_codes_count = {}
for error in errors:
    for code in error["reason_codes"]:
        error_codes_count[code] = error_codes_count.get(code, 0) + 1

print("Error distribution:", error_codes_count)
```

### 3. Trace Correlation

```python
# Link error response to audit log
error_envelope = e.response.json()
trace_id = error_envelope["trace_id"]

# Search audit.log for this trace_id
import subprocess
result = subprocess.run(
    f'grep "{trace_id}" audit.log | jq .',
    shell=True,
    capture_output=True,
    text=True
)
print(result.stdout)  # Full audit trail for request
```

---

## Implementation Checklist

- [ ] All error responses use this envelope format
- [ ] `reason_codes` is **never** empty
- [ ] HTTP status code matches semantic meaning (no 200 with error)
- [ ] `trace_id` is UUID and matches `X-TRACE-ID` header
- [ ] `message` is human-readable (max 200 chars)
- [ ] `details` contains only privacy-safe metadata
- [ ] No stack traces, paths, or secrets in any field
- [ ] Errors logged to `audit.log` with full context
- [ ] Tests verify error envelope structure (pydantic model)
- [ ] Documentation lists all possible `reason_codes`
