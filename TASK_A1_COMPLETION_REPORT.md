# TASK A1 — Session Persistence with Database

**Status:** ✅ COMPLETED  
**Test Results:** 13/13 PASSED  
**Implementation Time:** Phase 1 (ORM/model/repository/tests) + Phase 2 (integration/testing)

---

## Summary

Transitioned F2.3 Bearer token authentication from **in-memory session store** to **persistent database backend** (SQLite dev, PostgreSQL prod-ready).

### Deliverables

#### 1. **Database Infrastructure**
- `app/db/database.py` — SQLAlchemy ORM setup
  - Multi-database support (SQLite default, PostgreSQL via env)
  - Connection pooling configured
  - Startup initialization via `init_db()`
  - FastAPI dependency injection via `get_db()`

#### 2. **Persistence Model**
- `app/models/session.py` — SQLAlchemy declarative model
  - Session table with 7 fields: session_id (UUID PK), user_id, api_key_hash, created_at, expires_at, revoked_at, updated_at
  - Composite indices for expiry cleanup + user/key lookups
  - Helper methods: `is_valid()`, `is_revoked()`, `is_expired()`
  - All timestamps stored as naive UTC (timezone-aware at code level)

#### 3. **Data Access Layer**
- `app/db/session_repository.py` — CRUD operations with fail-closed semantics
  - `create()` — Session creation with UUID generation
  - `get_by_id()` — Direct lookup
  - `get_by_user_and_key()` — Validation lookup
  - `validate()` — Returns tuple (bool, reason_code) for audit trail
  - `revoke()` — Atomic revocation with timestamp
  - `cleanup_expired()` — Background task for expired session cleanup
  - `get_active_count()` — Observability metric
  - `get_by_user()` — Admin audit

#### 4. **Gate Integration**
- `app/gates/gate_f23_sessions_db.py` — New F2.3 implementation
  - Bearer token parsing + validation
  - User-ID header verification
  - Session binding check (user_id + api_key_hash)
  - Fail-closed: any validation failure → DENY
  - Methods: `evaluate()`, `create_session()`, `revoke_session()`

#### 5. **Application Integration**
- `app/main.py` — Modified startup
  - Added `@app.on_event("startup")` to call `init_db()` on app start
  - Ensures database tables created before first request

#### 6. **Environment Configuration**
- `.env.example` — New mandatory variables
  - `DATABASE_URL` (default: `sqlite:///./app.db`)
  - `VERITTA_ADMIN_API_KEY` (fail-closed)
  - `VERITTA_SESSION_TTL_HOURS` (default: 8h)

#### 7. **Comprehensive Test Suite**
- `tests/test_session_lifecycle.py` — 13 test scenarios
  - **TestSessionCreation:** Valid session creation, UUID format validation
  - **TestSessionValidation:** Valid, nonexistent, expired, revoked session states
  - **TestSessionRevocation:** Revocation mechanics, timestamp precedence, nonexistent handling
  - **TestSessionConcurrency:** Concurrent validation + revocation (atomic transactions)
  - **TestSessionBoundary:** Exact expiration time edge cases (1-second tolerance)
  - **TestSessionCleanup:** Expired session cleanup operations

#### 8. **Dependency Installation**
- Added `sqlalchemy` to `requirements.txt`

---

## Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0

tests/test_session_lifecycle.py::TestSessionCreation::test_create_valid_session PASSED
tests/test_session_lifecycle.py::TestSessionCreation::test_session_has_uuid_format PASSED
tests/test_session_lifecycle.py::TestSessionValidation::test_valid_session_passes_validation PASSED
tests/test_session_lifecycle.py::TestSessionValidation::test_nonexistent_session PASSED
tests/test_session_lifecycle.py::TestSessionValidation::test_expired_session PASSED
tests/test_session_lifecycle.py::TestSessionValidation::test_revoked_session PASSED
tests/test_session_lifecycle.py::TestSessionRevocation::test_revoke_sets_revoked_at PASSED
tests/test_session_lifecycle.py::TestSessionRevocation::test_revoke_nonexistent_session PASSED
tests/test_session_lifecycle.py::TestSessionRevocation::test_revocation_has_priority_over_expiration PASSED
tests/test_session_lifecycle.py::TestSessionConcurrency::test_concurrent_validation PASSED
tests/test_session_lifecycle.py::TestSessionConcurrency::test_concurrent_revoke PASSED
tests/test_session_lifecycle.py::TestSessionBoundary::test_session_expires_at_exact_time PASSED
tests/test_session_lifecycle.py::TestSessionCleanup::test_cleanup_expired_sessions PASSED

======================== 13 passed in 0.37s ========================
```

---

## Architecture Decisions

### 1. Naive UTC Timestamps
- **Why:** SQLite doesn't natively support timezone-aware DateTime; PostgreSQL does
- **How:** Store all timestamps as naive UTC in DB, convert to timezone-aware at runtime
- **Risk Mitigation:** Code always assumes DB timestamps are UTC; tests verify this assumption

### 2. Session Validation Return Tuple
- **Why:** Enforce reason_code provision in validation (audit trail requirement)
- **Pattern:** `validate(session_id) → (is_valid: bool, reason_code: Optional[str])`
- **Reason Codes:** `SESSION_INVALID`, `SESSION_EXPIRED`, `SESSION_REVOKED`

### 3. Composite Indices
- **Why:** Fast cleanup (expires_at index) + fast validation (user_id + api_key_hash index)
- **Scalability:** O(1) lookups for typical queries

### 4. Repository Pattern
- **Why:** Testable, mockable data access layer; easy to swap implementations
- **Benefit:** All CRUD logic centralized, isolated from gate logic

### 5. Atomic Transactions
- **Why:** Prevent race conditions in concurrent session operations
- **Method:** SQLAlchemy commit/rollback with query filters

---

## Next Steps (TASK A2 — Admin API)

### A2 Deliverables
1. **Endpoints:**
   - `POST /admin/sessions/revoke` — Revoke session by session_id
   - `GET /admin/sessions/{session_id}` — Get session details (admin-only)
   - `GET /admin/audit/summary` — Session audit statistics
   - `GET /admin/health` — App health + DB health

2. **Auth:** Require `VERITTA_ADMIN_API_KEY` header (X-VERITTA-ADMIN-KEY)

3. **Response Format:** JSON with trace_id, reason_codes

---

## Code Quality Checklist

✅ All timestamps timezone-aware at code level (naive at DB level)  
✅ Fail-closed validation (returns tuple with reason_code)  
✅ No implicit behavior (all choices explicit)  
✅ Fully testable (in-memory SQLite fixture)  
✅ LGPD-compliant (session binding, audit trail, no inference)  
✅ Human-in-the-loop (no automatic session cleanup in production; admin-controlled)  
✅ Documented (docstrings, inline comments)  
✅ Deterministic (UUID v4, absolute TTL, no sliding window)  

---

## Environment Variables

```bash
# Database configuration
DATABASE_URL=sqlite:///./app.db          # Dev/test default; set to postgresql://... for prod

# Admin access
VERITTA_ADMIN_API_KEY=<admin-key>        # Fail-closed; no default

# Session lifecycle
VERITTA_SESSION_TTL_HOURS=8               # Default 8-hour absolute TTL
```

---

## Files Modified/Created

| File | Action | Type |
|------|--------|------|
| `app/db/database.py` | Created | Infrastructure |
| `app/models/session.py` | Created | Model |
| `app/db/session_repository.py` | Created | Repository |
| `app/gates/gate_f23_sessions_db.py` | Created | Integration |
| `tests/test_session_lifecycle.py` | Created | Tests |
| `app/main.py` | Modified | Integration |
| `.env.example` | Modified | Configuration |
| `requirements.txt` | Modified | Dependencies |

---

## Verification

Run tests:
```bash
pytest tests/test_session_lifecycle.py -v
```

Expected: All 13 tests PASS

Check database initialization:
```bash
python -c "from app.db.database import init_db; init_db(); print('✅ DB initialized')"
```

Expected: `✅ DB initialized` (no errors)

---

## Document Index

- **P3 Docs:** [P3_DOCUMENTATION_INDEX.md](P3_DOCUMENTATION_INDEX.md)
- **Runbook:** [RUNBOOK_SAMURAI.md](RUNBOOK_SAMURAI.md)
- **Error Spec:** [ERROR_ENVELOPE.md](ERROR_ENVELOPE.md)
- **Audit Spec:** [AUDIT_LOG_SPEC.md](AUDIT_LOG_SPEC.md)
- **Sprint A Plan:** See `PROMPT CALÍOPE–APOLLO` in conversation

---

**Completed by:** GitHub Copilot (Claude Haiku 4.5)  
**Date:** 2025 (Task A1)  
**Governance:** V-COF, LGPD by design, human-in-the-loop  
