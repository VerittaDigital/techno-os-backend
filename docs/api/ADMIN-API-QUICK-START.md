# Admin API — Quick Start & Manual Testing

## Running Tests

```bash
# TASK A1 + A2 tests (27 total)
python -m pytest tests/test_session_lifecycle.py tests/test_admin_api.py -v

# A2 only (14 tests)
python -m pytest tests/test_admin_api.py -v

# Specific test
python -m pytest tests/test_admin_api.py::TestRevokeSessionEndpoint::test_revoke_valid_session -v
```

---

## Manual Testing (with FastAPI test_client)

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test with valid admin key (set VERITTA_ADMIN_API_KEY env var first)
admin_key = "your-admin-key"

# 1. Health check
response = client.get("/admin/health", headers={"X-ADMIN-KEY": admin_key})
print(response.json())

# 2. Revoke a session
response = client.post(
    "/admin/sessions/revoke",
    json={"session_id": "550e8400-e29b-41d4-a716-446655440000"},
    headers={"X-ADMIN-KEY": admin_key}
)
print(response.json())

# 3. Get session details
response = client.get(
    "/admin/sessions/550e8400-e29b-41d4-a716-446655440000",
    headers={"X-ADMIN-KEY": admin_key}
)
print(response.json())

# 4. Audit summary (with defaults)
response = client.get(
    "/admin/audit/summary",
    headers={"X-ADMIN-KEY": admin_key}
)
print(response.json())

# 5. Audit summary (custom parameters)
response = client.get(
    "/admin/audit/summary?days=7&limit=5000&event_type=decision_audit",
    headers={"X-ADMIN-KEY": admin_key}
)
print(response.json())
```

---

## Manual Testing with curl

```bash
# Set admin key
export ADMIN_KEY="your-admin-key"

# Health check
curl -X GET http://localhost:8000/admin/health \
  -H "X-ADMIN-KEY: $ADMIN_KEY"

# Revoke session
curl -X POST http://localhost:8000/admin/sessions/revoke \
  -H "Content-Type: application/json" \
  -H "X-ADMIN-KEY: $ADMIN_KEY" \
  -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000"}'

# Get session
curl -X GET http://localhost:8000/admin/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-ADMIN-KEY: $ADMIN_KEY"

# Audit summary (default: 1 day, 10k limit)
curl -X GET http://localhost:8000/admin/audit/summary \
  -H "X-ADMIN-KEY: $ADMIN_KEY"

# Audit summary (custom)
curl -X GET "http://localhost:8000/admin/audit/summary?days=7&limit=5000" \
  -H "X-ADMIN-KEY: $ADMIN_KEY"
```

---

## Expected Responses

### POST `/admin/sessions/revoke` (success)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "revoked",
  "revoked_at": "2025-01-XX...Z"
}
```

### GET `/admin/sessions/{session_id}` (success)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "created_at": "2025-01-XX...Z",
  "expires_at": "2025-01-XX...Z",
  "revoked_at": null
}
```

### GET `/admin/audit/summary` (success)
```json
{
  "window": {"days": 1, "limit": 10000},
  "decisions": {"allow": 5, "deny": 2},
  "deny_breakdown": {"RATE_LIMIT_EXCEEDED": 1, "ADMIN_KEY_INVALID": 1},
  "events_by_type": {"decision_audit": 7, "action_audit": 0},
  "ts_utc": "2025-01-XX...Z"
}
```

### GET `/admin/health` (success)
```json
{
  "status": "ok",
  "db": "connected",
  "audit_sink": "writable",
  "ts_utc": "2025-01-XX...Z"
}
```

---

## Error Responses

### Missing X-ADMIN-KEY (403)
```json
{
  "error": "forbidden",
  "message": "Admin authentication failed",
  "trace_id": "...",
  "reason_codes": ["ADMIN_KEY_MISSING"]
}
```

### Invalid X-ADMIN-KEY (403)
```json
{
  "error": "forbidden",
  "message": "Admin authentication failed",
  "trace_id": "...",
  "reason_codes": ["ADMIN_KEY_INVALID"]
}
```

### Rate limit exceeded (429)
```json
{
  "error": "rate_limit_exceeded",
  "message": "Admin rate limit exceeded",
  "trace_id": "...",
  "reason_codes": ["RATE_LIMIT_EXCEEDED"]
}
```

### Session not found (404)
```json
{
  "error": "not_found",
  "message": "Session not found",
  "trace_id": "...",
  "reason_codes": ["SESSION_NOT_FOUND"]
}
```

---

## Performance Notes

- **Health check:** <5ms (minimal DB query)
- **Session retrieval:** <10ms (indexed UUID lookup)
- **Session revoke:** <20ms (update + commit)
- **Audit summary:** ~100-500ms (depends on audit.log size)
  - Streaming parser stops at limit or time window
  - No memory explosion even with 1M+ events

---

## Troubleshooting

### "Audit log not found"
- `VERITTA_AUDIT_LOG_PATH` not set or file doesn't exist
- Create empty audit.log: `touch ./audit.log`
- Or set path: `export VERITTA_AUDIT_LOG_PATH=/path/to/audit.log`

### "Rate limit exceeded"
- Increase `VERITTA_ADMIN_RATE_LIMIT_PER_MIN` (default 100)
- Or wait 60 seconds for window to reset

### "Database disconnected"
- Check `DATABASE_URL` is set and PostgreSQL/SQLite is running
- Verify connection string in `.env`

### "Audit sink unwritable"
- Ensure process has write permission to `VERITTA_AUDIT_LOG_PATH`
- Check disk space and inodes

---

## Environment Variables

```env
# Admin API
VERITTA_ADMIN_API_KEY=your-secret-key          # Required
VERITTA_ADMIN_RATE_LIMIT_PER_MIN=100           # Optional (default 100)

# Database
DATABASE_URL=sqlite:///./techno.db              # SQLite (dev)
DATABASE_URL=postgresql://user:pass@host/db    # PostgreSQL (prod)

# Audit Log
VERITTA_AUDIT_LOG_PATH=./audit.log             # Optional (default ./audit.log)

# Session
VERITTA_SESSION_TTL_HOURS=8                    # Optional (default 8)
```

---

## Security Checklist

- [ ] `VERITTA_ADMIN_API_KEY` is strong (32+ chars, random)
- [ ] Never expose key in logs, errors, or responses
- [ ] Use HTTPS in production (no plaintext X-ADMIN-KEY)
- [ ] Monitor rate limit (429) responses
- [ ] Rotate key periodically
- [ ] Audit summary respects time windows (no unbounded reads)
- [ ] api_key_hash NEVER returned in session responses
- [ ] decision_audit captured for all auth attempts
