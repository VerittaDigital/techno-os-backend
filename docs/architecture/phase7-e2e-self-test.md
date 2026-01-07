# Phase 7: E2E Staging Validation + Self-Test Surface

## Purpose
Provide deterministic, fail-closed validation of Notion read-only integration end-to-end: Console -> Gateway -> Backend -> Notion API (whitelist + Tier redaction). Reduce operator ambiguity in staging/production.

## Endpoint
- GET /v1/notion/self_test
- Requires: X-API-Key, X-Request-ID, X-Timestamp, X-Client-Version
- Response: JSON envelope {status: success|blocked|error|ratelimited, data: [checks], trace_id}

## Self-Test Logic
- Validate required env vars (NOTION_TOKEN, DB IDs) present (boolean only).
- If missing, blocked with reason_code=MISSING_ENV_VARS.
- Else, check each whitelisted surface read-only:
  - agents (ORDO36)
  - arcontes
  - audit
  - actions
  - evidence
  - pipelines
  - docs/readmes
  - governance summary (high-level counts only)
- Each check: {check_name, status: pass|blocked, safe_counts (numbers only), reason_code}
- If any blocked, overall status=blocked (fail-closed).
- Handle 429: blocked, reason_code=RATE_LIMITED.
- Handle timeout: blocked, reason_code=TIMEOUT.

## Security
- No PII/IDs/URLs in response.
- Sanitize trace_id: mask token/apikey/signature/password/pwd query params, user:pass@host.
- No raw payloads logged.

## Operator Runbook
1. Ensure Notion integration shared with workspace.
2. Set env vars in backend.
3. Run smoke script: bash scripts/smoke-phase7-self-test.sh
4. If blocked, check reason_codes for issues.

## How to Run Smoke
- Backend running on localhost:8000.
- Script calls /health and /v1/notion/self_test, prints high-level status + sanitized trace_id.

## SEAL
Phase 7 implemented and sealed.

**Backend Commit Hash:** 94ebda86cb4ba766bbf01944e27ab26edf8168d4

**Console Commit Hash:** 55af3cd

**Evidence:**
- /v1/notion/self_test endpoint added, fail-closed.
- Checks restricted to existing whitelist only (agents, arcontes, audit, actions, evidence, pipelines, docs, governance).
- No secrets in repo; git grep clean.
- Tests pass.
- Smoke script works.
- Doc created.
- Repo clean post-commit.
- Console uses gatewayClient only, no localStorage, anti-network passes, no logs/raw rendering.