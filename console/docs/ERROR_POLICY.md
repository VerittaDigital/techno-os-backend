# ERROR_POLICY.md — Techno OS Console v0.1

**Effective:** January 4, 2026  
**Framework:** F-CONSOLE-0.1 Etapa 4  
**Governance:** Fail-Closed Error Handling  

---

## 1. Error Philosophy: Fail-Closed

**Core Principle:**
> When in doubt, return BLOCKED. Never escalate uncertainty to the user.

**Rationale:**
- Client code is public (embedded in compiled JS)
- Backend is potentially untrusted or unreachable
- User actions could be destructive (execute commands, audit logs)
- Safer to block than to allow on uncertain status

---

## 2. HTTP Status Code Handling

### 200 OK — Dual Semantics

**HTTP 200 does NOT mean success.** It means "response was processed."

```json
200 OK
{
  "status": "BLOCKED",       // ← This is the actual status!
  "trace_id": "api-403",
  "reason_codes": ["API_KEY_INVALID"]
}
```

**Client Logic:**
```javascript
if (response.ok) {
  // Parse the 'status' field — it may still be BLOCKED
  const status = response.data.status;
  if (status === "BLOCKED") {
    // User is blocked, even though HTTP 200
  }
}
```

### 4XX Errors — Client Responsibility

| Code | Cause | Client Action | Status Returned |
|------|-------|---|---|
| 400 | Malformed JSON | Parse error → fallback | `BLOCKED` |
| 401 | Missing API key | Message: "Autenticacao falhou" | `BLOCKED` |
| 403 | Invalid API key | Message: "Autenticacao falhou" | `BLOCKED` |

**Client Handler:**
```javascript
catch (error) {
  if (error.response?.status === 401 || error.response?.status === 403) {
    return { status: 'BLOCKED', message: 'Autenticacao falhou' };
  }
}
```

### 5XX Errors — Server Failure (Fail-Closed)

| Code | Cause | Client Action | Status Returned |
|------|-------|---|---|
| 500 | Server error | Treat as timeout → fallback | `BLOCKED` |
| 502/503/504 | Service unavailable | Treat as timeout → fallback | `BLOCKED` |

**Client Handler:**
```javascript
catch (error) {
  if (error.response?.status >= 500) {
    return { status: 'BLOCKED', message: 'Backend indisponivel' };
  }
}
```

### 0 (Network/Timeout) — Fail-Closed Default

| Cause | Timeout | Network Error |
|-------|---------|---|
| Client AbortController | Yes (15s hardcoded) | No |
| Connection refused | No | Yes |
| DNS failure | No | Yes |
| Client offline | No | Yes |

**Client Handler:**
```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 15000);

try {
  const response = await fetch(url, { signal: controller.signal });
  clearTimeout(timeoutId);
} catch (error) {
  clearTimeout(timeoutId);
  
  if (error.name === 'AbortError') {
    // Timeout
    return { status: 'BLOCKED', error: 'Request timeout' };
  } else {
    // Network error
    return { status: 'BLOCKED', error: 'Backend indisponivel' };
  }
}
```

---

## 3. Error Scenarios by Endpoint

### /api/execute — Fail-Closed Table

| Scenario | HTTP | Response | Client Status |
|----------|------|----------|---|
| Success | 200 | `{ status: 'APPROVED', ... }` | APPROVED |
| Business logic blocked | 200 | `{ status: 'BLOCKED', reason_codes: [...] }` | BLOCKED |
| Auth failed | 401 | Error response | BLOCKED |
| Invalid API key | 403 | Error response | BLOCKED |
| Malformed request | 400 | Error response | BLOCKED |
| Server error | 500 | Error response | BLOCKED |
| Timeout (>15s) | 0 | None | BLOCKED |
| Network error | 0 | None | BLOCKED |

**Outcome:** User sees BLOCKED; console shows error message with trace_id

### /api/audit — Fallback Chain

```
GET /api/audit?filter=all&limit=50
  ↓
  ├─ 200 OK, status: APPROVED
  │  → Return audit log
  │
  ├─ 200 OK, status: BLOCKED
  │  → AUTO-FALLBACK to /api/diagnostic/metrics
  │     (no retry limit; try once)
  │
  ├─ 4XX or 5XX or timeout
  │  → AUTO-FALLBACK to /api/diagnostic/metrics
  │
  ├─ /api/diagnostic/metrics ALSO fails
  │  → Return empty array []
  │
  └─ Parse error (invalid JSON)
     → Return empty array []
```

**Key Insight:** Never error out on missing audit log. Return empty array.

**Rationale:** Audit log is informational; never block user actions.

### /api/memory — Null Handling

| Scenario | HTTP | Response | Client Returns |
|----------|------|----------|---|
| Success | 200 | `{ command, output, ... }` | Object |
| Status BLOCKED | 200 | `{ status: 'BLOCKED' }` | `null` |
| Data missing | 200 | `{}` | `null` |
| Parse error | Error | None | `null` |
| Network error | 0 | None | `null` |

**Outcome:** User sees empty memory panel; no error message

---

## 4. Reason Codes — Error Classification

### Current Reason Codes (v0.1)

These are sent in `reason_codes` array when status is BLOCKED:

| Code | Meaning | Trigger |
|------|---------|---------|
| `API_KEY_INVALID` | API key missing or invalid | 401/403 response |
| `API_BLOCKED` | Backend blocked the request | 200 with BLOCKED status |
| `VALIDATION_FAILED` | Command validation failed | Invalid command pattern |
| `RATE_LIMITED` | Rate limit exceeded | Too many requests |

### Future Reason Codes (v0.2+)

These will be documented in MINOR releases:
- `TIMEOUT` — Request exceeded 15 seconds
- `RESOURCE_NOT_FOUND` — Endpoint does not exist
- `SESSION_EXPIRED` — Session ID invalid or expired
- `QUOTA_EXCEEDED` — User quota reached

### Client-Side Use of Reason Codes

```javascript
// Current: Just display reason codes as-is
if (response.reason_codes?.length > 0) {
  console.log('Reasons:', response.reason_codes.join(', '));
}

// Future (v1.0): Map to user-facing messages
const messages = {
  'API_KEY_INVALID': 'Authentication failed. Please check your API key.',
  'RATE_LIMITED': 'Too many requests. Please wait a moment.',
  // ...
};
```

---

## 5. Message Handling

### Standard Error Messages

**When to show to user:**

| Message | Condition | User Sees |
|---------|-----------|---|
| "Autenticacao falhou" | 401 or 403 response | ✅ Yes |
| "Request timeout" | Timeout after 15s | ✅ Yes |
| "Backend indisponivel" | Network error or 5XX | ✅ Yes |
| "Invalid response from server" | Parse error | ✅ Yes |
| reason_codes array | Business logic blocked | ✅ Yes (as array) |

**When NOT to show (fail-silent):**

| Message | Condition | User Sees |
|---------|-----------|---|
| trace_id | In console logs only | ❌ No (debug use) |
| Full stack trace | Server error | ❌ No (security) |
| Raw JSON response | Parse error | ❌ No (debug use) |

### Message Localization (Future)

Currently: All messages in Portuguese (pt-BR)

**For v1.0:**
```javascript
// i18n support planned
const i18n = {
  'pt-BR': {
    'autenticacao.falhou': 'Autenticacao falhou',
    'timeout': 'Requisição excedeu 15 segundos'
  },
  'en': {
    'autenticacao.falhou': 'Authentication failed',
    'timeout': 'Request exceeded 15 seconds'
  }
};
```

---

## 6. Retry Policy

### Client Retry Rules

**What DOES retry automatically:**
1. `/api/audit` → fallback to `/api/diagnostic/metrics` (once)
2. [None other — see below]

**What does NOT retry:**
1. `/api/execute` — no retry (command already sent once; retry could duplicate)
2. `/api/memory` — no retry (informational only)
3. `/process` (legacy) — no retry

**Why no general retry?**
- Command execution is not idempotent
- Risk of duplicate actions (execute twice)
- Timeout is fail-closed; retrying doesn't help
- Backend is either down or blocking (retry won't change that)

### Recommended Retry (Future)

For v1.0, implement exponential backoff:
```javascript
// Pseudo-code (not in 0.1)
async function executeWithRetry(command, maxRetries = 3, backoff = 100) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await executeCommand(command);
    } catch (err) {
      if (i < maxRetries - 1) {
        await sleep(backoff * Math.pow(2, i)); // Exponential backoff
      }
    }
  }
  return { status: 'BLOCKED' }; // Give up
}
```

---

## 7. Timeout Thresholds

### Client Timeout (Hardcoded)

| Endpoint | Timeout | Mechanism |
|----------|---------|-----------|
| `/api/execute` | 15 seconds | AbortController |
| `/api/audit` | 15 seconds | AbortController |
| `/api/diagnostic/metrics` | 15 seconds | AbortController |
| `/api/memory` | 15 seconds | AbortController |
| `/process` (legacy) | 15 seconds | AbortController |

**Cannot be changed (hardcoded in compiled client)**

### Server Response Time SLA (Recommended)

| Endpoint | P99 | P100 | Notes |
|----------|-----|------|-------|
| `/api/execute` | 1 sec | 5 sec | Should complete quickly |
| `/api/audit` | 2 sec | 10 sec | May query audit log |
| `/api/memory` | 500 ms | 5 sec | Simple cache lookup |

**Rationale:**
- If server can't respond in 15s, it will be treated as timeout anyway
- Aim for <5s to be safe; <1s ideal
- If audit takes 10s, fallback to /api/diagnostic/metrics will still timeout

---

## 8. Response Validation

### Schema Compliance (Client-Side)

**Client checks:**
```javascript
// 1. Check status is valid
if (!['APPROVED', 'BLOCKED', 'EXPIRED', 'WARNING', 'NEUTRAL'].includes(data.status)) {
  data.status = 'BLOCKED'; // Fail-closed
}

// 2. Check trace_id exists
if (!data.trace_id) {
  data.trace_id = 'api-' + response.status; // Fallback
}

// 3. Check ts_utc is ISO 8601
if (!data.ts_utc || !data.ts_utc.endsWith('Z')) {
  data.ts_utc = new Date().toISOString(); // Fallback
}

// 4. Check reason_codes is array
if (!Array.isArray(data.reason_codes)) {
  data.reason_codes = [];
}
```

---

## 9. Logging & Observability

### What Client Logs (For Debugging)

```javascript
console.log('[API] execute', {
  endpoint: '/api/execute',
  method: 'POST',
  timestamp: new Date().toISOString(),
  requestBody: { command },
  responseStatus: response.status,     // HTTP 200
  responseData: response.data,         // { status: 'APPROVED', trace_id: '...' }
  elapsedMs: Date.now() - startTime
});
```

**Do NOT log:**
- API key
- Full error stack traces
- Raw request/response bodies (too large)

### Server-Side Logging (Required)

Backend MUST log:
```
[2026-01-04 12:00:00] [TRACE] trace_id=api-200
  endpoint=/api/execute
  method=POST
  command=GET_STATUS
  session_id=sess_abc
  http_status=200
  status=APPROVED
  reason_codes=[]
  elapsed_ms=250
  user_ip=192.168.1.100
```

**Correlation:** Use trace_id to link client logs to server logs

---

## 10. Security & Error Information Leakage

### Never Expose in Error Messages

❌ Internal error details (e.g., "MySQL connection failed")  
❌ File paths (e.g., "/var/www/api/execute.php")  
❌ Database schema (e.g., "Column 'user_id' not found")  
❌ Stack traces (JavaScript or Python)  
❌ API credentials or keys  

### Safe to Expose

✅ Trace ID (for support reference)  
✅ Timestamp (ISO 8601)  
✅ HTTP status code  
✅ Generic reason codes (e.g., "VALIDATION_FAILED")  
✅ Business logic status (BLOCKED, APPROVED, EXPIRED)  

### Example: Safe Error Response

```json
{
  "status": "BLOCKED",
  "trace_id": "api-403",
  "ts_utc": "2026-01-04T12:00:00Z",
  "reason_codes": ["API_KEY_INVALID"],
  "message": "Autenticacao falhou"
}
```

### Example: UNSAFE Error Response (DO NOT SEND)

```json
{
  "error": "FATAL: Connection refused at 127.0.0.1:5432",
  "stack": "at PostgreSQL.connect() [postgres.js:42]",
  "query": "SELECT * FROM users WHERE id = $1",
  "api_key_attempted": "sk_test_xxx"
}
```

---

## 11. Monitoring & Alerting

### Metrics to Track (Etapa 5-6)

```yaml
# Response time distribution
api_execute_duration_ms:
  p50: ~100 ms    # Median
  p95: ~500 ms    # 95th percentile
  p99: ~1000 ms   # 99th percentile

# Error rates
api_execute_blocked_percent:
  target: <5% of requests
  alert: >10%

api_audit_fallback_percent:
  target: <1% (audit should not fail)
  alert: >5%

api_timeout_percent:
  target: 0%
  alert: >0.1%
```

### Alerting Rules

**Critical (page on-call):**
- `api_timeout_percent > 0.1%` → Server too slow
- `api_authentication_failures > 50/min` → Attack or config error
- `api_execute_blocked_percent > 50%` → Business logic failing

**Warning (create ticket):**
- `api_audit_fallback_percent > 1%` → Audit endpoint unstable
- `api_response_time_p99 > 10s` → Approaching timeout threshold

---

## 12. Error Testing (Etapa 5-6)

### Test Cases Required

**Client Simulation:**
```bash
# Test 1: Timeout handling
npm run test:timeout
  Expected: status = BLOCKED, message = "Request timeout"

# Test 2: Network error
npm run test:network-error
  Expected: status = BLOCKED, message = "Backend indisponivel"

# Test 3: Malformed response
npm run test:malformed-json
  Expected: status = BLOCKED, reason_codes = []

# Test 4: Audit fallback
npm run test:audit-fallback
  Expected: Tries /api/diagnostic/metrics if /api/audit blocked

# Test 5: Unknown status
npm run test:unknown-status
  Expected: Normalized to BLOCKED (fail-closed)
```

---

## 13. Known Limitations (v0.1)

| Limitation | Impact | Resolution (v1.0) |
|-----------|--------|---|
| No request deduplication | Duplicate commands possible on retry | Add idempotency key |
| No rate limiting | Abuse possible with compiled API key | Implement rate limits |
| No session validation | Any client can claim any session_id | Add session token validation |
| Timeout hardcoded (15s) | Cannot adjust for slow networks | Make configurable in headers |

---

## 14. Compliance Checklist

### Backend MUST

- ✅ Return all responses in <15 seconds
- ✅ Always include `trace_id` in success responses
- ✅ Return valid StatusType (never unknown values)
- ✅ Return 401/403 for auth failures
- ✅ Return reason_codes array in BLOCKED responses
- ✅ Log all requests with correlation to trace_id
- ✅ Never expose stack traces in error messages

### Client MUST

- ✅ Normalize unknown status to BLOCKED
- ✅ Retry /api/audit → /api/diagnostic/metrics on BLOCKED
- ✅ Never retry /api/execute (non-idempotent)
- ✅ Never store API key in sessionStorage
- ✅ Include X-API-Key header on all requests
- ✅ Enforce 15-second timeout via AbortController

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-04 | Initial error policy (F-CONSOLE-0.1 Etapa 4) |

---

**Next Gate:** Etapa 5 (Environment Hardening & Build Test) → Etapa 6 (Reproducible Build)
