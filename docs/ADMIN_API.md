# Admin API Documentation (TASK A2)

**Status:** ✅ COMPLETE  
**Component:** Techno OS Backend Admin Interface  
**Governance:** Fail-closed, audit-trail-first, human-in-the-loop  

---

## Overview

The Admin API provides minimal, secure, and governed access to:

- 🔐 **Session Management** — Revoke sessions with explicit human control
- 📊 **Audit Summary** — Read-only aggregations of decision_audit and action_audit events
- 🏥 **Health Check** — Verify database and audit sink connectivity
- 📍 **Session Lookup** — Query session metadata (without secrets)

All operations are **fail-closed**, **audited**, and **rate-limited**.

---

## Authentication: X-ADMIN-KEY Header

All admin endpoints require the **X-ADMIN-KEY** header:

```http
X-ADMIN-KEY: <secret-value>
```

### Environment Setup

Set the admin key in `.env`:

```bash
# Mandatory for admin API
VERITTA_ADMIN_API_KEY=your-long-random-secret-here

# Optional: override default rate limit
VERITTA_ADMIN_RATE_LIMIT_PER_MIN=100
```

### Authentication Failures

| Scenario | HTTP Status | reason_codes |
|----------|------------|---------------|
| Header missing | 403 | `ADMIN_KEY_MISSING` |
| Header invalid | 403 | `ADMIN_KEY_INVALID` |
| Rate limit exceeded | 429 | `RATE_LIMIT_EXCEEDED` |

All failures emit `decision_audit` for auditability.

---

## Rate Limiting

**Default:** 100 requests per minute per admin key (conservative)

**Configurable:** Set `VERITTA_ADMIN_RATE_LIMIT_PER_MIN` in `.env`

**Enforcement:** Automatic via `ADMIN_G10` gate with decision_audit emission

---

## Endpoints

### 1. POST /admin/sessions/revoke

**Purpose:** Revoke a session (idempotent)

#### Request

```bash
curl -X POST http://localhost:8000/admin/sessions/revoke \
  -H "X-ADMIN-KEY: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

#### Request Schema

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Response (Success)

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "revoked",
  "revoked_at": "2025-12-23T10:30:45.123456+00:00"
}
```

**HTTP Status:** 200

#### Response (Already Revoked - Idempotent)

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "already_revoked",
  "revoked_at": "2025-12-23T10:20:00.000000+00:00"
}
```

**HTTP Status:** 200

#### Response (Session Not Found)

```json
{
  "status_code": 404,
  "reason_codes": ["SESSION_NOT_FOUND"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session not found",
  "details": null
}
```

**HTTP Status:** 404

#### Audit Trail

Every revoke operation generates:

1. **decision_audit** — X-ADMIN-KEY validation result
   - `profile_id: ADMIN_G2`
   - `decision: ALLOW` (if key valid)
   - `profile_hash: <P1.1 fingerprint>`

2. **action_audit** — Revocation result
   - `action: revoke_session`
   - `status: SUCCESS` | `FAILED`
   - `trace_id: <correlates with HTTP response>`

---

### 2. GET /admin/sessions/{session_id}

**Purpose:** Retrieve session metadata (admin-only, never returns api_key_hash)

#### Request

```bash
curl -X GET http://localhost:8000/admin/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-ADMIN-KEY: your-admin-key"
```

#### Response (Success)

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "created_at": "2025-12-23T10:00:00.000000+00:00",
  "expires_at": "2025-12-23T18:00:00.000000+00:00",
  "revoked_at": null
}
```

**HTTP Status:** 200

**Important:** `api_key_hash` is **NEVER** returned (privacy by design)

#### Response (Not Found)

```json
{
  "status_code": 404,
  "reason_codes": ["SESSION_NOT_FOUND"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session not found",
  "details": null
}
```

**HTTP Status:** 404

---

### 3. GET /admin/audit/summary

**Purpose:** Read-only aggregation of audit events (with streaming parser to avoid memory issues)

#### Request (Defaults)

```bash
curl -X GET http://localhost:8000/admin/audit/summary \
  -H "X-ADMIN-KEY: your-admin-key"
```

#### Request (Custom Parameters)

```bash
# Last 7 days, max 50k events, only decision_audit
curl -X GET "http://localhost:8000/admin/audit/summary?days=7&limit=50000&event_type=decision_audit" \
  -H "X-ADMIN-KEY: your-admin-key"
```

#### Query Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `days` | int | 1 | 1–7 | Days to look back |
| `limit` | int | 10000 | 100–50000 | Max events to process |
| `event_type` | str | None | `decision_audit` / `action_audit` | Filter by type |

#### Response (Success)

```json
{
  "window": {
    "days": 1,
    "limit": 10000
  },
  "decisions": {
    "allow": 427,
    "deny": 23
  },
  "deny_breakdown": {
    "RATE_LIMIT_EXCEEDED": 12,
    "ADMIN_KEY_INVALID": 5,
    "SESSION_NOT_FOUND": 3,
    "SESSION_EXPIRED": 3
  },
  "events_by_type": {
    "decision_audit": 450,
    "action_audit": 0
  },
  "ts_utc": "2025-12-23T11:00:00.000000+00:00",
  "events_processed": 450,
  "parse_errors": 0
}
```

**HTTP Status:** 200

#### Behavior

- **Streaming Parser:** Reads audit.log line-by-line (safe against huge logs)
- **Time Window:** Returns events from `(now - days)` to `now`
- **Event Limit:** Stops processing after `limit` events (whichever comes first)
- **No Raw Events:** Only aggregations returned (privacy-first)

---

### 4. GET /admin/health

**Purpose:** Health check for database and audit sink connectivity

#### Request

```bash
curl -X GET http://localhost:8000/admin/health \
  -H "X-ADMIN-KEY: your-admin-key"
```

#### Response (Healthy)

```json
{
  "status": "ok",
  "db": "connected",
  "audit_sink": "writable",
  "ts_utc": "2025-12-23T11:00:00.000000+00:00"
}
```

**HTTP Status:** 200

#### Response (Degraded)

```json
{
  "status": "ok",
  "db": "disconnected",
  "audit_sink": "writable",
  "ts_utc": "2025-12-23T11:00:00.000000+00:00"
}
```

**Note:** Even if DB is disconnected, status is still "ok" (endpoint itself responds). Consume the `db` field to detect issues.

---

## Error Response Format (Canonical)

All errors follow the standardized error envelope (see [docs/ERROR_ENVELOPE.md](ERROR_ENVELOPE.md)):

```json
{
  "status_code": 403,
  "reason_codes": ["ADMIN_KEY_INVALID"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Admin authentication failed",
  "details": null
}
```

---

## Audit Trail Generated

### Decision Audit (All Admin Operations)

```json
{
  "event_type": "decision_audit",
  "decision": "ALLOW",
  "profile_id": "ADMIN_G2",
  "profile_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "matched_rules": ["Admin key valid"],
  "reason_codes": [],
  "input_digest": null,
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts_utc": "2025-12-23T11:00:00.000000+00:00"
}
```

### Action Audit (Revoke Operations)

```json
{
  "event_type": "action_audit",
  "action": "revoke_session",
  "executor_id": "admin_api",
  "executor_version": "1.0.0",
  "status": "SUCCESS",
  "reason_codes": [],
  "input_digest": null,
  "output_digest": null,
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts_utc": "2025-12-23T11:00:00.000000+00:00"
}
```

---

## Example Workflows

### Workflow 1: Revoke a User Session

```bash
#!/bin/bash

ADMIN_KEY="your-admin-key"
SESSION_ID="550e8400-e29b-41d4-a716-446655440000"

# Step 1: Verify session exists
echo "📍 Checking session..."
curl -s http://localhost:8000/admin/sessions/$SESSION_ID \
  -H "X-ADMIN-KEY: $ADMIN_KEY" | jq .

# Step 2: Revoke session
echo "🔐 Revoking session..."
curl -s -X POST http://localhost:8000/admin/sessions/revoke \
  -H "X-ADMIN-KEY: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\"}" | jq .

# Step 3: Verify revocation
echo "✅ Verifying..."
curl -s http://localhost:8000/admin/sessions/$SESSION_ID \
  -H "X-ADMIN-KEY: $ADMIN_KEY" | jq '.revoked_at'
```

### Workflow 2: Analyze Audit Summary

```bash
#!/bin/bash

ADMIN_KEY="your-admin-key"

# Get last 24h of audit summary
echo "📊 Fetching audit summary (last 24h)..."
curl -s "http://localhost:8000/admin/audit/summary?days=1&limit=10000" \
  -H "X-ADMIN-KEY: $ADMIN_KEY" | jq .

# Focus on DENY breakdown
curl -s "http://localhost:8000/admin/audit/summary?days=1" \
  -H "X-ADMIN-KEY: $ADMIN_KEY" | jq '.deny_breakdown'
```

### Workflow 3: Health Check

```bash
#!/bin/bash

ADMIN_KEY="your-admin-key"

# Check system health
curl -s http://localhost:8000/admin/health \
  -H "X-ADMIN-KEY: $ADMIN_KEY" | jq .
```

---

## Privacy & Security

### ✅ What Is Returned

- Session ID (UUID)
- User ID (identifier)
- Timestamps (created_at, expires_at, revoked_at)
- Aggregated audit statistics (counts, reason_codes)

### ❌ What Is NEVER Returned

- `api_key_hash` (binding secret)
- Raw request payloads
- Stack traces
- PII (names, emails, addresses)
- Internal configuration

---

## Rate Limit Behavior

**Per Admin Key:**
- 100 requests per minute (default)
- Sliding window (last 60 seconds)
- Exceeded → 429 + `RATE_LIMIT_EXCEEDED` reason_code

**Example:**
```bash
# Request 101 within 60 seconds:
curl -X GET http://localhost:8000/admin/health \
  -H "X-ADMIN-KEY: your-admin-key"

# Response:
{
  "status_code": 429,
  "reason_codes": ["RATE_LIMIT_EXCEEDED"],
  "trace_id": "...",
  "message": "Admin rate limit exceeded",
  "details": null
}
```

---

## Deployment Checklist

- [ ] Set `VERITTA_ADMIN_API_KEY` to a long random secret (32+ chars)
- [ ] Set `VERITTA_AUDIT_LOG_PATH` to a persistent location (e.g., `/var/log/veritta/audit.log`)
- [ ] Ensure audit log directory is writable by the application
- [ ] Enable database connectivity (SQLite dev, PostgreSQL prod)
- [ ] Run smoke tests: `pytest tests/test_admin_api.py -v`
- [ ] Monitor audit.log for admin operations
- [ ] Set up alerts for `ADMIN_KEY_INVALID` spike (brute force detection)

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 on all requests | `VERITTA_ADMIN_API_KEY` not set | Set env var and restart |
| 429 Too Many Requests | Rate limit exceeded | Wait 60 seconds or increase `VERITTA_ADMIN_RATE_LIMIT_PER_MIN` |
| 404 on valid session | Session doesn't exist or expired | Check session_id; verify with `/admin/audit/summary` |
| Audit summary parse error | Corrupted audit.log | Check file integrity; rotate if necessary |
| DB disconnected (health check) | Database connection failed | Restart app or check PostgreSQL |

---

## Compliance

- ✅ **Fail-Closed:** Missing/invalid key → 403 (no default pass-through)
- ✅ **Audit Trail:** All operations logged with profile_hash (P1.1 invariant)
- ✅ **Privacy:** No raw payloads, no secrets returned
- ✅ **Human-in-the-Loop:** No automatic revocation; explicit admin action required
- ✅ **Rate Limit:** Prevents brute force and DoS
- ✅ **Idempotent:** Revoke operations are safe to retry

---

## Architecture

```
Request with X-ADMIN-KEY header
    ↓
AdminGuard validation (emit decision_audit)
    ↓
AdminRateLimit check (emit decision_audit)
    ↓
Endpoint handler (revoke/query/health)
    ↓
action_audit (if applicable)
    ↓
Response (with trace_id for correlation)
```

All steps are auditabled and traceable via trace_id.

---

## Version

**Document Version:** 1.0.0  
**API Version:** 1.0.0  
**Last Updated:** 2025-12-23  
**Governance:** V-COF, LGPD by design, Human-in-the-loop  
