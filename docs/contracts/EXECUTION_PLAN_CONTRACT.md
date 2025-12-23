Execution Plan Contract
=======================

Purpose
-------
Defines the canonical execution plan schema, canonicalization rules, and global limits
used by `composite_executor_v1` to validate plans before execution.

Canonical JSON
--------------
All canonicalization uses:

json.dumps(obj, sort_keys=True, separators=(',', ':'))

Plan Digest
----------
- `plan_digest` = sha256(canonical_json(plan))
- The digest is recorded in composite output and audit metadata only as a hex string.

Schema (summary)
-----------------
- `plan.steps`: list of steps (each step: `name`, `executor_id`, `min_executor_version`?, `input`, `merge`, `output_key`?)
- `input`: initial payload (dict)
- `limits`:
  - `max_steps`: int, default 8
  - `max_total_payload_bytes`: int, default 65536
  - `max_llm_calls`: int, optional
- `privacy.strip_keys`: list of sensitive keys to remove from step outputs before digest/merge

Validation rules
----------------
Pre-run validation (must pass before any step executes):
- Plan and input must be canonical JSON serializable.
- `len(steps) <= max_steps`.
- `declared_bytes = size(canonical_json(plan)) + size(canonical_json(input)) <= max_total_payload_bytes`.
- `declared_llm_calls` (counted by resolving each step's executor capabilities or id) <= `max_llm_calls` if set.
- For each step with `min_executor_version`, the registered executor version must satisfy the minimum.

Runtime guards
--------------
- After each step and merge, the composite recalculates the canonical size of the current payload and aborts
  with `PLAN_VALIDATION` if it exceeds `max_total_payload_bytes`.
- Any step runtime failure raises `RuntimeError("COMPOSITE_STEP_FAILED:<step_name>")` and maps to FAILED.

Privacy
-------
- Step outputs are sanitized by removing keys in `privacy.strip_keys` before digest and merge.
- No raw plan or input is emitted to audit logs; only `plan_digest` and metadata.

Errors
------
- Pre-run validation failures raise `ValueError("PLAN_VALIDATION")` (pipeline → FAILED).
- Step execution failures raise `RuntimeError("COMPOSITE_STEP_FAILED:<step_name>")`.

