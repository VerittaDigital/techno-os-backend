# P3 Documentation Index

**Phase:** P3 — Normative Documentation + Mandatory Environment Variables + Operational Runbook  
**Status:** ✅ Complete  
**Date:** 2025-12-23

---

## Quick Links

### 🚀 Getting Started

- **[README.md](README.md)** — Main quickstart guide (clone → setup → run → test)
- **[.env.example](.env.example)** — Environment variable reference (copy to .env)

### 📋 API Contracts

- **[docs/ERROR_ENVELOPE.md](docs/ERROR_ENVELOPE.md)** — Error response structure, reason codes, client patterns
- **[docs/AUDIT_LOG_SPEC.md](docs/AUDIT_LOG_SPEC.md)** — Audit trail (JSONL) format, invariants, offline tools

### 🔧 Operations

- **[docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md)** — Smoke tests, diagnostics, incident response
- **[P3_IMPLEMENTATION_SUMMARY.md](P3_IMPLEMENTATION_SUMMARY.md)** — Detailed implementation report

---

## File Organization

```
techno-os-backend/
├── README.md                      ← Main documentation (start here)
├── .env.example                   ← Environment variables (mandatory + optional)
├── P3_IMPLEMENTATION_SUMMARY.md   ← Implementation report
├── docs/
│   ├── ERROR_ENVELOPE.md          ← Error response contract
│   ├── AUDIT_LOG_SPEC.md          ← Audit trail specification
│   └── RUNBOOK_SAMURAI.md         ← Operational runbook
└── app/
    ├── main.py                    ← FastAPI app entry point
    ├── auth.py                    ← Authentication gates
    ├── audit_log.py               ← Audit logging
    └── ...
```

---

## Documentation Roles

### For Developers (Building Integrations)

1. Read: [README.md](README.md) § "API Examples"
2. Reference: [docs/ERROR_ENVELOPE.md](docs/ERROR_ENVELOPE.md) for error handling
3. Check: [.env.example](.env.example) for required headers

### For DevOps / SRE (Deployment & Monitoring)

1. Setup: Follow [README.md](README.md) § "Quickstart"
2. Configure: [.env.example](.env.example) (mandatory vars)
3. Validate: [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) § "Pre-Launch Checklist"
4. Monitor: [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) § "Production Diagnostics"

### For Security / Compliance (Audit & Privacy)

1. Review: [docs/AUDIT_LOG_SPEC.md](docs/AUDIT_LOG_SPEC.md) (P1.1 invariant, privacy rules)
2. Verify: [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) § "Audit Log Integrity Check"
3. Check: [README.md](README.md) § "Security — Production Deployment"

### For On-Call Engineers (Troubleshooting)

1. Incident response: [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) § "Part 4"
2. Query audit log: [docs/AUDIT_LOG_SPEC.md](docs/AUDIT_LOG_SPEC.md) § "Reading & Validation"
3. Understand errors: [docs/ERROR_ENVELOPE.md](docs/ERROR_ENVELOPE.md) § "Reason Codes"

---

## Key Principles

### 🔐 Security (Fail-Closed)

- Missing `VERITTA_BETA_API_KEY` → Server returns 500 on startup
- All authentication gates default to DENY
- No secrets in error messages or audit logs

### 📊 Audit (P1.1 Invariant)

- All decisions logged to JSONL audit trail
- `profile_hash` never empty (governance fingerprint)
- `trace_id` links HTTP requests to audit entries

### 🛡️ Privacy (LGPD by Design)

- No raw payloads in audit or errors
- No stack traces exposed to clients
- No PII stored; only SHA256 digests
- All data is purpose-limited and ephemeral

### 👤 Human-in-the-Loop

- IA (Copilot) as instrument, not decision-maker
- All governance decisions are auditable
- Users maintain control over authentication & authorization
- No automatic actions without human review

---

## Environment Variables (Quick Reference)

**Mandatory:**
- `VERITTA_BETA_API_KEY` — API authentication (fail-closed if missing)
- `VERITTA_PROFILES_FINGERPRINT` — Governance hash (P1.1)

**Recommended:**
- `VERITTA_AUDIT_LOG_PATH` — Audit trail location (default: ./audit.log)
- `VERITTA_AUDIT_DIGEST_ENABLED` — Include SHA256 in audit (default: true)

**Optional:**
- `VERITTA_HOST`, `VERITTA_PORT` — Binding address
- `VERITTA_MAX_PAYLOAD_SIZE`, `VERITTA_EXECUTOR_TIMEOUT_S` — Limits
- `LLM_PROVIDER`, `LLM_API_KEY` — For agentic pipeline

See [.env.example](.env.example) for full list.

---

## Testing Checklist

- [ ] **Pre-Launch:** Run [RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) § "Part 1" checklist
- [ ] **Smoke Tests:** Execute [RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) § "Part 2" scripts
- [ ] **Unit Tests:** `pytest tests/ -v` (expect 243+ passed)
- [ ] **Audit Log:** Verify P1.1 invariant (profile_hash never empty)
- [ ] **Error Handling:** Test [ERROR_ENVELOPE.md](docs/ERROR_ENVELOPE.md) reason codes
- [ ] **Production:** Review security checklist in [README.md](README.md)

---

## Support & Troubleshooting

| Issue | Where to Look |
|-------|---------------|
| "How do I set up the backend?" | [README.md](README.md) § Quickstart |
| "What env vars are required?" | [.env.example](.env.example) or [README.md](README.md) § Mandatory Variables |
| "How do I handle API errors?" | [docs/ERROR_ENVELOPE.md](docs/ERROR_ENVELOPE.md) |
| "How do I read the audit log?" | [docs/AUDIT_LOG_SPEC.md](docs/AUDIT_LOG_SPEC.md) § Reading & Validation |
| "How do I run smoke tests?" | [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) § Part 2 |
| "API is returning 500, what do I do?" | [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) § Part 4.1 |
| "What does reason code X mean?" | [docs/ERROR_ENVELOPE.md](docs/ERROR_ENVELOPE.md) § Reason Codes |
| "Is this LGPD compliant?" | [docs/AUDIT_LOG_SPEC.md](docs/AUDIT_LOG_SPEC.md) § Privacy Constraints |

---

## Implementation Status

| Component | Status | File |
|-----------|--------|------|
| **Quickstart Documentation** | ✅ | [README.md](README.md) |
| **Environment Variables** | ✅ | [.env.example](.env.example) |
| **Error Envelope Spec** | ✅ | [docs/ERROR_ENVELOPE.md](docs/ERROR_ENVELOPE.md) |
| **Audit Log Spec** | ✅ | [docs/AUDIT_LOG_SPEC.md](docs/AUDIT_LOG_SPEC.md) |
| **Operational Runbook** | ✅ | [docs/RUNBOOK_SAMURAI.md](docs/RUNBOOK_SAMURAI.md) |
| **Implementation Summary** | ✅ | [P3_IMPLEMENTATION_SUMMARY.md](P3_IMPLEMENTATION_SUMMARY.md) |

---

**Last Updated:** 2025-12-23  
**Phase:** P3 Complete ✅
