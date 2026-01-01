# Evidence Policy

## Canonical Light Evidence
- Files committed to git: policies, scripts, configs that define the system.
- Examples: docker-compose.yml, scripts/, docs/, .gitignore updates.

## Heavy Artifacts
- Runtime evidences: logs, probes, checksums, reports generated during execution.
- Ignored in .gitignore under artifacts/

## Rationale
- Keep repo lean for CI/CD.
- Heavy artifacts can be regenerated or stored externally if needed.
