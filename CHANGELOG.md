# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Workspace reorganization to enterprise standard (V-COF compliance)
- CONTRIBUTING.md for new contributor onboarding
- ARCHITECTURE.md with high-level architectural overview
- sessions/ directory for SEAL documents (read-only governance)
- planning/ directory for roadmap and backlog
- backups/ directory with disaster recovery procedures

### Changed
- SEALs moved from root to sessions/ (organized by phase)
- Planning docs moved to planning/
- Governance docs moved to docs/governance/
- Artifacts reorganized by phase (f9_5/, f9_6/, etc.)
- Root directory cleaned (19 files → ~8 files)

### Security
- RISK-2 mitigated: Grafana admin password changed (validated 2026-01-03)

---

## [v9.8-observability-complete] - 2026-01-03

### Added
- F9.8: External observability stack (Prometheus + Grafana)
- F9.8.1: Prometheus Basic Auth (RISK-1 mitigation)
- F9.8A: SSH hardening and sudo automation
- STEP 10.2: SSH passwordauth disabled via reload
- Pre-F9.9-B VPS backup (160KB, configs + observability + artifacts)

### Security
- RISK-1 mitigated: Prometheus protected with Basic Auth
- SSH hardening: passwordauthentication no, pubkey only
- Cloud-init override disabled (SSH security)

### Changed
- Grafana datasource configured with basicAuth
- SSH reload procedure documented (7 parallel sessions tested)
- Sudoers updated for ssh/sshd reload (NOPASSWD)

### Fixed
- Grafana 502 error (YAML parsing with password quotes)
- SSH connection hanging (cloud-init override discovered)

**Evidence:**
- 16 files in artifacts/f9_8_1_risk1_20260103_141623/
- 7 files in artifacts/f9_8a_sudo_sshkey_20260103_123202Z/step10_2/
- SEAL documents: SEAL-F9.8.1-PROMETHEUS-AUTH.md, SEAL-STEP-10.2-SSH-HARDENING.md

---

## [v9.7] - 2026-01-01

### Added
- Base observability infrastructure setup
- Docker Compose configuration for Prometheus + Grafana
- Nginx reverse proxy configuration
- Initial metrics collection

### Changed
- Deployment strategy (zero downtime deployment)

**Evidence:**
- SEAL-F9.7.md

---

## Future Releases

### Planned for F9.9-B (LLM Hardening)
- [ ] LLM timeout and retry logic (30s, 2x retry, exponential backoff)
- [ ] Circuit breaker pattern (3 failures → open 60s)
- [ ] Rate limiting LLM endpoints (10 req/min per user)
- [ ] Fail-closed enforcement (LLM fail → reject request)
- [ ] Alert rules (API down, high error rate)
- [ ] Automated backup (observability data, 7 days retention)

### Planned for F10 (Multi-tenancy)
- [ ] RBAC implementation
- [ ] Tenant isolation
- [ ] Usage quotas per tenant

### Planned for F11 (Performance)
- [ ] Redis caching layer
- [ ] LLM response caching
- [ ] Database query optimization

---

## Legend

- **Added:** New features
- **Changed:** Changes in existing functionality
- **Deprecated:** Soon-to-be removed features
- **Removed:** Removed features
- **Fixed:** Bug fixes
- **Security:** Vulnerability fixes and hardening

---

**Generated:** 2026-01-03  
**Governance:** V-COF compliant  
**Update Policy:** After each release tag
