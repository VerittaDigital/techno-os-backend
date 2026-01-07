# Phase 4 — Notion Read-only Console Surface (fail-closed)

**Implementation: Backend read-only gateway for Notion integration.**

## Scope and Non-Goals
- **Scope**: Backend endpoints /v1/notion/* returning sanitized data from whitelisted Notion sources. Enforce Tier 1–4 redaction server-side. Fail-closed on any uncertainty.
- **Non-Goals**: No UI changes (console repo). No write operations. No arbitrary Notion queries. No data storage beyond caching.

## Whitelist (names/paths only, no IDs)
- DB: "🏛️ Arcontes — Governança Superior do V-COF"
- DB: "🧭 ORDO 36 — Núcleos e Agentes da ORDO VERITTÀ"
- DBs: "Audit — Techno OS", "Actions — Techno OS", "Evidence · Artifacts Ledger — Techno OS", "Pipelines — Techno OS"
- Pages: "📄 Documentação Técnica" + child READMEs (Audit/Evidence/Pipelines/Actions)
- Page: "Techno OS — BETA Ops (1 user)"
- Governance pages: "Ciclo Superior — LOGOS → BEGIN → AION → FORGE → SEAL → NOESIS", "LOGOS Teleológico — Propósito e Ordem Superior", "PRINCÍPIOS LOGOS — Notas", "NOESIS — Painel Analítico-Executivo", "Painel SYNCHRONOS — Coerência Global", "NÚCLEO INTERNO DO SISTEMA — V-COF OPERACIONAL"
- Embedded DBs in governance pages (structure + Tier-1 fields; Tier-2 previews; deep-link for details).

## Data Classification & Redaction (Server-Side Binding)
- **Tier 1 (Always-safe)**: Structural fields (titles, select/status, numbers, dates not linked to persons). Render freely.
- **Tier 2 (Free-text w/ PII risk)**: Preview-only (120 chars max after redaction) + deep-link. Redact emails, phones, tokens, auth headers, high-entropy sequences.
- **Tier 3 (Attachments)**: Metadata only (filename, type, size, last_modified, notion_url). No binary fetch.
- **Tier 4 (Relations)**: Structure (counts, titles) only. No dereference.

## LGPD / Privacy Posture
- All data sanitized before return. No direct identifiers stored/cached. Owners: Legal/LGPD + Technical Approver.

## K-SEC Rules
- NOTION_TOKEN runtime-only (env). Never logged. Endpoints require X-API-Key for auth (but Notion uses Bearer).
- No secrets in responses. Redaction applied before truncation.

## Endpoints
- GET /v1/notion/agents: ORDO36 list (Tier 1–4)
- GET /v1/notion/arcontes: Arcontes list
- GET /v1/notion/audit: Audit list
- GET /v1/notion/actions, /evidence, /pipelines: Minimal lists
- GET /v1/notion/docs: Page list + child titles
- GET /v1/notion/governance: Governance pages list

## Headers & Correlation
- Require X-Request-ID and X-Client-Version (fail-closed if missing).
- Propagate X-Request-ID in responses.

## Timeouts & Rate Limits
- Request timeout: 10s.
- 429: Honor Retry-After; no auto-retry.
- Cache: In-memory TTL 60s for list endpoints.

## Fail-Closed Behaviors
- Missing env var: BLOCKED (403) "MISSING_CONFIG"
- Parse error/unknown status: BLOCKED
- Timeout/network: BLOCKED
- Unsupported scope: BLOCKED

## Implementation Files
- app/integrations/notion_client.py: Client with httpx, caching, redaction.
- app/routes/notion.py: FastAPI endpoints.
- app/main.py: Router inclusion.
- tests/test_notion.py: Unit tests for redaction, contract tests.
- scripts/smoke-notion.sh: Smoke test script.

## SEAL Criteria (Phase 4 backend)
- Files exist at canonical paths
- Owners recorded
- Whitelist codified (names only)
- Tier 1–4 enforced server-side
- K-SEC: no secrets; redaction unit tests pass
- Tests green
- Repo clean after commit
- Commit hash recorded