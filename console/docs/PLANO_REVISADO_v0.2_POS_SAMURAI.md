# 🏛️ PLANO DE EXECUÇÃO REVISADO — v0.2 (Post-Parecer Samurai)

**Framework:** F-CONSOLE-0.1 Phase 2 (v0.2 Planning)  
**Status:** APTO COM RESSALVAS (Samurai Approval)  
**Data:** 4 de janeiro de 2026  
**Fase:** PRE-IMPLEMENTATION (Gate Validation)

---

## 📌 Mudanças Implementadas Pós-Crítica

### Original vs Revisado

| Aspecto | Original | Revisado | Delta |
|---------|----------|----------|-------|
| Timeline | 6 semanas | 8-10 semanas | +2-4 semanas |
| Contingency | Nenhum | 2 semanas buffer | +2 semanas |
| Feature Flag | Compile-time | Runtime | ⬆️ Segurança |
| Token Storage | sessionStorage | HttpOnly/Encrypted | ⬆️ Segurança |
| Testing | Ad-hoc | 9-matrix scenarios | ⬆️ Qualidade |
| Release Strategy | Direct | Canary 1%→100% | ⬆️ Segurança |
| Rollback Plan | "Best effort" | < 5 min SLA | ⬆️ Confiabilidade |

---

## 🎯 Plano Revisado (8-10 Semanas)

### PRÉ-PHASE: Gate Validation (Semanas 0-1)

**Objetivo:** Validar pré-requisitos críticos antes de começar implementação.

**Responsabilidades:**
```
Product Manager:
  [ ] Confirmar com backend: "OAuth2 provider ready [DATE]"
  [ ] Se delay > 2 weeks: Decidir contingency
  [ ] Artefato: BACKEND_OAUTH2_CONFIRMATION.md (assinado)

Security Engineer:
  [ ] Design token storage strategy
  [ ] Design CSP headers (prevent XSS)
  [ ] Design refresh token mechanism
  [ ] Artefato: SECURITY_DESIGN_v0.2.md

DevOps / Platform:
  [ ] Design runtime feature flag
  [ ] Design canary rollout (timeline + automation)
  [ ] Design rollback procedure (< 5 min test)
  [ ] Artefato: DEPLOYMENT_STRATEGY_v0.2.md

Engineering Manager:
  [ ] Revise timeline (6 → 8-10 weeks)
  [ ] Define milestone gates
  [ ] Add contingency buffer
  [ ] Artefato: PROJECT_PLAN_v0.2_REVISED.md
```

**Gate to Phase 1:**
```
✅ Backend OAuth2 confirmation received (email)
✅ Security design document approved
✅ Deployment strategy documented
✅ Timeline revised (8+ weeks, not 6)
⚠️ If ANY missing: Return to PRE-PHASE (don't continue)
```

---

### PHASE 1: Setup & Architecture (Semanas 1-2)

**Objetivo:** Establish foundation, security, and architecture.

**Deliverables:**
```
1. Runtime Feature Flag System
   - Endpoint: GET /api/health?check_f2_3=true
   - Frontend: Fetch flag at app startup
   - Cache: 5 min TTL
   - Default: FALSE (F2.3 disabled)
   - Artefato: lib/feature-flags.ts

2. Security Implementation
   - Token storage: HttpOnly cookies (preferred) OR AES-encrypted sessionStorage
   - CSP headers: Strict-dynamic, no unsafe-inline
   - Refresh token flow: Backend provides refresh_token with access_token
   - Artefato: lib/secure-auth.ts

3. OAuth2 Integration (Mock + Real)
   - Mock provider: For local dev/testing
   - Real provider: Integration with backend (when ready)
   - Test suite: oauth2.test.ts
   - Artefato: lib/oauth2-client.ts

4. Logging & Tracing
   - Log which auth method (F2.1 vs F2.3) each request uses
   - Trace ID: Include in all requests (for metrics)
   - Dashboard mock: Show metrics structure
   - Artefato: lib/request-logging.ts

5. Metrics Definition
   - Success metric: User authenticated via F2.3 AND called /api/v1/preferences
   - Adoption metric: (F2.3 successes / Total requests) × 100%
   - SLO: ≥ 95% F2.3 success rate before v1.0 cutoff
   - Artefato: docs/METRICS_DEFINITION_v0.2.md
```

**Milestone Gate (End of Week 2):**
```
✅ Runtime feature flag working (tested: TRUE/FALSE toggle)
✅ Security design implemented (token encryption/CSP)
✅ Mock OAuth2 provider working (login/logout/refresh)
✅ Logging shows auth method per request
⚠️ If gate fails: Spend extra week on setup (no rushing)
```

---

### PHASE 2: OAuth2 + F2.3 Implementation (Semanas 2-5)

**Objective:** Implement OAuth2 login flow and F2.3 dual-mode support.

#### Milestone 2.1: OAuth2 Login Flow (Week 2-3)

**Deliverables:**
```
1. OAuth2 UI Components
   - Login button (if F2.3 enabled)
   - Login page: /login (redirect from /unauthorized)
   - Logout button: Clear tokens + redirect to /
   - Artefato: app/login/page.jsx

2. OAuth2 Backend Integration
   - GET /oauth2/authorize → Frontend redirects user to login
   - POST /oauth2/token → Backend returns {access_token, refresh_token}
   - POST /oauth2/refresh → Refresh expired token
   - Artefato: lib/oauth2-client.ts (request handlers)

3. Token Storage (Secure)
   - Access token: HttpOnly cookie (browser can't read via JS)
   - Refresh token: localStorage (long-lived, for refresh)
   - SessionStorage: Expiry time + auth method (F2.1 vs F2.3)
   - Artefato: lib/token-storage.ts

4. Error Handling
   - 401 Unauthorized → Redirect to /login
   - 403 Forbidden → Show "Access denied" message
   - Token expired → Auto-refresh (transparent to user)
   - Artefato: lib/oauth2-error-handling.ts

5. Tests
   - Unit: OAuth2 flow steps (request → response → token storage)
   - Integration: Mock backend + UI (login → authenticated)
   - E2E: Full user flow (click login → auth → redirect)
   - Artefato: tests/oauth2.test.ts (50+ test cases)
```

**Milestone Gate (End of Week 3):**
```
✅ OAuth2 login: User clicks button → Redirected to OAuth provider
✅ OAuth2 response: Token returned + stored securely
✅ Token refresh: Automatic refresh on 401
✅ Logout: Token cleared + redirect to /
✅ All 50+ tests passing
⚠️ If gate fails: Don't proceed to dual-mode (OAuth2 must work first)
```

#### Milestone 2.2: /api/v1/preferences Endpoint (Week 3-4)

**Deliverables:**
```
1. API Client (F2.3)
   - GET /api/v1/preferences (with Bearer token + X-VERITTA-USER-ID)
   - PUT /api/v1/preferences (same auth)
   - Error handling: 401/403
   - Artefato: lib/api-client-v1.ts

2. Preferences Page UI
   - Display: User preferences (theme, language, etc)
   - Edit: Form to update preferences
   - Save: Call PUT /api/v1/preferences
   - Artefato: app/preferences/page.jsx

3. Contract Validation
   - Verify response matches docs/CONTRACT.md (section 6)
   - Verify auth headers match F2.3 spec
   - Artefato: tests/contract-validation.test.ts

4. Error Scenarios
   - Missing Bearer token → 401 "Unauthorized"
   - Invalid token → 403 "Forbidden"
   - User ID mismatch → 403 "Access denied"
   - Artefato: tests/api-v1-errors.test.ts
```

**Milestone Gate (End of Week 4):**
```
✅ GET /api/v1/preferences: Returns user's preferences (F2.3 auth)
✅ PUT /api/v1/preferences: Updates preferences (F2.3 auth)
✅ 401 error: Handled gracefully (redirect to login)
✅ 403 error: Shown to user
✅ Contract compliance: Response matches docs/CONTRACT.md
⚠️ If gate fails: Revisit API design with backend
```

#### Milestone 2.3: Dual-Mode Request Handler (Week 4-5)

**Deliverables:**
```
1. Dual-Mode Logic
   - If F2.3 enabled AND token valid AND not expired: Use F2.3 (Bearer)
   - Else if F2.1 available: Use F2.1 (X-API-Key)
   - Else: Return error "No valid auth method"
   - Artefato: lib/dual-mode-fetch.ts

2. Testing Matrix (9 Scenarios)
   Test cases (exhaustive):
   
   F2.3 Enabled:
   [ ] Token valid, not expired        → Use F2.3 ✅
   [ ] Token valid, expired             → Auto-refresh → Use F2.3 ✅
   [ ] Token invalid (malformed)        → Use F2.1 fallback ✅
   [ ] No token (sessionStorage empty)  → Use F2.1 ✅
   
   F2.3 Disabled:
   [ ] API key present                  → Use F2.1 ✅
   [ ] API key missing                  → Error "No auth" ✅
   
   Mixed:
   [ ] Both F2.3 + F2.1 present        → F2.3 preferred ✅
   [ ] F2.3 expired + F2.1 present     → Use F2.1 ✅
   
   Artefato: tests/dual-mode-matrix.test.ts (9 cases)

3. Integration Tests
   - Old code (F2.1 only) still works (backward compat)
   - New code (F2.3) works when enabled
   - Migration: F2.1 → F2.3 (user logs in with OAuth2)
   - Artefato: tests/dual-mode-integration.test.ts

4. Performance
   - No additional latency (feature flag check is cached)
   - Token refresh doesn't block requests (async)
   - Artefato: performance benchmarks

5. Migration Guide v1
   - Code examples (how to use dual-mode fetch)
   - Common pitfalls (token expiry, XSS, refresh)
   - Runnable example: examples/oauth2-migration/
   - Artefato: docs/MIGRATION_GUIDE_v0.2.md
```

**Milestone Gate (End of Week 5):**
```
✅ Dual-mode logic implemented
✅ All 9 scenarios tested and passing
✅ Backward compatibility: F2.1 still works
✅ E2E: F2.1 → F2.3 migration tested
✅ Performance: No regression
⚠️ If gate fails: Debug each scenario, don't proceed to metrics
```

---

### PHASE 3: Metrics & Monitoring (Semanas 5-6)

**Objective:** Implement observability and migration tracking.

**Deliverables:**
```
1. Metrics Dashboard
   - F2.1 vs F2.3 request volume (% split)
   - Success rate by auth method
   - Token refresh rate (how often users refresh)
   - Login attempts vs successes
   - Average session duration (F2.1 vs F2.3)
   - Artefato: dashboard/metrics.tsx (mock data)

2. Logging Integration
   - Every API request logs: auth_method (F2.1|F2.3), timestamp, success
   - Log to: Console (dev), Backend (prod)
   - Trace ID: Included in every log entry
   - Artefato: lib/analytics.ts

3. Alerts & SLO
   - Alert: F2.3 errors > 5% (rollback trigger)
   - Alert: Token refresh failures > 2%
   - Alert: XSS attempt detected (CSP violation)
   - SLO: F2.3 availability ≥ 99%
   - Artefato: docs/MONITORING_PLAN_v0.2.md

4. Manual Audit Checklist
   - Sample 10 production sessions
   - Verify: F2.3 actually used (not just feature flag enabled)
   - Verify: Token refresh happened correctly
   - Verify: No XSS vulnerabilities in logs
   - Artefato: MANUAL_AUDIT_CHECKLIST.md
```

**Milestone Gate (End of Week 6):**
```
✅ Metrics dashboard working (F2.1 vs F2.3 split visible)
✅ Logging captures auth_method per request
✅ Alerts configured (F2.3 error > 5% → escalate)
✅ Manual audit checklist created (ready for canary)
```

---

### PHASE 4: Release & Canary (Semanas 6-7)

**Objective:** Release with canary strategy (1% → 100%).

**Deliverables:**
```
1. Release Checklist
   [ ] Feature flag NEXT_PUBLIC_ENABLE_F2_3 = FALSE (default)
   [ ] All tests passing (unit + integration + E2E)
   [ ] Security review passed (XSS, CSP, token storage)
   [ ] Deployment strategy approved (rollback < 5 min)
   [ ] Migration guide published with examples
   [ ] Deprecation warning in API responses (F2.1)
   [ ] Artefato: RELEASE_CHECKLIST_v0.2.md

2. Canary Deployment (Week 6)
   Phase 1 (Day 1): 1% of users → F2.3 enabled
   Phase 2 (Day 3): 10% of users (if 1% successful)
   Phase 3 (Day 5): 50% of users (if 10% successful)
   Phase 4 (Day 7): 100% of users (if 50% successful)
   
   Success criteria per phase:
   - F2.3 error rate < 2%
   - No escalated support tickets
   - No XSS/security incidents
   - Manual audit: No anomalies
   
   Failure criteria (ROLLBACK):
   - F2.3 error rate > 5% → Rollback immediately
   - 3+ support escalations → Rollback
   - Any security incident → Rollback immediately
   
   Artefato: CANARY_PLAN_v0.2.md

3. Rollback Plan (< 5 min)
   [ ] Feature flag NEXT_PUBLIC_ENABLE_F2_3 = FALSE
   [ ] Redeploy (automated via CI/CD)
   [ ] Verify: F2.3 disabled (health check)
   [ ] Notify users: "F2.3 temporarily unavailable"
   [ ] Incident post-mortem (within 24h)
   Artefato: ROLLBACK_PROCEDURE_v0.2.md

4. Communication
   [ ] Blog post: "v0.2 introduces OAuth2 support (opt-in)"
   [ ] Email to F2.1 users: "You can now upgrade to F2.3"
   [ ] Slack announcement (internal team)
   [ ] Deprecation notice: "F2.1 will be removed in v1.0 (Sep 2026)"
   Artefato: COMMUNICATION_PLAN_v0.2.md
```

**Milestone Gate (End of Week 7):**
```
✅ Canary 1% successful (F2.3 error rate < 2%, 0 rollbacks)
✅ Rollback tested (< 5 min from start to finish)
✅ Communication published (blog, email, Slack)
✅ Metrics dashboard live (public to team)
```

---

### PHASE 5: Contingency Buffer (Semanas 7-10)

**Objective:** Absorb delays, unexpected issues, and final polish.

**Use cases for buffer:**
```
If OAuth2 provider delayed:
  → Use mock provider for additional testing
  → Delay integration 2 weeks (still ship on time)

If security review found issues:
  → Fix (2 weeks buffer allows this)
  → Re-test (canary again if needed)

If metrics unreliable:
  → Redesign metrics
  → Run manual audit (buffer time available)

If bugs found in production:
  → Rollback (1 hour)
  → Fix (2-3 days)
  → Re-release (1 day)
```

**Use buffer wisely:**
- Don't extend timeline beyond week 10
- If buffer not used by week 9: Ship anyway
- Document why buffer was/wasn't used (lessons learned)

---

## 🏁 Timeline Visual

```
Week 1    [PRE-PHASE: Gate Validation        ] ← Must pass before Phase 1
Week 2    [PHASE 1: Setup & Architecture    ] 
Week 3    [PHASE 2.1: OAuth2 Login          ]
Week 4    [PHASE 2.2: /api/v1/preferences   ]
Week 5    [PHASE 2.3: Dual-Mode + PHASE 3   ]
Week 6    [PHASE 4: Release & Canary        ]
Week 7    [PHASE 4: Canary Complete         ]
Week 8-10 [CONTINGENCY BUFFER               ]

Release Target: End of Week 7
Hard Deadline: End of Week 10 (max)
```

---

## 📋 Risk Mitigation Tracking

### Tracked Risks (From Samurai Review)

| Risk | Mitigation | Week | Owner | Status |
|------|-----------|------|-------|--------|
| OAuth2 delay | Confirm + contingency | 0 | PM | Gate |
| XSS / Token | HttpOnly + CSP | 1 | Security | Phase 1 |
| Feature flag | Runtime + canary | 1 | DevOps | Phase 1 |
| Dual-mode bugs | 9-matrix tests | 4 | QA | Phase 2.3 |
| Metrics unreliable | KPI definition | 5 | Data | Phase 3 |
| Timeline | 8-10 weeks + buffer | 0 | PM | Gate |
| F2.1 deprecation | Communication plan | 6 | PM | Phase 4 |
| Migration guide | Examples + runnable | 5 | Eng | Phase 2.3 |

**Tracking:** Weekly risk review (every Monday standup)

---

## 🎯 Success Criteria (Definition of Done)

**v0.2 is COMPLETE when:**

```
✅ Functional:
   • OAuth2 login/logout working end-to-end
   • /api/v1/preferences GET/PUT working (F2.3)
   • Dual-mode fetch working (F2.1 OR F2.3)
   • Feature flag can be toggled (runtime)

✅ Tested:
   • Unit: 100+ tests, 95%+ pass rate
   • Integration: 50+ tests
   • E2E: 20+ user flows
   • Contract: Response matches docs/CONTRACT.md

✅ Secured:
   • XSS audit: 0 vulnerabilities
   • Token storage: HttpOnly (or encrypted)
   • CSP: Strict-dynamic implemented
   • Secrets: No hardcoded keys

✅ Documented:
   • Migration guide (with examples)
   • Deprecation notice (F2.1 removal date)
   • API documentation (CONTRACT.md)
   • Runnable example (examples/oauth2-migration/)

✅ Deployed:
   • Canary 1% successful
   • Rollback < 5 min verified
   • Monitoring live
   • Metrics dashboard visible

✅ Communicated:
   • Blog post published
   • Email sent to users
   • Slack announcement (internal)
   • Status page updated
```

---

## 📊 Effort Estimation (Revised)

| Phase | Duration | Team | Effort |
|-------|----------|------|--------|
| PRE | 1 week | PM, Security, DevOps | 10 FTE-days |
| 1 | 2 weeks | Eng, Security | 30 FTE-days |
| 2.1 | 2 weeks | Eng, QA | 40 FTE-days |
| 2.2 | 2 weeks | Eng, QA | 30 FTE-days |
| 2.3 | 2 weeks | Eng, QA | 40 FTE-days |
| 3 | 1 week | Eng, Data | 15 FTE-days |
| 4 | 1 week | Eng, DevOps, PM | 20 FTE-days |
| 5 | 3 weeks | All (buffer) | 30 FTE-days |
| **TOTAL** | **10 weeks** | | **215 FTE-days** |

**Team Size:** 4-5 people  
**FTE:** 2 full-time engineers + part-time (PM, QA, DevOps, Security)  
**Cost Impact:** +50% vs original 6-week plan

---

## 🏛️ Final Veredito (Post-Plano Revisado)

### Status: ✅ **APTO PARA EXECUÇÃO**

**Condições:**

1. ✅ Pré-requisito Gate (Semana 1):
   - [ ] Backend OAuth2 confirmation
   - [ ] Security design approved
   - [ ] Deployment strategy documented
   - [ ] Timeline agreed (8-10 weeks)

2. ✅ Milestone Gates (Semanais):
   - [ ] Week 2: Feature flag + OAuth2 mock working
   - [ ] Week 4: /api/v1/preferences endpoint done
   - [ ] Week 5: Dual-mode + tests passing
   - [ ] Week 7: Canary successful

3. ✅ Release Gates:
   - [ ] Feature flag default = FALSE
   - [ ] Canary 1% successful
   - [ ] Rollback < 5 min tested
   - [ ] Migration guide published

**Risco Residual:** 🟢 BAIXO (if all mitigations applied)

---

**Plano Revisado Completo**

Assinado: Arquiteto Samurai  
Data: 4 de janeiro de 2026  
Status: ✅ APROVADO (com revisões)

> **"Mais tempo, mais testes, mais segurança. Esse é o caminho para v0.2 bem-sucedida."**

