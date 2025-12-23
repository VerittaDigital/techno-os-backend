# Executor Review Gate — Anti-Drift Checklist

Purpose
-------
Objective checklist used by reviewers to validate any new or modified executor implementation before acceptance. Each item is mandatory and must be answered unequivocally.

Review Items
------------
1. Identification
   - [ ] Is `executor_id` unique and documented? (lowercase, underscore-separated)
   - [ ] Is `version` present and valid semver (X.Y.Z)?

2. Determinism
   - [ ] Does `execute()` produce deterministic output for identical canonical inputs?
   - [ ] Are any random seeds or timestamps avoided inside `execute()`? If timestamps are required, are they returned only as metadata and not in the output digest computation?

3. Side-effects & I/O
   - [ ] Does `execute()` avoid filesystem, network, DB, subprocess, or other I/O?
   - [ ] Does `execute()` avoid global state mutation?

4. Privacy
   - [ ] Does the implementation avoid returning raw inputs/outputs? (Prefer `None` or serializable outputs that do not include sensitive fields.)
   - [ ] Are sensitive fields redacted or omitted by design?

5. Error semantics
   - [ ] Are expected error conditions documented? (e.g., validation errors)
   - [ ] Does the executor allow unexpected exceptions to bubble so the pipeline can map them to `FAILED`?

6. Limits & Safety
   - [ ] Are `limits` provided and reasonable (`timeout_ms`, `max_payload_bytes`, `max_depth`, `max_list_items`)?
   - [ ] Has the implementor verified the pipeline's payload limit enforcement will be respected?

7. Capabilities & Compatibility
   - [ ] Are `capabilities` declared and minimal (uppercase normalized)?
   - [ ] Is `min_executor_version` documented by the requesting action metadata if needed?

8. Testing Artefacts (for reviewer only — do not add new tests here)
   - [ ] Has the implementor provided a short manual test plan? (not committed as automated tests)
   - [ ] Is there a note describing how determinism was validated?

9. Documentation & Governance
   - [ ] Does the implementation reference `docs/contracts/EXECUTOR_CONTRACT.md`?
   - [ ] Has the change been recorded in governance changelog if required?

Reviewer Outcome
----------------
- Approve only if ALL mandatory items are `Yes`.
- If any item is `No`, return to implementor with required corrective actions.

Notes
-----
This checklist is intentionally strict to prevent drift and to keep the execution surface auditable and minimal. Use it as a gate for code review and for CI policy checks where feasible.
