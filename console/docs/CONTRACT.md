# CONTRACT.md — Techno OS Console v0.1

**Effective:** January 4, 2026  
**Status:** PRODUCTION-MINIMUM GOVERNANCE  
**Scope:** Client ↔ Backend API Contract  

---

## 1. Version Strategy

### Current Version: 0.1.0

```
Semantic Versioning: MAJOR.MINOR.PATCH

0.1.0
│ │ └─ PATCH: Bug fixes, internal improvements (no API change)
│ └─── MINOR: New endpoints, new optional fields, new error codes
└───── MAJOR: Breaking changes (removed endpoints, type changes, status enum changes)
```

### Versioning Rules (Etapa 3)

1. **PATCH Releases (0.1.X)**
   - ✅ Bug fixes to existing endpoint logic
   - ✅ New fields added as OPTIONAL (with defaults)
   - ✅ New error_code values in existing reason_codes array
   - ❌ NO changes to required fields
   - ❌ NO changes to response status type

2. **MINOR Releases (0.X.0)**
   - ✅ New optional endpoints
   - ✅ New optional query parameters
   - ✅ New optional response fields (backward compatible)
   - ✅ Deprecation of old endpoints (with warning period)
   - ❌ NO breaking removal of fields
   - ❌ NO type changes to existing fields

3. **MAJOR Releases (X.0.0)**
   - ✅ Breaking changes with advance notice (6+ weeks)
   - ✅ Removal of deprecated endpoints
   - ✅ Type changes to existing fields
   - ⚠️  ONLY after deprecation period and client migration

### Deprecation Policy

When removing an endpoint (MAJOR version):

1. **Week 1-2:** Add deprecation notice to OpenAPI schema
   ```yaml
   x-deprecated: true
   deprecated: true
   ```

2. **Week 3-6:** Publish migration guide; redirect to new endpoint
   ```yaml
   x-migrated-to: /api/new-endpoint
   ```

3. **Week 7+:** Remove old endpoint; release MAJOR version

---

## 2. Stability Guarantees

### Guaranteed (Backward Compatible)

**Status Enum (Forever)**
- Current: `APPROVED | BLOCKED | EXPIRED | WARNING | NEUTRAL`
- New statuses may be added, but existing values NEVER change
- Unknown values → normalized to `BLOCKED` (client-side fail-closed)

**Response Structure**
```json
{
  "status": "...",           // GUARANTEED — always present
  "ts_utc": "...",           // GUARANTEED — always ISO 8601
  "trace_id": "...",         // GUARANTEED — always present (for audit trail)
  "reason_codes": [...],     // GUARANTEED — always array (may be empty)
  "new_field_v1_X": "..."    // OPTIONAL — only in v1.X+
}
```

**Trace ID Format**
- Client expects: alphanumeric + hyphens
- Backend must provide valid trace_id in ALL success responses
- Used for audit trail and debugging

**Timeout Behavior**
- Client hardcoded: AbortController at 15 seconds
- Backend must respond within 15 seconds for all endpoints
- Timeout → HTTP 0, status: BLOCKED (fail-closed)

---

## 3. Client-Side Fail-Closed Assumptions

**These behaviors are HARDCODED in the client. Backend must comply.**

### /api/execute
- If response missing or empty → status: `BLOCKED` (not error)
- If timeout (>15s) → Treated as BLOCKED
- If network error → Treated as BLOCKED
- Unknown status value → Normalized to BLOCKED

### /api/audit
- If response status is BLOCKED → Auto-fallback to `/api/diagnostic/metrics`
- If BOTH fail → Return empty array [] (not error)
- If parse error → Return empty array []

### /api/memory
- If response status is BLOCKED or data missing → return null
- If parse error → return null

### /process (Legacy)
- Missing `NEXT_PUBLIC_API_BASE_URL` → Error before fetch
- 401/403 → Mapped to "Autenticacao falhou"

---

## 4. Authentication & Headers

### Required Header: X-API-Key

**Rule:** ALL requests must include `X-API-Key` header

```http
X-API-Key: ${NEXT_PUBLIC_API_KEY}
Content-Type: application/json
```

**Backend Validation:**
- Missing header → 401 Unauthorized
- Invalid key → 403 Forbidden
- Valid key → Proceed

**Security Note:**
- API key is public (embedded in compiled client code)
- Should be short-lived or rotated frequently
- NOT a substitute for OAuth2/JWT (use for v1.0+)

---

## 5. Error Response Contract

### Standard Error Response

**When to return error status:**
```json
{
  "status": "BLOCKED",          // or EXPIRED, WARNING
  "trace_id": "api-403",        // REQUIRED
  "reason_codes": [             // REQUIRED (may be empty)
    "API_KEY_INVALID",
    "RATE_LIMIT_EXCEEDED"
  ],
  "message": "Autenticacao falhou"  // REQUIRED in error path
}
```

### HTTP Status Codes

| Code | Scenario | Client Handles As |
|------|----------|---|
| 200 | Success OR business logic BLOCKED | Parse status field |
| 400 | Invalid request (malformed JSON) | HTTP error; fallback to BLOCKED |
| 401 | Missing API key | HTTP error; message: "Autenticacao falhou" |
| 403 | Invalid API key | HTTP error; message: "Autenticacao falhou" |
| 500 | Server error | HTTP error; fallback to BLOCKED |
| 0 | Timeout (>15s) OR network error | Client NEVER sees this; treated as BLOCKED |

### Reason Codes (Extensible)

Current known codes (from compiled analysis):
- `API_BLOCKED` — Generic blocking
- `API_KEY_INVALID` — Authentication failed
- `RATE_LIMITED` — Rate limit exceeded

Future codes (v0.2+):
- `VALIDATION_FAILED`
- `RESOURCE_NOT_FOUND`
- (Will be documented in MINOR releases)

---

## 6. Endpoint Evolution & Backend Parecer Integration

### Backend Endpoints (DEV SENIOR Parecer v1.0)

**Source:** DEV SENIOR Backend (2026-01-04)  
**Status:** F9.9-A SELADA (ab04ef0), F9.9-B SELADA (7141cad)  
**Veredito:** APTO PARA EXECUÇÃO

| # | Método | Endpoint | Auth | Tipo | Status |
|----|--------|----------|------|------|--------|
| 1 | POST | /process | F2.1 | Legacy | DEPRECATED |
| 2 | GET | /health | Public | Standard | ✅ |
| 3 | GET | /metrics | Public | Standard | ✅ |
| 4 | GET | /api/v1/preferences | F2.3 | Standard | ✅ |
| 5 | PUT | /api/v1/preferences | F2.3 | Standard | ✅ |
| 6 | POST | /api/admin/sessions/revoke | F2.1 | Admin | ✅ |
| 7 | GET | /api/admin/sessions/{id} | F2.1 | Admin | ✅ |
| 8 | GET | /api/admin/audit/summary | F2.1 | Admin | ✅ |
| 9 | GET | /api/admin/health | F2.1 | Admin | ✅ |

### Console Legacy Endpoints (Compiled-in Client)

| Endpoint | Purpose | Status |
|----------|---------|--------|
| /api/execute | Execute command (internal) | Embedded in client |
| /api/audit | Fetch audit log (internal) | Embedded in client |
| /api/diagnostic/metrics | Fallback for audit | Embedded in client |
| /api/memory | Fetch execution snapshot | Embedded in client |

**Note:** Console endpoints are for UI state management. Backend endpoints (above) are the source of truth.

### /api/execute — Guaranteed Interface

**Current (v0.1):**
```json
POST /api/execute
{
  "command": "GET_STATUS",
  "session_id": "optional_string"
}

→ 200 OK
{
  "status": "APPROVED|BLOCKED|...",
  "ts_utc": "2026-01-04T12:00:00Z",
  "trace_id": "api-200",
  "reason_codes": []
}
```

**What can change (MINOR):**
- ✅ Add new optional fields to request
- ✅ Add new optional fields to response
- ✅ Add new reason_codes

**What CANNOT change (MAJOR required):**
- ❌ Remove command field
- ❌ Change command pattern from `^[A-Z_]+$`
- ❌ Remove status/trace_id from response
- ❌ Change StatusType enum

### /api/v1/preferences — Backend Standard Endpoint

**Current (v0.1):**
```json
GET /api/v1/preferences
Headers: {
  "Authorization": "Bearer {token}",
  "X-VERITTA-USER-ID": "{user_id}"
}

→ 200 OK
{
  "user_id": "user_123",
  "preferences": {
    "theme": "dark",
    "language": "pt-BR"
  }
}
```

**Auth Mechanism:** F2.3 (Bearer token + X-VERITTA-USER-ID)

### /api/admin/sessions/revoke — Admin Endpoint

**Current (v0.1):**
```json
POST /api/admin/sessions/revoke
Headers: {
  "X-API-Key": "{api_key}"
}
Body: {
  "session_id": "sess_abc123"
}

→ 200 OK
{
  "session_id": "sess_abc123",
  "revoked": true
}
```

**Auth Mechanism:** F2.1 (X-API-Key, legacy)

### /api/audit — Guaranteed Interface (Legacy)

**Current (v0.1):**
```json
GET /api/audit?filter=all&limit=50

→ 200 OK
[
  {
    "timestamp": "2026-01-04T11:59:00Z",
    "action": "API_CALL",
    "result": "SUCCESS",
    "state": "APPROVED",
    "execution_id": "exec_xyz"
  }
]
```

**Fallback Guarantee:**
- If this endpoint returns BLOCKED, client WILL retry `/api/diagnostic/metrics`
- Backend must ensure `/api/diagnostic/metrics` can serve as fallback
- Response shape must match for seamless fallback

---

## 7. Traceability & Audit Trail

### Trace ID Requirement

Every response must include `trace_id`:
```json
{
  "status": "APPROVED",
  "trace_id": "api-200",     // REQUIRED — used for debugging
  "ts_utc": "2026-01-04T12:00:00Z"
}
```

**Client-side use:**
- Stored in session for debugging
- Displayed in UI (users can reference for support)
- NOT stored in persistent logs (security)

**Backend-side use:**
- Must be unique per request (or at minimum per time window)
- Should correlate with server logs
- Format: recommendation is `api-{http_status}` or UUID

---

## 8. Storage & Session Management

### Client-Side Storage

**Whitelist (ONLY these fields allowed in sessionStorage):**
```
✅ route, endpoint, method, clickTime, resultTime, elapsedSec
✅ httpStatusShown, traceIdShown, messageLiteral, reasonCodesShown, storedAt
❌ API_KEY (strictly prohibited)
❌ Authorization headers (strictly prohibited)
❌ session_id or user_id (to be confirmed in v1.0)
```

**Security Rule:**
- API key NEVER stored in sessionStorage
- Any storage containing "api_key" or "X-API-Key" is SECURITY ERROR
- Client-side validation prevents leakage

---

## 9. Breaking Changes & Migration Path

### Known Blockers for v1.0

**These require MAJOR version bump & migration period:**

1. **OAuth2/JWT Authentication** (instead of X-API-Key)
2. **User-scoped sessions** (instead of anonymous API key)
3. **Persistent audit log** (currently in-memory/disposable)
4. **Rate limiting policies** (not yet implemented)
5. **API versioning header** (Accept: application/vnd.techno.v1+json)

### Migration Timeline (Hypothetical)

```
v0.1 (Now)         → Minimal viable; compiled-source only; hardcoded timeout
  ↓
v0.2 (Q1 2026)     → Add /api/sessions; optional OAuth2
  ↓
v0.3 (Q2 2026)     → Add /api/metrics; new reason codes
  ↓
v1.0 (Q3 2026)     → OAuth2 required; deprecate X-API-Key; require versioning header
  ↓
v2.0 (2027)        → Remove X-API-Key; multi-tenant support
```

---

## 10. Validation & Testing

### Client Responsibilities
- ✅ Validate all response status fields (unknown → BLOCKED)
- ✅ Enforce 15-second timeout via AbortController
- ✅ Implement fallback for /api/audit → /api/diagnostic/metrics
- ✅ Never store API keys in sessionStorage
- ✅ Always include X-API-Key header

### Backend Responsibilities
- ✅ Return all responses within 15 seconds
- ✅ Include trace_id in all 200 responses
- ✅ Return 401/403 for authentication failures
- ✅ Validate request body before processing
- ✅ Never change StatusType enum without major version

### Contract Verification (CI/CD)

**Etapa 5-6 will add:**
```bash
# Check OpenAPI compliance
npm run validate:openapi

# Check no secrets in compiled bundle
npm run check:secrets

# Test fail-closed behavior
npm run test:timeout
npm run test:network-error
npm run test:malformed-response
```

---

## 11. Support & Escalation

### For Ambiguities

If response doesn't match CONTRACT.md:

1. **Check OpenAPI Schema** (`openapi/console-v0.1.yaml`)
2. **Check INVENTORY.md** (what client actually expects)
3. **Check ERROR_POLICY.md** (error handling rules)
4. **Escalate with trace_id** (for debugging)

### Known Gaps (Requires Backend Confirmation)

- [ ] Exact semantics of `reason_codes` (when to include which codes)
- [ ] Fallback behavior of `/api/diagnostic/metrics` (does it exist? Same schema?)
- [ ] `/api/memory` null semantics (when to return null vs empty object)
- [ ] Session ID handling (is session_id optional or required?)
- [ ] Timeout recovery (should retry be automatic or client-initiated?)

---

## 12. Document History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-04 | Initial contract (F-CONSOLE-0.1 Etapa 3) |

---

## Appendix: OpenAPI Compliance

This CONTRACT.md is derived from OpenAPI schema in `openapi/console-v0.1.yaml`.

**Fields marked with:**
- `x-source: inferred-from-compiled-code` — Inferred from client expectations
- `x-requires-backend-confirmation: true` — Needs server validation

**To validate compliance:**
```bash
npm install -g swagger-cli
swagger-cli validate openapi/console-v0.1.yaml
```

---

**Document Version:** 0.1  
**Status:** READY FOR BACKEND REVIEW  
**Next Gate:** Etapa 4 (ERROR_POLICY.md) → Etapa 5 (Hardening) → Etapa 6 (Build)
