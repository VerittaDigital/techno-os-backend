# Executor Contract — Techno OS (P3+ Seal)

Purpose
--------
This short, normative document freezes the canonical executor contract used by the governed execution pipeline. It is intentionally compact and prescriptive — implementors must follow it exactly.

Interface
---------
- Executor must expose these attributes (immutable at runtime):
  - `executor_id`: string — unique identifier (lowercase, underscore-separated).
  - `version`: string — semantic version (MAJOR.MINOR.PATCH) using `X.Y.Z` format.
  - `capabilities`: list[str] — declared capabilities (may be empty). Values MUST be normalized to uppercase.
  - `limits`: object with numeric fields:
    - `timeout_ms`: maximum simulated timeout (integer)
    - `max_payload_bytes`: maximum canonical payload size in bytes
    - `max_depth`: maximum nesting depth
    - `max_list_items`: maximum list length
- Executor must implement: `execute(req: ActionRequest) -> Any`
  - `ActionRequest` is the canonical request object used by the pipeline.
  - Return value may be JSON-serializable output, or `None` when no output is produced.

Invariants (must hold for every executor)
-----------------------------------------
1. Determinism: for identical canonical inputs an executor must produce identical outputs (or identical absence of output).
2. Side-effect free: executors MUST NOT perform I/O — no filesystem, network, database, or external process calls.
3. No environment reads: executors MUST NOT read environment variables or other ambient configuration during `execute()`; all configuration must be passed in the `ActionRequest` payload or derived from declared `capabilities`/`version`.
4. Fail/Exception semantics: executors MAY raise exceptions. The pipeline maps exceptions to `FAILED` results and to the reason code `EXECUTOR_EXCEPTION`. Executors must not catch and swallow unexpected exceptions to change this contract.
5. Versioning: `version` MUST be valid semantic version string. Backwards-compatibility decisions must be implemented via version checks outside the executor.
6. Privacy: Raw inputs and raw outputs MUST NOT be returned or persisted by the executor; only digests are allowed to be emitted by the pipeline/audit.

Prohibitions (explicit)
-----------------------
- NO filesystem reads/writes (including temp files).
- NO network calls (HTTP, sockets, RPC).
- NO direct DB access.
- NO writing to global process state or modifying shared in-memory structures.
- NO secret leakage (do not include secrets in returned outputs).

Error semantics (explicit mapping)
---------------------------------
- If `execute()` raises any exception, the pipeline will record an `ActionResult` with `status = "FAILED"` and include `reason_codes` containing `EXECUTOR_EXCEPTION`.
- If the executor exceeds declared limits (pipeline enforces), the pipeline will mark the outcome `BLOCKED` with `reason_codes` such as `EXECUTOR_TIMEOUT` or `LIMIT_EXCEEDED`.
- Executors MUST NOT attempt to override or alter pipeline error envelopes; pipeline maps executor behavior to canonical `ActionResult` objects.

Audit rules
-----------
- Executors MUST NOT produce audit logs themselves. All audit emission is the pipeline's responsibility.
- Audit records MUST include: `event_type = "action_audit"`, `executor_id`, `executor_version`, `status`, `trace_id`, `duration_ms`, `input_digest`, and `output_digest` (or `null`).
- Executors MUST ensure their outputs are JSON-serializable if they are expected to produce an `output_digest`; otherwise return `None` and the pipeline will record `output_digest = null`.

Compatibility & Evolution
-------------------------
- New optional fields MAY be added to executor classes provided they are strictly additive and do not change existing attribute names or types.
- Any change to `executor_id` or to `ActionRequest`/`ActionResult` shapes requires governance approval and a version bump at protocol-level (outside this file).

Minimal implementor checklist (quick)
-------------------------------------
- `executor_id` present and unique
- `version` is semver
- `capabilities` declared
- `limits` present with required numeric fields
- `execute()` deterministic and side-effect free
- returns `None` when no output

Seal
----
This document is normative for P3+ and must be referenced by the Executor Review Gate before accepting any new executor into the codebase.
