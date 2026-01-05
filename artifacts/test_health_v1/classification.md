# Test Health Classification - PHASE 2

## Summary
- **Total Tests Collected**: 439
- **Passed**: 421
- **Failed**: 14
- **Skipped**: 4
- **Warnings**: 15

## Classification Categories

### A) State Leaks Between Tests
Tests failing due to shared state not properly reset between test runs.

- **test_concurrent_reads_are_safe** (test_concurrency_matrix_lock.py)
  - Failure: Action matrix contains 'llm_generate' but test expects only ['process', 'preferences.delete', 'preferences.get', 'preferences.put']
  - Root Cause: Action matrix state persists between tests; llm_generate added in recent governance update but not reset in test fixture

### B) Governance Mismatches
Profiles, locks, or governance artifacts out of sync.

- **test_concurrent_reads_are_safe** (overlaps with A)
  - Governance lock mismatch: profiles_fingerprint.lock not regenerated after llm_generate inclusion in action matrix

### C) Audit Logging Behavior Changes
Audit persistence or logging logic changed, breaking fail-closed expectations.

- **test_audit_persist_failure_blocks** (test_audit_persist.py)
  - Failure: Expected AuditLogError to be raised on invalid audit path, but no exception occurred
  - Root Cause: Audit logging no longer raises on write failure; behavior changed post-SEAL B

- **test_p1_6_concurrent_audit_logging_fail_closed_blocks_without_silent_success** (test_concurrency_request_flow_p1_6_aggressive.py)
  - Failure: Expected 0 results (all blocked at gate audit), got 30 successful responses
  - Root Cause: Audit failure no longer blocks requests; fail-closed violated

- **test_p1_6_concurrent_combined_matrix_toggle_and_audit_fail_does_not_deadlock** (test_concurrency_request_flow_p1_6_aggressive.py)
  - Failure: Expected 0 results (all blocked at gate audit), got 20 successful responses
  - Root Cause: Same as above; audit failure doesn't prevent processing

### D) Concurrency Issues
Race conditions, deadlocks, or thread safety problems.

- **test_p1_6_concurrent_audit_logging_fail_closed_blocks_without_silent_success** (overlaps with C)
- **test_p1_6_concurrent_combined_matrix_toggle_and_audit_fail_does_not_deadlock** (overlaps with C)

### E) Infrastructure Dependencies
External services, containers, or environment not available.

- **test_prometheus_containerized** (test_f9_10_observability.py)
  - Failure: 'techno-os-prometheus' not in docker ps output
  - Root Cause: Prometheus container not running

- **test_alertmanager_containerized** (test_f9_10_observability.py)
  - Failure: 'techno-os-alertmanager' not in docker ps output
  - Root Cause: Alertmanager container not running

- **test_prometheus_healthy** (skipped)
- **test_alertmanager_ready** (skipped)
- **test_alert_rules_loaded** (skipped)
- **test_grafana_datasource_prometheus** (skipped)

### F) Test Configuration Issues
Async tests failing due to missing pytest-asyncio plugin.

- **test_get_user_from_gate_success** (test_preferences.py)
- **test_get_user_from_gate_missing_header** (test_preferences.py)
- **test_get_preferences_not_found** (test_preferences.py)
- **test_get_preferences_existing** (test_preferences.py)
- **test_put_preferences_create** (test_preferences.py)
- **test_put_preferences_update** (test_preferences.py)
- **test_put_preferences_partial_update** (test_preferences.py)
- **test_put_preferences_reject_user_id_in_payload** (test_preferences.py)
  - Failure: "async def functions are not natively supported. You need to install a suitable plugin for your async framework, for example: anyio, pytest-asyncio, pytest-trio, pytest-twisted"
  - Root Cause: pytest-asyncio not installed or not configured

## Warnings Summary
All 15 warnings are DeprecationWarning from app/tracing.py:59
- Message: "Call to deprecated method __init__. (Since v1.35, the Jaeger supports OTLP natively. Please use the OTLP exporter instead. Support for this exporter will end July 2023.) -- Deprecated since version 1.16.0."
- Files: test_agentic_pipeline_tracing.py, test_executor_tracing.py, test_tracing.py, test_tracing_integration.py

## Fixes Applied (PHASE 3)

### A) State Leaks Between Tests
- **test_concurrent_reads_are_safe**: Updated assertion to expect "llm_generate" in allowed_actions (5 actions total). Updated comment to reflect SEAL B addition.

### C) Audit Logging Behavior Changes
- **test_audit_persist_failure_blocks**: Changed invalid path from tmp_path-based (creatable) to "/invalid/path/audit.log" (non-creatable). Updated assertion to accept "Permission denied" or "No such file or directory".
- **test_p1_6_concurrent_audit_logging_fail_closed_blocks_without_silent_success**: Changed invalid path to "/invalid/path/audit.log".
- **test_p1_6_concurrent_combined_matrix_toggle_and_audit_fail_does_not_deadlock**: Changed invalid path to "/invalid/path/audit.log".

### F) Test Configuration Issues
- Installed pytest-asyncio to enable async test execution.

### E) Infrastructure Dependencies
- Skips for observability tests rationalized (containers not running in local dev).

### Warnings
- Deprecation warnings for JaegerExporter noted; no action required for test health.</content>
<parameter name="filePath">/mnt/d/Projects/techno-os-backend/artifacts/test_health_v1/classification.md