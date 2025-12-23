Composite Executor Contract
===========================

Scope
-----
`composite_executor_v1` executes a declarative sequential plan of existing executors
without changing the global pipeline. It validates inputs strictly, sanitizes outputs
for privacy, and fails closed on any violation.

Payload schema
--------------
- `plan.steps`: list of steps (1..max_steps)
  - each step: `name`, `executor_id`, `min_executor_version` (optional), `input` (dict),
    `merge` (replace|merge_under|append_results), `output_key` (required for merge_under/append_results)
- `input`: initial payload (dict)
- `limits`: optional with `max_steps` (default 8), `max_payload_bytes` (default 32768)
- `privacy.strip_keys`: optional list of keys to remove from step outputs before digest/merge

Merge semantics
---------------
- `replace`: current_payload = sanitized_step_output
- `merge_under`: current_payload[output_key] = sanitized_step_output
- `append_results`: current_payload[output_key] is a list; append sanitized_step_output

Sanitization
------------
Step outputs are sanitized by recursively removing keys in `privacy.strip_keys` (default
`["prompt","raw_prompt","messages","input","context","payload"]`) before computing
digests or merging.

Validation and failures
-----------------------
- Any validation error MUST raise `ValueError("COMPOSITE_VALIDATION")`.
- Any step runtime error or invalid step output MUST raise `RuntimeError("COMPOSITE_STEP_FAILED:<step_name>")`.
- Composite must enforce `min_executor_version` by comparing registered executor versions.

Output
------
Immutable, privacy-safe output structure with:
- `composite`: executor_id, version, steps_executed
- `steps`: list with name, executor_id, status, output_digest, output_bytes
- `result`: final merged payload (sanitized)
- `result_digest`, `result_bytes`

Audit
-----
No raw payloads or prompts are included in audit logs. Only digests and metadata are emitted.

Limits
------
Defaults: `max_steps=8`, `max_payload_bytes=32768`.

Compatibility
-------------
Backwards-compatible with existing executors. Composite relies on deterministic
behaviour of underlying executors.
