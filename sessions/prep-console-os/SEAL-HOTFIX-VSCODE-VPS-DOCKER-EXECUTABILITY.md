# SEAL HOTFIX: VSCode VPS Docker Executability

## Status
Sealed: Improved debugging executability with runbook, scripts, and baseline inventory.

## Changes
- VSCode Remote-SSH runbook for stable remote development.
- VPS toolchain inventory (OS, tools, permissions).
- Docker/Compose debug scripts (safe, no secrets).
- Standardized compose path: /opt/techno-os/app/backend.

## Evidence
- artifacts/hotfix_exec_v1/ (baseline inventory).
- sessions/prep-console-os/HOTFIX-REMOTE-SSH-DOCKER-RUNBOOK.md
- scripts/vps_debug_bundle.sh
- scripts/vps_compose_restart_api.sh

## Note
This seal is only about tooling/executability. SEAL B remains pending.