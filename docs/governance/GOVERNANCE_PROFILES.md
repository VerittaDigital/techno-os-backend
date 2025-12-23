# Profiles Governance (Gate)

This repository treats DEFAULT_PROFILES as a policy surface.

## Change Rule (Fail-Closed)
Any change to `app/gate_profiles.py::DEFAULT_PROFILES` MUST include:
1) Update `app/profiles_fingerprint.lock` with the new SHA256.
2) Add an entry below describing:
   - what changed
   - why it changed
   - reviewer/owner approval

## Change Log
- 2025-12-21: Initial lock created from current DEFAULT_PROFILES. (owner: Verittà)
- 2025-12-21: Added ACTION_PROCESS="process" profile for HTTP /process endpoint gating. Allows {"text"} field, fail-closed, no external fields. (owner: Samurai Gate Hardening v0.1)
- 2025-12-23: P3+ SEAL — Executor contract frozen and sealed (A3→P3+).
   - What: Added `docs/contracts/EXECUTOR_CONTRACT.md`, `docs/contracts/EXECUTOR_CHECKLIST.md`, and executor scaffold `app/executors/_executor_template.py`.
   - Why: Formalize executor interface, prevent drift before A4, and provide a normative template for implementors.
   - Owner / Reviewer: Verittà / Samurai team
   - Commit: c98c3ed seal(p3+): executor contract, checklist and template (A3→P3+)
   - Notes: This change is strictly contractual; no runtime, gate, or auth behavior modified. Reviewers must follow `docs/contracts/EXECUTOR_CHECKLIST.md` before accepting any new executor.
