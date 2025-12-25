# ADR-001: Phase 0 Infrastructure Decisions (SELADO)

**Date**: 2025-12-25  
**Status**: ACCEPTED ✅  
**Context**: Phase 0 CI/CD + Docker implementation  
**Decision Maker**: Technical Lead (Samurai Approval)

---

## 1. Python Version: 3.12 (Stable LTS)

### Decision
- **CI/CD validates**: Python 3.12 (production)
- **Local dev**: Python 3.14 permitted (future-proofing)
- **Dockerfile**: Python 3.12-slim ONLY
- **Rationale**: LTS stability, all dependencies validated

### Implementation
- GitHub Actions: `PYTHON_VERSION: "3.12"`
- Dockerfile: `FROM python:3.12-slim`
- requirements.txt: No version locks (compatibility managed in CI)

### Rollback Criterion
If 3.12 shows regressions in staging load tests → roll back to 3.11

---

## 2. Docker Registry: ghcr.io (GitHub Container Registry)

### Decision
- **Registry**: ghcr.io (native GitHub integration)
- **Image path**: `ghcr.io/your-org/techno-os-backend`
- **Tag strategy**: 
  - Immutable: `sha-<commit-hash>` (always pushed)
  - Release: `staging` (for staging deployments)
  - Candidate: `release-candidate` (for RC testing)
  - ❌ Avoid `:latest` as sole tag

### Implementation
- GitHub Actions step: `docker/build-push-action@v4`
- Uses `GITHUB_TOKEN` (auto-rotated, built-in)
- Artifacts signed via SLSA provenance

### Benefits
- Native GitHub integration (no external credentials)
- Dependency scanning auto-enabled
- Commit-traceable deployments
- Privacy: Private images allowed

---

## 3. Database: PostgreSQL Staging-Ready

### Decision
- **docker-compose.yml**: PostgreSQL 15 always (staging mirror)
- **Local development option**: Can use SQLite if preferred (not enforced)
- **Staging/Production**: PostgreSQL 15-alpine mandatory
- **Rationale**: Multi-instance scaling, compliance, test → prod parity

### Implementation
- `docker-compose.yml` includes postgres:15-alpine service
- `.env.example` defaults to PostgreSQL connection string
- SQLAlchemy ORM handles both (no code changes needed)
- Healthcheck: `pg_isready` for orchestration

### Migration Path
1. Dev: Try both (SQLite + PostgreSQL in compose)
2. Staging: PostgreSQL only
3. Prod: PostgreSQL + replica standby

---

## 4. Docker Tests: CI-Only (No Multi-Stage)

### Decision
- **Tests location**: GitHub Actions (ubuntu-latest environment)
- **Docker build**: Runtime-only (no pytest in image)
- **Test service**: Separate PostgreSQL container in CI
- **Rationale**: Separation of concerns, smaller production images, faster CI feedback

### Implementation
- `.github/workflows/ci.yml`:
  - Services block includes postgres:15-alpine
  - Step 1: pytest run (validates code)
  - Step 2: docker build (if tests pass)
  - Step 3: docker push (to ghcr.io)

### Image Size Benefit
- Production image: ~350 MB (no test deps)
- vs Multi-stage approach: ~450 MB (with pytest, coverage, etc.)

---

## 5. Health Check: INCLUDED (Lightweight, No Logic)

### Decision
- **Endpoint**: `GET /health` (already exists in app/main.py)
- **Response**: `{"status": "ok"}` (no DB calls, no executor logic)
- **Healthcheck in Dockerfile**: 
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
  ```
- **Usage**: Docker orchestration, K8s readiness probes, load balancer checks
- **Rationale**: Fail-fast detection, standard DevOps practice

### Current Status
✅ Endpoint already exists (no code changes needed)

---

## Three Samurai Adjustments (Incorporated)

### A. Python 3.14 Local Caveat
✅ **Decided**: Keep 3.14 local if preferred, CI will validate 3.12 only
- Protects production stability
- Allows teams to experiment locally

### B. GHCR Tag Strategy (Hardened)
✅ **Decided**: Avoid `:latest`, use immutable `sha-<hash>` tags
- Prevents accidental rollbacks (no `:latest` ambiguity)
- Audit trail: Every deployment linked to commit SHA
- Rollback: Easy (just redeploy previous SHA tag)

### C. Healthcheck No Logic
✅ **Decided**: Keep /health simple (process alive only)
- No database queries
- No executor dependencies
- Observability comes in Phase 2

---

## Implementation Status

| Component | Status | Files |
|-----------|--------|-------|
| GitHub Actions CI/CD | ✅ DONE | `.github/workflows/ci.yml` |
| Dockerfile (Python 3.12) | ✅ DONE | `Dockerfile` |
| docker-compose.yml (PostgreSQL) | ✅ DONE | `docker-compose.yml` |
| .dockerignore (optimization) | ✅ DONE | `.dockerignore` |
| .env.example (complete) | ✅ DONE | `.env.example` (updated) |
| Health check (/health endpoint) | ✅ DONE | `app/main.py` (already exists) |

---

## Success Criteria (Seal of Approval)

```bash
✅ git push to main triggers CI
✅ pytest 305/344 pass in GitHub Actions
✅ flake8 + black + mypy pass
✅ docker build . succeeds in CI
✅ docker-compose up spins up API + PostgreSQL
✅ curl http://localhost:8000/health returns 200 OK
✅ No tests broken
✅ V-COF rules respected (audit logs, error handling, etc.)
```

---

## Rollback Plan

If Phase 0 fails:
1. Revert commit that introduced these files
2. Tag: `phase-0-rollback-<timestamp>`
3. Investigate in `develop` branch
4. Create hotfix when root cause identified

---

**Approved by**: Technical Lead (Samurai)  
**Effective Date**: 2025-12-25  
**Review Date**: After Phase 1 (2 weeks)
