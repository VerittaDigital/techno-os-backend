# 🎯 PROPOSTA: PHASE 1 IMPLEMENTATION PLAN

**Para:** Arquiteto Samurai  
**De:** Engineering Team  
**Data:** 4 janeiro 2026  
**Ref:** PRÉ-PHASE Execution Complete → PHASE 1 Ready to Start

---

## 📋 EXECUTIVE SUMMARY

Once Gate 1 (OAuth2 confirmation) is received from backend:

```
TIMELINE:
  Jan 5:     All 5 gates ✅ PASSED
  Jan 5:     Team kick-off (30 min)
  Jan 6-20:  PHASE 1 IMPLEMENTATION (2 weeks)
  
DELIVERABLES:
  ✅ Runtime Feature Flag System (lib/feature-flags.ts)
  ✅ Security Implementation (lib/secure-auth.ts)
  ✅ OAuth2 Integration (lib/oauth2-client.ts + mock provider)
  ✅ Logging & Tracing (lib/request-logging.ts)
  ✅ Metrics Definition (docs/METRICS_DEFINITION_v0.2.md)

GATE TO PHASE 2:
  ✅ Feature flag working (toggle TRUE/FALSE locally)
  ✅ Security design implemented
  ✅ Mock OAuth2 provider functional
  ✅ Logging captures auth_method per request
  ⚠️ If gate fails: Extra week for fixes (no rushing)
```

---

## 🔧 PHASE 1 WORK BREAKDOWN

### Task 1: Runtime Feature Flag System (Days 1-2)

**Owner:** Senior Engineer  
**Complexity:** Low  
**Dependencies:** None

**What:**
```typescript
// lib/feature-flags.ts
export interface FeatureFlags {
  F2_3_ENABLED: boolean;
}

export async function getFeatureFlags(): Promise<FeatureFlags> {
  // Option A: Env var (simple, for MVP)
  if (process.env.NEXT_PUBLIC_ENABLE_F2_3 === 'true') {
    return { F2_3_ENABLED: true };
  }
  
  // Option B: Runtime endpoint (future)
  // const response = await fetch('/api/health?check_f2_3=true');
  // return response.json();
  
  return { F2_3_ENABLED: false };
}

// Usage in app:
const flags = await getFeatureFlags();
if (flags.F2_3_ENABLED) {
  // Use OAuth2 login
} else {
  // Use existing auth (or no auth for v0.1)
}
```

**Deliverables:**
- [x] lib/feature-flags.ts (50 LOC)
- [x] tests/feature-flags.test.ts (unit tests)
- [x] app/page.jsx updated (check flag on mount)

**Acceptance Criteria:**
```
✅ Feature flag can be toggled via NEXT_PUBLIC_ENABLE_F2_3
✅ Default value: FALSE (F2.3 disabled)
✅ Unit tests: 100% coverage
✅ Local test: npm run dev + set env var = flag changes
```

---

### Task 2: Security Implementation (Days 2-4)

**Owner:** Security Engineer  
**Complexity:** High  
**Dependencies:** None (but informs Task 3)

**What:**

#### Token Storage Strategy
```typescript
// lib/token-storage.ts
export interface TokenStorage {
  setAccessToken(token: string, expiresIn: number): void;
  getAccessToken(): string | null;
  setRefreshToken(token: string): void;
  getRefreshToken(): string | null;
  clearTokens(): void;
}

// Implementation Option 1: HttpOnly Cookies (PREFERRED)
// - Browser cannot read via JS (secure)
// - Backend sets via Set-Cookie header
// - Automatic inclusion in requests
// - XSS-resistant

// Implementation Option 2: AES-Encrypted sessionStorage (FALLBACK)
// - If HttpOnly not available
// - Encrypt with AES-256-GCM (Node.js crypto)
// - Store in sessionStorage (expires on tab close)
// - Lower security, but still acceptable
```

#### CSP Headers
```
// next.config.js
headers: [
  {
    key: 'Content-Security-Policy',
    value: "default-src 'self'; script-src 'strict-dynamic' 'nonce-{random}'; style-src 'nonce-{random}';"
  }
]
```

#### Token Refresh Mechanism
```typescript
// lib/token-refresh.ts
export async function ensureValidToken(): Promise<string> {
  const token = getAccessToken();
  
  if (!token) {
    throw new Error('No token');
  }
  
  if (isExpired(token)) {
    const newToken = await refreshToken(getRefreshToken());
    setAccessToken(newToken);
    return newToken;
  }
  
  return token;
}

// Middleware: Auto-refresh on 401
// lib/api-interceptor.ts
fetch(url, {
  headers: {
    'Authorization': `Bearer ${await ensureValidToken()}`
  }
})
.catch(async (err) => {
  if (err.status === 401) {
    // Auto-refresh and retry
    const token = await refreshToken();
    return fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
  }
  throw err;
});
```

**Deliverables:**
- [x] lib/token-storage.ts (100 LOC)
- [x] lib/token-refresh.ts (100 LOC)
- [x] lib/csp-headers.ts (50 LOC)
- [x] next.config.js updated (CSP headers)
- [x] tests/security.test.ts (50 test cases)

**Acceptance Criteria:**
```
✅ HttpOnly cookies set correctly (no XSS bypass)
✅ CSP headers prevent inline scripts (strict-dynamic)
✅ Token refresh transparent to user (auto-retry)
✅ 401 errors handled gracefully (redirect to login)
✅ Security audit: 0 XSS vulnerabilities
```

---

### Task 3: OAuth2 Integration (Days 3-5)

**Owner:** Senior Engineer  
**Complexity:** Medium  
**Dependencies:** Task 2 (security design)

**What:**

#### Mock OAuth2 Provider
```typescript
// lib/mock-oauth2-provider.ts
export class MockOAuth2Provider {
  // Simulate backend OAuth2 server
  
  async authorize(params: {
    client_id: string;
    redirect_uri: string;
    state: string;
    scope: string;
  }): Promise<void> {
    // Redirect to login page
    window.location.href = `/login?state=${params.state}`;
  }
  
  async token(params: {
    grant_type: 'authorization_code' | 'refresh_token';
    code?: string;
    refresh_token?: string;
  }): Promise<TokenResponse> {
    return {
      access_token: generateJWT({ sub: 'user-123' }),
      refresh_token: generateToken(),
      expires_in: 3600,
      token_type: 'Bearer'
    };
  }
  
  async refreshToken(refresh_token: string): Promise<TokenResponse> {
    // Return new access_token
  }
}

// Usage:
const provider = new MockOAuth2Provider();
const token = await provider.token({ grant_type: 'authorization_code', code: '...' });
```

#### OAuth2 Client
```typescript
// lib/oauth2-client.ts
export class OAuth2Client {
  constructor(private provider: OAuth2Provider) {}
  
  async login(): Promise<void> {
    const { authorize_endpoint, client_id, redirect_uri } = this.provider.config;
    const state = generateRandomString();
    
    window.location.href = `${authorize_endpoint}?` +
      `client_id=${client_id}&` +
      `redirect_uri=${redirect_uri}&` +
      `state=${state}&` +
      `scope=openid+profile+email`;
  }
  
  async handleCallback(code: string): Promise<void> {
    const { token_endpoint } = this.provider.config;
    const response = await fetch(token_endpoint, {
      method: 'POST',
      body: JSON.stringify({ grant_type: 'authorization_code', code }),
      headers: { 'Content-Type': 'application/json' }
    });
    
    const { access_token, refresh_token, expires_in } = await response.json();
    
    // Store tokens securely (HttpOnly/encrypted)
    setAccessToken(access_token, expires_in);
    setRefreshToken(refresh_token);
    
    // Redirect to home
    window.location.href = '/';
  }
  
  async logout(): Promise<void> {
    clearTokens();
    window.location.href = '/';
  }
}
```

#### Login Page
```typescript
// app/login/page.jsx
export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  
  useEffect(() => {
    // Check if callback from OAuth2 provider
    const code = new URLSearchParams(window.location.search).get('code');
    if (code) {
      oauth2Client.handleCallback(code).then(() => router.push('/'));
    }
  }, []);
  
  const handleLogin = async () => {
    setIsLoading(true);
    try {
      await oauth2Client.login();
    } catch (err) {
      console.error('Login failed:', err);
      setIsLoading(false);
    }
  };
  
  return (
    <div>
      <h1>Login</h1>
      <button onClick={handleLogin} disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login with OAuth2'}
      </button>
    </div>
  );
}
```

**Deliverables:**
- [x] lib/mock-oauth2-provider.ts (200 LOC)
- [x] lib/oauth2-client.ts (150 LOC)
- [x] app/login/page.jsx (100 LOC)
- [x] tests/oauth2-client.test.ts (100 test cases)

**Acceptance Criteria:**
```
✅ Mock provider works locally
✅ Login flow: Click button → OAuth2 redirect → Callback → Authenticated
✅ Logout flow: Clear tokens → Redirect to /
✅ Token refresh: Automatic on 401
✅ 100+ test cases covering all scenarios
```

---

### Task 4: Logging & Tracing Infrastructure (Days 4-5)

**Owner:** Engineer  
**Complexity:** Low  
**Dependencies:** Task 1 (feature flag), Task 3 (auth method)

**What:**

```typescript
// lib/request-logging.ts
export interface RequestLog {
  timestamp: string;
  method: string;
  url: string;
  auth_method: 'F2_3' | 'F2_1' | 'NONE';
  status: number;
  duration_ms: number;
  trace_id: string;
  user_id?: string;
  error?: string;
}

export function logRequest(log: RequestLog): void {
  console.log({
    ...log,
    message: `[${log.auth_method}] ${log.method} ${log.url} → ${log.status} (${log.duration_ms}ms)`
  });
  
  // Send to backend (in production)
  // if (process.env.NODE_ENV === 'production') {
  //   sendToLoggingBackend(log);
  // }
}

// Usage in API interceptor:
const startTime = Date.now();
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Trace-ID': traceId
  }
});

logRequest({
  timestamp: new Date().toISOString(),
  method: 'GET',
  url: url,
  auth_method: flags.F2_3_ENABLED ? 'F2_3' : 'F2_1',
  status: response.status,
  duration_ms: Date.now() - startTime,
  trace_id: traceId,
  user_id: getUserId()
});
```

**Deliverables:**
- [x] lib/request-logging.ts (80 LOC)
- [x] lib/request-interceptor.ts (100 LOC)
- [x] tests/logging.test.ts (50 test cases)

**Acceptance Criteria:**
```
✅ Every API request logs auth_method
✅ Log includes: timestamp, status, duration, trace_id
✅ Logging doesn't block requests
✅ Can toggle logging on/off via env var
```

---

### Task 5: Metrics Definition (Days 5)

**Owner:** Data/Analytics Engineer  
**Complexity:** Low  
**Dependencies:** Task 4 (logging)

**What:**

```markdown
# Metrics Definition v0.2

## Success Metric

Definition:
  User authenticated via F2.3 AND successfully called /api/v1/preferences

KPI:
  "F2.3 Adoption Rate = (F2.3 authenticated users / Total users) × 100%"

Target:
  By end of canary: ≥ 50% F2.3 adoption
  By v1.0 release: ≥ 95% F2.3 adoption

Calculation:
  F2.3_Users = COUNT(requests WHERE auth_method = 'F2_3')
  Total_Users = COUNT(requests WHERE auth_method IN ('F2_3', 'F2_1'))
  Adoption = (F2.3_Users / Total_Users) × 100%

## Error Rate Metric

Definition:
  Percentage of F2.3 requests that fail (401, 403, 500)

Target:
  < 2% during canary
  < 1% in production

Alert:
  If error rate > 5% → Trigger rollback

## Token Refresh Metric

Definition:
  How often users need to refresh tokens (token expiry)

Target:
  < 10% per day (most users don't expire token in single session)

Alert:
  If > 30% per day → Token TTL too short

## Session Duration Metric

Definition:
  Average time user stays authenticated

F2.1 Baseline:
  ~4 hours (legacy behavior)

F2.3 Target:
  ≥ 4 hours (OAuth2 refresh extends this)

Alert:
  If < 2 hours → Investigate token refresh logic
```

**Deliverables:**
- [x] docs/METRICS_DEFINITION_v0.2.md (written)
- [x] dashboard/metrics-mock.tsx (mock dashboard)

**Acceptance Criteria:**
```
✅ All 4 metrics defined
✅ Calculation formulas documented
✅ Alert thresholds set
✅ Dashboard structure ready (real data in Phase 3)
```

---

## 📊 PHASE 1 TIMELINE (2 Weeks)

```
Week 1:
  Day 1: Kick-off + setup (0.5 day)
         Feature flag system + unit tests (1 day)
         Security design review (0.5 day)
  
  Day 2: Token storage + encryption (1 day)
         CSP headers + security tests (1 day)
  
  Day 3: OAuth2 provider design (0.5 day)
         Mock provider + login page (1.5 days)
  
  Day 4: OAuth2 client + integration tests (1 day)
         Logging infrastructure (1 day)
  
  Day 5: Metrics definition doc (0.5 day)
         Integration testing + bug fixes (1.5 days)

Week 2:
  Day 1-2: Full integration testing (2 days)
           - Feature flag + auth together
           - Mock OAuth2 end-to-end
           - Security validation
  
  Day 3-4: Performance testing + optimization (2 days)
           - No regression vs v0.1
           - Token refresh doesn't block
           - Logging performance
  
  Day 5: PHASE 1 Gate Review (1 day)
         - Verify all deliverables
         - All tests passing
         - Documentation complete
         - Ready for PHASE 2
```

---

## ✅ PHASE 1 GATE (End of Week 2)

**Go/No-Go Checklist:**

```
FUNCTIONAL:
  ✅ Feature flag can be toggled (TRUE/FALSE)
  ✅ OAuth2 mock login works end-to-end
  ✅ Logout clears tokens
  ✅ Token auto-refresh on 401

SECURITY:
  ✅ Token storage: HttpOnly cookies (or encrypted)
  ✅ CSP headers: Strict-dynamic, no inline scripts
  ✅ Secrets: No hardcoded API keys
  ✅ Security audit: 0 XSS vulnerabilities

TESTING:
  ✅ Unit tests: 100+ passing
  ✅ Integration tests: 50+ passing
  ✅ Coverage: ≥ 95%

LOGGING:
  ✅ Auth method logged per request
  ✅ Trace ID present in all logs
  ✅ Logging doesn't block requests

METRICS:
  ✅ KPIs defined
  ✅ Calculation formulas documented
  ✅ Dashboard structure ready

DOCUMENTATION:
  ✅ README updated (setup + feature flag)
  ✅ Migration guide skeleton (for Phase 2)
  ✅ Security design doc (completed)
  ✅ Metrics definition doc (completed)
```

**If Gate Passes:**
- ✅ Move to PHASE 2 (OAuth2 login + /api/v1/preferences)

**If Gate Fails:**
- ⚠️ Spend extra week (week 3) fixing
- ⚠️ Timeline shifts to week 4 start for PHASE 2
- ⚠️ Buffer absorbs this (8-10 weeks accounts for it)

---

## 📊 RESOURCE ALLOCATION

**Team (5 people, 2 weeks):**

| Role | Time | Tasks |
|------|------|-------|
| Senior Engineer | 50% | Feature flag, OAuth2 client, logging |
| Security Engineer | 30% | Token storage, CSP, security tests |
| QA Engineer | 30% | Test suite, security audit |
| Engineer | 20% | Logging infrastructure, mock provider |
| Product Manager | 10% | Coordination, gate review |

**Total Effort:** ~60 FTE-days (for 2-week phase)

---

## 🎯 SUCCESS CRITERIA FOR SAMURAI

**Phase 1 is successful when:**

```
✅ All 5 deliverables completed
✅ All tests passing (unit + integration)
✅ No security vulnerabilities
✅ Performance baseline established
✅ Team is confident for PHASE 2
✅ Gate passed unanimously
```

---

## 🏛️ SAMURAI'S OVERSIGHT

**Weekly Check-in:**

```
Monday Standup:
  • What did we complete last week?
  • What's blocked?
  • Risk updates?

Deliverable Review:
  • Code quality
  • Test coverage
  • Documentation

Gate Validation:
  • All criteria met?
  • Ready to advance to next phase?
```

---

## 📝 PHASE 1 SUCCESS = PHASE 2 READY

Once PHASE 1 gate is passed:

```
PHASE 2 (Weeks 3-5):
  ✅ OAuth2 login flow (F2.3)
  ✅ /api/v1/preferences endpoint (GET/PUT)
  ✅ Dual-mode logic (F2.3 preferred, none needed for fallback)
  ✅ 50+ test cases
  ✅ Migration guide v1
```

---

**PHASE 1 Proposal**

Ready for Samurai approval once Gate 1 confirmed (OAuth2 provider).

Proposto por: Engineering Team  
Data: 4 janeiro 2026  
Status: Pending Samurai review + Gate 1 confirmation
