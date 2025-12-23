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
