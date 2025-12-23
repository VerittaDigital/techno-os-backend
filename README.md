# Techno OS Backend — Verittà (Governed Runtime)

**Cryptographically auditable backend with fail-closed authentication gates, canonical error envelopes, and human-in-the-loop governance.**

---

## Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Gates (F2.1 + F2.3)** | ✅ Implemented | X-API-Key + Bearer token chains |
| **Authentication** | ✅ Fail-closed | Mandatory; missing → 500 DENY (audited) |
| **Error Envelope** | ✅ Canonical | Unified structure, reason codes, privacy-safe |
| **Audit Trail** | ✅ JSONL sink | `decision_audit` + `action_audit` events |
| **Profile Hash (P1.1)** | ✅ Non-empty invariant | Verified in all audit records |
| **Tests** | ✅ 35/35 passing | Unit + smoke tests |

---

## Quickstart (Local Development)

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/veritta/techno-os-backend.git
cd techno-os-backend

# Create virtual environment
python -m venv venv

# Activate (choose one)
source venv/bin/activate           # Linux/Mac
venv\Scripts\activate              # Windows PowerShell
venv\Scripts\activate.bat          # Windows Command Prompt

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example to .env
cp .env.example .env

# Edit .env and set required variables:
# - VERITTA_BETA_API_KEY (mandatory)
# - VERITTA_PROFILES_FINGERPRINT (run: python scripts/generate_profiles_fingerprint_lock.py)
# - VERITTA_AUDIT_LOG_PATH (default: ./audit.log)
```

**Critical:** Missing `VERITTA_BETA_API_KEY` → Server returns 500 on startup.

### 3. Run Server

```bash
# Development (auto-reload)
python -m uvicorn app.main:app --reload

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server listens on `http://127.0.0.1:8000`

### 4. Verify Setup

```bash
# Check health
curl -s http://localhost:8000/health | jq .

# Run all tests
pytest tests/ -v

# Run smoke tests
bash <(cat docs/RUNBOOK_SAMURAI.md | grep -A 50 "2.4 End-to-End")
```

---

## Mandatory Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| **VERITTA_HOST** | No | `0.0.0.0` | FastAPI host binding |
| **VERITTA_PORT** | No | `8000` | FastAPI port |
| **VERITTA_BETA_API_KEY** | **YES** | None | API authentication key (fail-closed if missing) |
| **VERITTA_PROFILES_FINGERPRINT** | **YES** | None | Governance fingerprint (P1.1 invariant) |
| **VERITTA_AUDIT_LOG_PATH** | No | `./audit.log` | JSONL audit sink path |
| **VERITTA_AUDIT_DIGEST_ENABLED** | No | `true` | Include SHA256 digests in audit |
| **VERITTA_MAX_PAYLOAD_SIZE** | No | `8192` | Max request payload (bytes) |
| **VERITTA_EXECUTOR_TIMEOUT_S** | No | `10.0` | Action execution timeout (seconds) |

---

## API Examples

### F2.1 — Legacy X-API-Key Gate (Gate G2)

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $VERITTA_BETA_API_KEY" \
  -d '{
    "action": "process",
    "event_type": "test_event",
    "text": "Hello World"
  }'
```

**Expected Response (HTTP 200):**

```json
{
  "status_code": 200,
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "action": "process",
    "status": "SUCCESS"
  }
}
```

### F2.3 — Bearer Token Gate (Gate G4)

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <session_token>" \
  -H "X-VERITTA-USER-ID: u_12345" \
  -H "X-VERITTA-SESSION-ID: sess_abcdef" \
  -d '{
    "action": "process",
    "event_type": "test_event"
  }'
```

### Error Response Example

```bash
# Missing API key
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"action":"test"}'
```

**Response (HTTP 403):**

```json
{
  "status_code": 403,
  "reason_codes": ["MISSING_API_KEY"],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Missing required header: X-API-Key",
  "details": {
    "header": "X-API-Key"
  }
}
```

---

## Testing

### Unit Tests (35/35)

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_auth.py::test_valid_api_key -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Smoke Tests (Executable)

See [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) for full runbook.

**Quick smoke test:**

```bash
# Start server in background
python -m uvicorn app.main:app &

# Run F2.1 test
curl -s -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $VERITTA_BETA_API_KEY" \
  -d '{"action":"test_action","event_type":"test_event"}' | jq '.trace_id'

# Verify audit log
tail -1 audit.log | jq .
```

---

## Audit Log

All decisions are logged to `VERITTA_AUDIT_LOG_PATH` (JSONL format).

**Example decision_audit record:**

```json
{
  "event_type": "decision_audit",
  "decision": "ALLOW",
  "profile_id": "G2",
  "profile_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "matched_rules": ["API key valid"],
  "reason_codes": [],
  "input_digest": "abcd1234...",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts_utc": "2025-12-23T00:48:00.123456+00:00"
}
```

**Check audit log:**

```bash
# View last 10 records
tail -10 audit.log | jq .

# Count events
grep -c '"event_type":"decision_audit"' audit.log

# Find DENY decisions
grep '"decision":"DENY"' audit.log | jq '.reason_codes'

# Lookup by trace_id
grep "550e8400-e29b-41d4-a716-446655440000" audit.log | jq .
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/ERROR_ENVELOPE.md](docs/ERROR_ENVELOPE.md) | Error response contract, reason codes, client patterns |
| [docs/AUDIT_LOG_SPEC.md](docs/AUDIT_LOG_SPEC.md) | JSONL audit format, invariants, offline tools |
| [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) | Executable smoke tests, diagnostics, incident response |
| [.env.example](.env.example) | Environment variable reference |

---

## Architecture

### Authentication Gates (Fail-Closed)

1. **G0 — Missing Auth Header** → 403 DENY
2. **G2 — F2.1 X-API-Key** → Validate against `VERITTA_BETA_API_KEY`
3. **G4 — F2.3 Bearer Token** → Validate session + user binding
4. **G10 — Rate Limiting** → 1000 req/min per key, 100/min per session

All gates emit `decision_audit` events to audit log.

### Execution Pipeline

```
Request
  ↓
Authentication Gate (G0/G2/G4)
  ↓
Profile Check (P1.1)
  ↓
Payload Validation (P2)
  ↓
Action Registry Lookup
  ↓
Executor Dispatch
  ↓
Audit Log (action_audit)
  ↓
Error Envelope + Response
```

### Privacy & Security (LGPD by Design)

- **No raw payloads** in audit or errors
- **No stack traces** exposed to clients
- **No PII** logged (only digests)
- **Trace IDs** enable request correlation without storing data
- **Human-in-the-loop:** All governance decisions are auditable

---

## Production Deployment

### Security Checklist

- [ ] `VERITTA_BETA_API_KEY` is a 64+ char random string
- [ ] `VERITTA_PROFILES_FINGERPRINT` is non-empty
- [ ] `VERITTA_AUDIT_LOG_PATH` points to absolute path on secure volume
- [ ] Audit log rotation configured (90-day retention minimum)
- [ ] Environment variables loaded from secure secret manager (not .env)
- [ ] API runs behind TLS reverse proxy (https only)
- [ ] Rate limiting verified in production
- [ ] Health check endpoint disabled or authenticated in production

### Log Rotation (Linux)

```bash
# /etc/logrotate.d/veritta
/var/log/veritta/audit.log {
  daily
  rotate 90
  compress
  gzip
  missingok
  notifempty
}
```

### Monitoring

- Monitor `RATE_LIMIT_EXCEEDED` reason codes → Rate limit tune
- Monitor `EXECUTOR_TIMEOUT` → Increase `VERITTA_EXECUTOR_TIMEOUT_S`
- Monitor `AUDIT_SINK_FAILED` → Check disk space
- Monitor decision DENY rate → Audit for legitimate blocking

See [docs/RUNBOOK_SAMURAI.md § 3 (Production Diagnostics)](docs/RUNBOOK_SAMURAI.md#part-3-production-diagnostics) for queries.

---

## Support

For issues, questions, or contributions:

1. Check [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) for troubleshooting
2. Search audit.log for trace_id correlation
3. Review [docs/ERROR_ENVELOPE.md](docs/ERROR_ENVELOPE.md) for reason codes
4. Run `pytest tests/ -v` to verify test suite

---

## License

MIT (see LICENSE file)
