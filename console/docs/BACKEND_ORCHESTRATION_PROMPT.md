```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  TECHNO OS CONSOLE — BACKEND INTEGRATION ORCHESTRATION                      ║
║  F-CONSOLE-0.1 Framework | Console v0.1.0 | Date: 2026-01-04               ║
║                                                                              ║
║  TO: COPILOT - Backend Dev Senior (Claude Sonnet)                           ║
║  FROM: COPILOT - Console Dev Lead (Claude Haiku)                            ║
║  RE: Backend Implementation & API Contract Alignment                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

## ⚠️ IMPORTANT CONTEXT (Backend Reality Check)

The current backend (**Techno OS**) already has:
  ✅ FastAPI-based core architecture
  ✅ X-API-Key authentication middleware
  ✅ Canonical audit log with reason_codes (G0, G8, G10, etc.)
  ✅ UUID v4 trace_id enforced at middleware level
  ✅ Fail-closed error normalization (unknown status → BLOCKED)
  ✅ Response schema conventions established

However, current **public endpoints do NOT yet match** the console contract:
  ❌ /api/execute (command execution) — NOT exposed
  ❌ /api/audit (audit log access) — NOT exposed
  ❌ /api/memory (memory stats) — NOT exposed
  ❌ /api/diagnostic/metrics (fallback endpoint) — NOT exposed

---

### 🎯 THIS IS NOT A GREENFIELD BACKEND TASK

**This is a CONTRACT ALIGNMENT & ADAPTER task:**

✓ Do NOT redesign governance, audit, or auth layers  
✓ Do NOT simplify fail-closed semantics  
✓ Do NOT change UUID trace_id or reason_code structure  
✗ Do NOT use different response normalization  
✗ Do NOT create new authentication schemes  

**Focus narrowly on:**
1. Mapping/wrapping existing internal capabilities
2. Implementing missing PUBLIC endpoints per OpenAPI
3. Preserving existing fail-closed semantics exactly as-is
4. Adapter layer between internal representation → public contract

---

## 🎯 CONTEXT & MISSION

The **Techno OS Console (v0.1.0)** has completed the **F-CONSOLE-0.1 governance 
framework** and is **PRODUCTION-READY**. 

Your role: Implement the **public API endpoints** to fulfill the published contract
and enable full console ↔ backend integration.

**Current Status:**
- Console: ✅ Ready for deployment (all 6 etapas passed, 12/12 tests)
- Backend: ⏳ Pending public endpoint implementation per contract
- Framework: ✅ F-CONSOLE-0.1 (governance + error handling + AI guidelines)

---

## 📋 CRITICAL INFORMATION NEEDED (3 Sections)

### SECTION 1️⃣: BACKEND INVENTORY (Factual Status)

Please provide a **factual inventory** of what currently exists:

```
AUTHENTICATION LAYER
  ├─ Current impl: X-API-Key middleware (yes/no?)
  ├─ Location: [file path]
  ├─ Key validation logic: [brief description]
  └─ Can be reused for /api/execute, /api/audit, /api/memory? (yes/no)

AUDIT LOG LAYER
  ├─ Current impl: UUID trace_id + reason_codes (yes/no?)
  ├─ Location: [file path]
  ├─ reason_code enums: [list: G0, G8, G10, ...]
  ├─ Storage: [database table? in-memory?]
  └─ Can be exposed via /api/audit endpoint? (yes/no)

FAIL-CLOSED ERROR HANDLING
  ├─ Current impl: (unknown status → BLOCKED) (yes/no?)
  ├─ Location: [file path]
  ├─ HTTP status code normalization: [brief description]
  └─ Can be reused for new endpoints? (yes/no)

MEMORY/DIAGNOSTICS LAYER
  ├─ Current impl: Memory stats available? (yes/no?)
  ├─ Location: [file path]
  ├─ Available metrics: [list]
  └─ Can be exposed via /api/memory endpoint? (yes/no)

COMMAND EXECUTION LAYER
  ├─ Current impl: Command execution available? (yes/no?)
  ├─ Location: [file path]
  ├─ Execution engine: [description]
  ├─ Result format: [schema]
  └─ Can be exposed via /api/execute endpoint? (yes/no)
```

---

### SECTION 2️⃣: ENDPOINT MAPPING (Current → Contract)

Create a **gap matrix** showing:

```
CURRENT BACKEND                          CONSOLE CONTRACT
────────────────────────────────────────────────────────────

Endpoint A: [current name]          →   POST /api/execute
  Status: Exists? (yes/no)
  Gap: [what's missing to match contract?]
  Effort: [small/medium/large]

Endpoint B: [current name]          →   GET /api/audit
  Status: Exists? (yes/no)
  Gap: [what's missing?]
  Effort: [small/medium/large]

Endpoint C: [current name]          →   GET /api/memory
  Status: Exists? (yes/no)
  Gap: [what's missing?]
  Effort: [small/medium/large]

Endpoint D: [current name]          →   GET /api/diagnostic/metrics
  Status: Exists? (yes/no)
  Gap: [what's missing?]
  Effort: [small/medium/large]

[Any other mappings?]
```

---

### SECTION 3️⃣: EXPLICIT GAP LIST

List **gaps between current backend and console contract**:

```
🔴 CRITICAL GAPS (must fix before integration):
  1. [Gap description]
  2. [Gap description]
  ...

🟡 MINOR GAPS (nice to have, workaround acceptable):
  1. [Gap description]
  2. [Gap description]
  ...

🟢 NO GAPS (ready to expose as-is):
  [Endpoint(s) ready]
```

---

## 📊 DETAILED ENDPOINT SPEC (Reference)

The console expects these endpoints per **openapi/console-v0.1.yaml**:

```
┌─ ENDPOINT INVENTORY ─────────────────────────────────────────┐
│                                                              │
│ POST /api/execute                                           │
│   ├─ Purpose: Execute command                               │
│   ├─ Auth: X-API-Key header (required)                      │
│   ├─ Request: { command: string, sessionId: string }        │
│   └─ Response: {                                            │
│        status: APPROVED|BLOCKED|EXPIRED|WARNING|NEUTRAL,   │
│        trace_id: string (UUID for audit),                  │
│        ts_utc: ISO8601 timestamp,                           │
│        reason_codes: string[] (if status ≠ APPROVED)        │
│      }                                                       │
│                                                              │
│ GET /api/audit                                              │
│   ├─ Purpose: Fetch audit log                               │
│   ├─ Fallback: /api/diagnostic/metrics (if audit fails)    │
│   ├─ Query: ?filter=*, ?limit=100                           │
│   ├─ Auth: X-API-Key header (required)                      │
│   └─ Response: {                                            │
│        entries: [{...}],                                    │
│        trace_id: string,                                    │
│        ts_utc: ISO8601 timestamp,                           │
│        status: APPROVED|BLOCKED|...,                        │
│        reason_codes: string[]                               │
│      }                                                       │
│                                                              │
│ GET /api/memory                                             │
│   ├─ Purpose: Get memory usage                              │
│   ├─ Auth: X-API-Key header (required)                      │
│   └─ Response: {                                            │
│        used: number (bytes),                                │
│        available: number (bytes),                           │
│        status: APPROVED|BLOCKED|...,                        │
│        trace_id: string,                                    │
│        ts_utc: ISO8601 timestamp                            │
│      }                                                       │
│                                                              │
│ GET /api/diagnostic/metrics (FALLBACK for /api/audit)      │
│   └─ Returns diagnostic data when audit endpoint fails      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Validation Requirements:**

✓ Each response includes `status` field (not just HTTP status)  
✓ `status` is one of: APPROVED|BLOCKED|EXPIRED|WARNING|NEUTRAL  
✓ Every response has `trace_id` (UUID for audit/debugging)  
✓ Every response has `ts_utc` (ISO8601 timestamp)  
✓ BLOCKED/EXPIRED responses include `reason_codes` array  
✓ Authentication via X-API-Key header  
✓ /api/audit has fallback chain to /api/diagnostic/metrics  

---

## 🔒 ERROR HANDLING & FAIL-CLOSED BEHAVIOR

The console implements **fail-closed error handling**:
- If status is unknown → treat as BLOCKED
- If connection times out (>15s) → treat as BLOCKED
- If network error occurs → treat as BLOCKED
- If response is malformed → treat as BLOCKED

**Backend must preserve these semantics.**

**Questions:**

✓ How does backend currently handle validation errors? (returns which HTTP code?)
✓ How does backend currently handle auth failures? (G0_auth_not_configured → HTTP code?)
✓ How does backend currently handle malformed requests? (G10_BODY_PARSE_ERROR → HTTP code?)
✓ Does backend have timeouts defined? (recommended: ≥15s for console AbortController)
✓ Are error responses already normalized (status/trace_id/ts_utc)?
✓ Do you use reason_codes for error classification? (already implemented?)

---

## 4️⃣ DEPLOYMENT & INTEGRATION READINESS

**Current Setup (Console Side):**
```
docker-compose.yml configuration:
  ├─ Port: 127.0.0.1:3001 (console)
  ├─ Expected backend: https://api.verittadigital.com
  ├─ Network: techno-net (external, must exist)
  ├─ API Key: X-API-Key header (how is it provisioned?)
  └─ Environment: NEXT_PUBLIC_API_URL (configurable)
```

**Questions:**

✓ Will backend run in Docker? (docker-compose for both console + backend?)
✓ Shared network (techno-net)? Or separate networks?
✓ Database: External? Docker service? In-memory?
✓ API Key provisioning: hardcoded, env var, or external auth service?
✓ Production API endpoint: https://api.verittadigital.com correct?
✓ Any CI/CD pipeline already in place?

---

## ✅ RESPONSE REQUIREMENTS (Expected Output)

Please respond with **exactly these 3 sections**:

### 1. BACKEND INVENTORY
Fill out the inventory template above (factual status of current code)

### 2. ENDPOINT GAP MATRIX
Show which endpoints exist, which don't, what gaps remain

### 3. CRITICAL GAPS LIST
Prioritized list of what must be done for integration

---

## 📚 REFERENCE MATERIALS

**Available for your review in d:\Projects\techno-os-console\:**

| Document | Purpose |
|----------|---------|
| openapi/console-v0.1.yaml | Complete endpoint spec |
| docs/ERROR_POLICY.md | Fail-closed behavior definition |
| docs/INVENTORY.md | Evidence of endpoints in console |
| docs/CONTRACT.md | Versioning & deprecation rules |
| docs/COPILOT_INSTRUCTIONS.md | Code standards for COPILOT |
| docs/F-CONSOLE-0.1_COMPLETION.md | Console current state |

---

## 🎯 ACCEPTANCE CRITERIA

Backend work is **COMPLETE & READY FOR INTEGRATION** when:

✅ All 5 endpoints implemented (or mapped via adapters)  
✅ Response schemas match contract exactly  
✅ Authentication via X-API-Key (no redesign needed)  
✅ Error handling preserves fail-closed semantics  
✅ Audit trail logged for all requests  
✅ No hardcoded secrets (all config via environment)  
✅ Docker-ready (compatible with docker-compose)  
✅ Gap matrix completed (shows what was done vs. spec)  
✅ Documentation updated (README, API docs, setup)  

---

## 🎓 FINAL NOTE

> **"IA como instrumento. Humano como centro."**

This is **contract alignment**, not redesign.

Preserve existing governance layers.  
Expose internal capabilities cleanly.  
Map to public contract exactly.  

The console is waiting. Let's build the bridge.

---

**Status: Ready to send to Claude Sonnet. Awaiting your factual inventory. 🚀**
```
