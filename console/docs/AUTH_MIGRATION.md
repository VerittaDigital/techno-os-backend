# AUTH_MIGRATION.md — F2.1 → F2.3 Roadmap

**Framework:** F-CONSOLE-0.1 Etapa 5  
**Status:** Planning (Etapa 5 gates)  
**Timeline:** v0.1 (current) → v0.2 → v1.0  

---

## Executive Summary

Techno OS Console is currently built on **F2.1 (Legacy API Key Authentication)** with a planned migration to **F2.3 (Bearer Token + User ID)** by v1.0.

This document outlines:
1. Current architecture (F2.1)
2. Target architecture (F2.3)
3. Migration timeline & milestones
4. Backward compatibility guarantees
5. Testing strategy

---

## 1. Current Architecture (F2.1 — v0.1)

### Authentication Mechanism

**X-API-Key Header (Legacy)**

```http
POST /api/execute
X-API-Key: sk_test_abc123xyz
Content-Type: application/json

{
  "command": "GET_STATUS"
}
```

### Characteristics

| Aspect | F2.1 |
|--------|------|
| **Method** | Static API key in header |
| **Scope** | Application-level (not user-scoped) |
| **Lifecycle** | Long-lived (manual rotation needed) |
| **Storage** | Compiled client bundle (public) |
| **Security Level** | Low (suitable for v0.1 only) |
| **Use Case** | Testing, gated environments, non-sensitive |

### Deployment

```
┌─────────────────┐
│  Compiled JS    │
│  (public)       │
│  API_KEY="..."  │
└────────┬────────┘
         │
    ┌────v────────────┐
    │ HTTP Request    │
    │ X-API-Key: ...  │
    └────┬────────────┘
         │
    ┌────v──────────────┐
    │  Backend (F2.1)   │
    │  Validates header │
    │  Returns response │
    └───────────────────┘
```

### Known Limitations

1. **No user context** — All requests are anonymous (app-level)
2. **No audit trail** — Cannot track who executed what
3. **No rate limiting** — Could be abused if key is leaked
4. **No expiration** — Key rotation is manual
5. **Public key exposure** — Embedded in compiled client code

---

## 2. Target Architecture (F2.3 — v1.0)

### Authentication Mechanism

**Bearer Token + X-VERITTA-USER-ID Header (Preferred)**

```http
GET /api/v1/preferences
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-VERITTA-USER-ID: user_123
Content-Type: application/json
```

### Characteristics

| Aspect | F2.3 |
|--------|------|
| **Method** | JWT Bearer token + user context |
| **Scope** | User-scoped (action attributed to user) |
| **Lifecycle** | Short-lived (OAuth2 + refresh token) |
| **Storage** | Memory (sessionStorage, cleared on logout) |
| **Security Level** | High (suitable for production) |
| **Use Case** | Production, multi-user, auditable |

### Deployment

```
┌──────────────────────────┐
│  Login Server            │
│  (OAuth2 Provider)       │
│  Returns: JWT + refresh  │
└────────┬─────────────────┘
         │
    ┌────v────────────────────────┐
    │  Client (In Memory)         │
    │  localStorage: refresh_token│
    │  sessionStorage: Bearer     │
    └────┬───────────────────────┘
         │
    ┌────v──────────────┐
    │ HTTP Request      │
    │ Auth: Bearer ...  │
    │ X-VERITTA-USER-ID │
    └────┬──────────────┘
         │
    ┌────v──────────────────────┐
    │  Backend (F2.3)           │
    │  Validate JWT (sig, exp)  │
    │  Extract user from claims │
    │  Return user-scoped data  │
    └───────────────────────────┘
```

### Advantages

1. **User context** — Requests are attributed to specific users
2. **Audit trail** — Full logging of who did what
3. **Built-in rate limiting** — Per-user rate limits possible
4. **Automatic expiration** — Tokens expire after short period
5. **Refresh mechanism** — No long-term secrets in client

---

## 3. Migration Timeline

### v0.1 (Current) — F2.1 Only

**Status:** Live  
**Auth:** X-API-Key (legacy)  
**Endpoints:** /api/execute, /api/audit, /process (deprecated)

**Responsibility:**
- [x] Implement F2.1 (already done)
- [x] Document CONTRACT.md with F2.1 expectations
- [x] Unit tests for timeout/error handling
- [ ] Gate environment setup (local dev)

### v0.2 (Q1 2026) — F2.1 + F2.3 Dual Support

**Planned:** January-March 2026  
**Auth:** X-API-Key (legacy) + Bearer token (new, optional)  
**Endpoints:** Add /api/v1/preferences (F2.3), keep /api/execute (F2.1)  

**Responsibility:**
- [ ] Implement OAuth2 client (redirect to login)
- [ ] Add /api/v1/preferences endpoint (F2.3)
- [ ] Dual-mode request handler (F2.1 OR F2.3)
- [ ] Migration guide for developers
- [ ] Backward compatibility tests
- [ ] Beta period (2 weeks)

**Deployment:**
```
Request → Check for Bearer token
  ├─ If Bearer present → Use F2.3 (user-scoped)
  └─ If no Bearer → Fall back to F2.1 (app-level)
```

### v0.3 (Q2 2026) — F2.3 Preferred (F2.1 Deprecated)

**Planned:** April-June 2026  
**Auth:** Bearer token (preferred) + X-API-Key (deprecated warning)  
**Endpoints:** Full F2.3 support, F2.1 marked deprecated  

**Responsibility:**
- [ ] Deprecation warning in API responses
  ```json
  {
    "status": "APPROVED",
    "trace_id": "api-200",
    "x-deprecated": "F2.1 authentication will be removed in v1.0"
  }
  ```
- [ ] Metrics: track F2.1 vs F2.3 usage
- [ ] Timeline: announce F2.1 removal (6+ weeks notice)

### v1.0 (Q3 2026) — F2.3 Only (F2.1 Removed)

**Planned:** July-September 2026  
**Auth:** Bearer token + X-VERITTA-USER-ID (required)  
**Endpoints:** All endpoints require F2.3  

**Responsibility:**
- [ ] Remove F2.1 support completely
- [ ] Return 401 for missing Authorization header
- [ ] Enforce JWT signature validation
- [ ] Implement refresh token mechanism
- [ ] Multi-user audit logging

**Breaking Changes:**
```
❌ X-API-Key header: REMOVED
❌ /process endpoint: REMOVED (use /api/execute with Bearer)
✅ All endpoints require Authorization header
✅ All responses include X-VERITTA-USER-ID context
```

---

## 4. Migration Path for Developers

### Step 1: Run on v0.1 (Current) with F2.1

```javascript
// lib/api-client.ts (v0.1)
async function executeCommand(command: string) {
  return fetch('/api/execute', {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.NEXT_PUBLIC_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ command }),
  });
}
```

### Step 2: Prepare for F2.3 (v0.2+)

```javascript
// lib/api-client.ts (v0.2)
async function executeCommand(command: string) {
  // Try F2.3 first (if user is logged in)
  const token = sessionStorage.getItem('bearer_token');
  const userId = sessionStorage.getItem('user_id');
  
  if (token && userId) {
    return fetch('/api/execute', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-VERITTA-USER-ID': userId,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ command }),
    });
  }
  
  // Fall back to F2.1 (legacy)
  return fetch('/api/execute', {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.NEXT_PUBLIC_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ command }),
  });
}
```

### Step 3: Migrate to F2.3 Only (v1.0)

```javascript
// lib/api-client.ts (v1.0)
async function executeCommand(command: string) {
  const token = sessionStorage.getItem('bearer_token');
  const userId = sessionStorage.getItem('user_id');
  
  if (!token || !userId) {
    // Redirect to login
    window.location.href = '/login';
    return;
  }
  
  return fetch('/api/execute', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-VERITTA-USER-ID': userId,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ command }),
  });
}
```

---

## 5. Backward Compatibility Guarantees

### v0.2 (Dual Support)

| Scenario | v0.1 Code | v0.2 Behavior |
|----------|-----------|---------------|
| F2.1 request (X-API-Key only) | ✅ Works | ✅ Works (legacy path) |
| F2.3 request (Bearer + user_id) | ❌ Would fail | ✅ Works (new path) |
| Mixed headers (both F2.1 + F2.3) | N/A | Uses F2.3 (preferred) |

**Rule:** v0.2 will NOT break existing v0.1 deployments.

### v0.3+ (F2.3 Preferred)

| Scenario | v0.1 Code | v0.3+ Behavior |
|----------|-----------|----------------|
| F2.1 request | ✅ Works | ⚠️ Works (deprecated warning) |
| F2.3 request | ❌ Would fail | ✅ Works |

**Rule:** v0.3+ will continue supporting F2.1 but recommend migration.

### v1.0 (F2.3 Only)

| Scenario | v0.1 Code | v1.0 Behavior |
|----------|-----------|---------------|
| F2.1 request | ✅ Works | ❌ Fails (401) |
| F2.3 request | ❌ Would fail | ✅ Works |

**Rule:** v1.0 is a BREAKING CHANGE. 6+ weeks notice required.

---

## 6. Testing Strategy

### F2.1 Tests (Current — v0.1)

```javascript
describe('F2.1 Authentication', () => {
  test('Valid API key → request succeeds', async () => {
    // Test with NEXT_PUBLIC_API_KEY
  });
  
  test('Missing API key → 401 response', async () => {
    // Test without X-API-Key header
  });
  
  test('Invalid API key → 403 response', async () => {
    // Test with fake key
  });
});
```

### F2.3 Tests (Planned — v0.2+)

```javascript
describe('F2.3 Authentication', () => {
  test('Valid Bearer token → request succeeds', async () => {
    // Test with valid JWT + user_id
  });
  
  test('Missing Bearer token → 401 response', async () => {
    // Test without Authorization header
  });
  
  test('Expired token → 401 response', async () => {
    // Test with expired JWT
  });
  
  test('Invalid JWT signature → 401 response', async () => {
    // Test with tampered token
  });
});
```

### Dual-Mode Tests (v0.2)

```javascript
describe('Dual-Mode (F2.1 + F2.3)', () => {
  test('F2.1 request when F2.3 available → F2.3 preferred', async () => {
    // Send both headers; verify F2.3 is used
  });
  
  test('F2.1 fallback when F2.3 unavailable', async () => {
    // Send only F2.1; verify it works
  });
});
```

---

## 7. Dependency Checklist

### v0.2 OAuth2 Implementation

- [ ] **npm package:** `@next-auth/core` or `next-auth`
- [ ] **OAuth2 provider:** GitHub, Google, or custom
- [ ] **Token storage:** Secure sessionStorage + localStorage (refresh)
- [ ] **Logout:** Clear both session and refresh tokens
- [ ] **Error handling:** Re-auth on 401, force logout on 403

### v0.3 Metrics & Monitoring

- [ ] **F2.1 usage tracking** (for deprecation timeline)
- [ ] **F2.3 adoption rate** (for migration milestones)
- [ ] **Error rates by auth method**
- [ ] **Failed login attempts** (for security)

### v1.0 Production Readiness

- [ ] **JWT library:** `jsonwebtoken` (verify signature)
- [ ] **Rate limiting:** Per-user buckets (optional)
- [ ] **Audit logging:** User + action + timestamp
- [ ] **Session management:** Refresh token rotation

---

## 8. Rollout Checklist

### Before v0.2 Release

- [ ] Implement F2.3 endpoint (/api/v1/preferences)
- [ ] Implement OAuth2 login flow
- [ ] Update CONTRACT.md with F2.3 details
- [ ] Add migration guide for developers
- [ ] Beta test with internal team
- [ ] Set up feature flag (NEXT_PUBLIC_ENABLE_F2_3 = false by default)
- [ ] Monitor F2.1 requests (baseline)

### Before v0.3 Release

- [ ] Enable F2.3 by default (feature flag = true)
- [ ] Add deprecation warnings to F2.1 responses
- [ ] Publish "Upgrade to F2.3" guide
- [ ] Announce F2.1 removal timeline (6+ weeks)
- [ ] Track adoption metrics

### Before v1.0 Release

- [ ] Remove F2.1 support
- [ ] Enforce JWT validation on all endpoints
- [ ] Implement refresh token mechanism
- [ ] Run production load tests
- [ ] Verify all endpoints working with F2.3
- [ ] Announce: "v1.0 requires Bearer token"

---

## 9. FAQ & Troubleshooting

### Q: What happens to existing v0.1 deployments when v0.2 is released?

**A:** They continue to work. v0.2 is backward compatible with F2.1. No changes required until v1.0.

### Q: Can I use both F2.1 and F2.3 on the same v0.2 instance?

**A:** Yes! v0.2 supports both. The backend will use F2.3 if both headers are present (F2.3 preferred).

### Q: What's the difference between "deprecated" (v0.3) and "removed" (v1.0)?

**A:** 
- **Deprecated (v0.3):** Still works, but warnings shown. Developers should migrate.
- **Removed (v1.0):** No longer works. Requests fail with 401.

### Q: Do I need to update my code before v1.0?

**A:** Yes, eventually. But you have until v1.0 release (6+ weeks notice from v0.3).

### Q: How do I test F2.3 locally before it's released?

**A:** Use the feature flag: `NEXT_PUBLIC_ENABLE_F2_3=true` (planned for v0.2).

---

## 10. References

- CONTRACT.md (current authentication rules)
- ERROR_POLICY.md (error handling during migration)
- docs/COPILOT_INSTRUCTIONS.md (governance framework)
- Backend parecer (F2.1/F2.3 endpoint definitions)

---

**Document Version:** 0.1  
**Status:** Planning (Etapa 5 gate)  
**Next Review:** v0.2 implementation (Q1 2026)

