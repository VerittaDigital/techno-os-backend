LLM Executor Hardening Notes
=================================

Scope
-----
This document records the minimal hardening performed for `llm_executor_v1` to prepare
for Beta (1→36 users). It is intentionally short and technical.

What the executor does
----------------------
- Validates a strict payload schema: `prompt`, `model`, `max_tokens`.
- Applies a governance `Policy` (model allowlist, size caps, timeout).
- Calls an injected `LLMClient` and returns a minimal output object containing `text`, `model`, and `usage`.
- Side-effect free: executor does not store prompts or outputs; pipeline persists only digests.

What it explicitly does NOT do
------------------------------
- No retries, no automatic backoff.
- No fallback between models.
- No streaming, no function-calling or tool execution.
- Does not call OpenAI directly from the executor (client is injected).

Privacy guarantees
------------------
- Prompts are never written to audit logs or persisted artifacts; only canonical digests are recorded.
- Audit trail contains `input_digest` and `output_digest` but not raw payloads or outputs.

Fail-closed guarantees
----------------------
- Any provider/client error surfaces as an exception which the pipeline maps to `FAILED`.
- Audit logging is performed in a fail-closed manner (pipeline converts failures to BLOCKED when necessary).

Limitations
-----------
- No retries or multi-model strategies are implemented (A5 scope).
- Latency and usage metrics are produced by the client and surfaced in executor outputs, not in audit fields.

Notes for reviewers
-------------------
- Tests validate privacy, determinism, concurrency stability, and basic observability without adding fields.
- All LLM client code is isolated under `app/llm/` and can be replaced by an approved provider integration.
