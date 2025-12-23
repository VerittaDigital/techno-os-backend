# Runbook Samurai — Operational Excellence Guide

Real-time diagnostics and validation for Techno OS Backend.

---

## Part 1: Pre-Launch Checklist

Run this before deploying to staging or production.

### 1.1 Environment Setup

```bash
# Copy example to .env (if missing)
cp .env.example .env

# Verify mandatory variables are set
grep -E "^VERITTA_(HOST|PORT|BETA_API_KEY|PROFILES_FINGERPRINT|AUDIT_LOG_PATH)" .env

# Expected output (all 5 lines present):
# VERITTA_HOST=0.0.0.0
# VERITTA_PORT=8000
# VERITTA_BETA_API_KEY=CHANGE_ME_TO_A_LONG_RANDOM_SECRET
# VERITTA_PROFILES_FINGERPRINT=...
# VERITTA_AUDIT_LOG_PATH=./audit.log
```

### 1.2 Python Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Expected: No errors; all packages installed

# Verify critical packages
python -c "import fastapi, pydantic, pytest; print('✓ Core deps OK')"
```

### 1.3 Governance Profiles Fingerprint (P1.1 Invariant)

```bash
# If VERITTA_PROFILES_FINGERPRINT is missing or empty:
python scripts/generate_profiles_fingerprint_lock.py

# This outputs a SHA256 hash
# Copy the hash to .env: VERITTA_PROFILES_FINGERPRINT=<hash>

# Verify the hash is non-empty
if [ -z "$VERITTA_PROFILES_FINGERPRINT" ]; then
  echo "ERROR: VERITTA_PROFILES_FINGERPRINT is empty"
  exit 1
fi
echo "✓ Profiles fingerprint locked: ${VERITTA_PROFILES_FINGERPRINT:0:16}..."
```

### 1.4 Action Registry Sync

```bash
# Verify action registry is loadable
python -c "from app.action_registry import registry; print(f'✓ Registry: {len(registry.actions)} actions loaded')"

# Expected: At least 1 action ("test_event" for smoke tests)
```

### 1.5 Audit Log Path

```bash
# Create audit log directory if needed
mkdir -p $(dirname "$VERITTA_AUDIT_LOG_PATH")

# Test write permission
touch "$VERITTA_AUDIT_LOG_PATH"

# Verify it's writable
if [ ! -w "$VERITTA_AUDIT_LOG_PATH" ]; then
  echo "ERROR: Cannot write to $VERITTA_AUDIT_LOG_PATH"
  exit 1
fi
echo "✓ Audit log writable: $VERITTA_AUDIT_LOG_PATH"
```

---

## Part 2: Smoke Tests (Executable)

Run all smoke tests **before** marking the deployment as "go".

### 2.1 Unit Tests (pytest)

```bash
# Run all tests
pytest tests/ -v --tb=short

# Expected output:
# tests/test_action_registry.py::test_load_actions PASSED
# tests/test_auth.py::test_valid_api_key PASSED
# tests/test_audit_log.py::test_audit_sink PASSED
# ...
# ========================== X passed in Y.XXs ==========================
```

### 2.2 Smoke Test Event Type Registration

```bash
# Verify the smoke test event type exists in registry
python -c "
from app.action_registry import registry
event_type = 'test_event'  # VERITTA_SMOKE_TEST_EVENT_TYPE
if event_type in registry.actions:
    print(f'✓ Smoke test event registered: {event_type}')
else:
    print(f'✗ Missing event type: {event_type}')
    exit(1)
"
```

### 2.3 API Startup Test

```bash
# Start the backend in background
python -m uvicorn app.main:app --host "$VERITTA_HOST" --port "$VERITTA_PORT" &
API_PID=$!

# Wait for startup
sleep 2

# Check health
curl -s http://localhost:8000/health && echo "✓ API healthy"

# Kill the process
kill $API_PID
```

### 2.4 End-to-End Smoke Test

```bash
# Start the backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
sleep 2

# Run a test request
TRACE_ID=$(uuidgen)
RESPONSE=$(curl -s -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $VERITTA_BETA_API_KEY" \
  -H "X-TRACE-ID: $TRACE_ID" \
  -d '{"action":"test_action","event_type":"test_event"}')

# Check response status
if echo "$RESPONSE" | jq -e '.status_code == 200' &>/dev/null; then
  echo "✓ Smoke test PASSED"
  echo "Response: $RESPONSE" | jq .
else
  echo "✗ Smoke test FAILED"
  echo "$RESPONSE" | jq .
  kill $API_PID
  exit 1
fi

# Verify audit log has entry with same trace_id
sleep 1
if grep "$TRACE_ID" "$VERITTA_AUDIT_LOG_PATH" &>/dev/null; then
  echo "✓ Audit trail recorded for trace_id: $TRACE_ID"
else
  echo "✗ No audit entry for trace_id: $TRACE_ID"
fi

# Cleanup
kill $API_PID
```

### 2.5 Audit Log Integrity Check (P1.1 Invariant)

```bash
# Verify profile_hash is never empty in audit logs
EMPTY_HASHES=$(grep -c '"profile_hash":""' "$VERITTA_AUDIT_LOG_PATH" || echo 0)
NULL_HASHES=$(grep -c '"profile_hash":null' "$VERITTA_AUDIT_LOG_PATH" || echo 0)

if [ "$EMPTY_HASHES" -eq 0 ] && [ "$NULL_HASHES" -eq 0 ]; then
  echo "✓ P1.1 Invariant: profile_hash never empty"
else
  echo "✗ P1.1 Violation: Found empty profile_hash in audit log"
  exit 1
fi

# Verify reason_codes is non-empty for DENY decisions
DENY_NO_CODES=$(jq -c 'select(.event_type=="decision_audit" and .decision=="DENY" and (.reason_codes == [] or .reason_codes == null))' "$VERITTA_AUDIT_LOG_PATH" | wc -l)

if [ "$DENY_NO_CODES" -eq 0 ]; then
  echo "✓ Audit invariant: reason_codes non-empty for DENY"
else
  echo "✗ Audit violation: DENY decision without reason_codes"
  exit 1
fi
```

---

## Part 3: Production Diagnostics

Use these commands to investigate issues in production.

### 3.1 Check API Health

```bash
# Remote health check (adjust URL)
curl -s https://api.techno-os.example.com/health | jq .

# Expected response:
# {"status": "ok", "timestamp": "2025-12-23T..."}
```

### 3.2 Audit Log Analysis

```bash
# Count events by type
jq -r '.event_type' "$VERITTA_AUDIT_LOG_PATH" | sort | uniq -c | sort -rn

# Example output:
#   1000 action_audit
#    850 decision_audit
```

### 3.3 Find DENY Decisions

```bash
# List all DENY decisions with reason codes
jq -c 'select(.event_type=="decision_audit" and .decision=="DENY")' "$VERITTA_AUDIT_LOG_PATH" | \
  jq '.reason_codes, .trace_id' | \
  head -20

# Correlate with specific API key
API_KEY_HASH=$(echo -n "sk_test_abc123" | sha256sum | cut -d' ' -f1)
grep "$API_KEY_HASH" "$VERITTA_AUDIT_LOG_PATH" | jq -c '.decision, .reason_codes' | sort | uniq -c
```

### 3.4 Rate Limit Violations

```bash
# Find rate limit exceeded errors
grep -c "RATE_LIMIT_EXCEEDED" "$VERITTA_AUDIT_LOG_PATH"

# Find when they occurred
grep "RATE_LIMIT_EXCEEDED" "$VERITTA_AUDIT_LOG_PATH" | \
  jq '.ts_utc, .trace_id' | \
  head -10
```

### 3.5 Executor Failures

```bash
# Find action execution failures
jq -c 'select(.event_type=="action_audit" and .status != "SUCCESS")' "$VERITTA_AUDIT_LOG_PATH" | \
  jq '.status, .reason_codes, .executor_id' | \
  head -20

# Count by executor
jq -c 'select(.event_type=="action_audit")' "$VERITTA_AUDIT_LOG_PATH" | \
  jq -r '.executor_id' | \
  sort | \
  uniq -c | \
  sort -rn
```

### 3.6 Session Expiration Issues

```bash
# Find session-related denials
grep "G5_session" "$VERITTA_AUDIT_LOG_PATH" | wc -l

# Find specific session errors
jq -c 'select(.reason_codes[] | contains("G5_session"))' "$VERITTA_AUDIT_LOG_PATH" | \
  jq '.reason_codes, .ts_utc' | \
  head -10
```

### 3.7 Performance Analysis

```bash
# Average decision latency (from first to last decision per trace_id)
jq -c 'select(.event_type=="decision_audit")' "$VERITTA_AUDIT_LOG_PATH" | \
  jq '.ts_utc' | \
  sort | \
  awk 'NR == 1 { first = $0; last = $0; next } { last = $0 } END { print "Decision latency window:", first, "to", last }'

# Count audit records per second (throughput)
jq -r '.ts_utc' "$VERITTA_AUDIT_LOG_PATH" | \
  sed 's/\.[0-9]*+//' | \
  uniq -c | \
  awk '{ sum += $1; print $1 " records at " $2 " (avg: " int(sum/NR) "/s)" }'
```

---

## Part 4: Incident Response

### 4.1 API Suddenly Returns 500 Errors

**Steps:**

1. Check if the API is still running:
   ```bash
   curl -s http://localhost:8000/health
   ```

2. Check audit log for recent failures:
   ```bash
   jq -c 'select(.event_type=="action_audit" and .status=="FAILED")' "$VERITTA_AUDIT_LOG_PATH" | tail -5
   ```

3. Check error type:
   ```bash
   tail -20 "$VERITTA_AUDIT_LOG_PATH" | jq '.reason_codes'
   ```

4. If `EXECUTOR_TIMEOUT`: Increase `VERITTA_EXECUTOR_TIMEOUT_S` or investigate executor performance
5. If `AUDIT_SINK_FAILED`: Check disk space and write permissions on `VERITTA_AUDIT_LOG_PATH`
6. If `LLM_PROVIDER_UNAVAILABLE`: Check LLM provider connectivity and `LLM_API_KEY`

### 4.2 High DENY Rate

**Steps:**

1. Check DENY distribution:
   ```bash
   jq -r '.reason_codes[]' "$VERITTA_AUDIT_LOG_PATH" | sort | uniq -c | sort -rn | head -10
   ```

2. If `G2_INVALID_API_KEY`: Verify `VERITTA_BETA_API_KEY` is correct
3. If `G7_PAYLOAD_LIMIT_EXCEEDED`: Clients are sending payloads > 8KB; increase `VERITTA_MAX_PAYLOAD_SIZE`
4. If `G10_RATE_LIMIT_EXCEEDED`: Consider increasing rate limit for known clients

### 4.3 Audit Log Growing Too Fast

**Steps:**

1. Check log size:
   ```bash
   du -sh "$VERITTA_AUDIT_LOG_PATH"
   ```

2. Disable digest logging (saves space):
   ```bash
   # In .env:
   VERITTA_AUDIT_DIGEST_ENABLED=false
   ```

3. Archive old logs:
   ```bash
   # Keep last 7 days
   find ./audit.log.* -mtime +7 -delete
   ```

---

## Part 5: Runbook Verification (Automated)

```bash
#!/bin/bash
# run-complete-diagnostics.sh — Full system validation

set -e

echo "========== TECHNO OS BACKEND DIAGNOSTICS =========="

# Checklist
echo ""
echo "1. Checking environment..."
python scripts/check_env.py

echo ""
echo "2. Running unit tests..."
pytest tests/ -q

echo ""
echo "3. Verifying action registry..."
python -c "from app.action_registry import registry; print(f'✓ {len(registry.actions)} actions')"

echo ""
echo "4. Starting API..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
sleep 2

echo ""
echo "5. Running smoke tests..."
curl -s -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $VERITTA_BETA_API_KEY" \
  -d '{"action":"test_action","event_type":"test_event"}' | jq -e '.status_code == 200' && echo "✓ Smoke test passed"

echo ""
echo "6. Verifying audit invariants..."
python scripts/verify_audit_invariants.py

echo ""
echo "========== ALL CHECKS PASSED =========="

kill $API_PID 2>/dev/null || true
```

---

## Appendix: Quick Reference

| Issue | Command |
|-------|---------|
| API won't start | `python -m uvicorn app.main:app` (check error output) |
| Missing env vars | `python -c "import os; print(os.environ['VERITTA_BETA_API_KEY'])"` |
| Audit log problems | `jq -c '.' "$VERITTA_AUDIT_LOG_PATH" \| head -5` |
| Recent errors | `tail -20 "$VERITTA_AUDIT_LOG_PATH" \| jq '.reason_codes'` |
| Trace lookup | `grep "550e8400..." "$VERITTA_AUDIT_LOG_PATH" \| jq .` |
| Rate limits | `grep "G10_rate_limit" "$VERITTA_AUDIT_LOG_PATH" \| wc -l` |
| Profile hash | `jq -c '.profile_hash' "$VERITTA_AUDIT_LOG_PATH" \| sort \| uniq` |
