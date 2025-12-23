# Sprint A — Remaining Test Issues (No Fixes Applied)

## Global Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 302 |
| **Passed** | 277 ✅ |
| **Failed** | 10 ❌ |
| **Errors** | 0 |
| **Skipped** | 3 ⏭️ |
| **Status** | 91.7% pass rate |

---

## FAILURES (Assertion / Expected Behavior)

| # | Test Node ID | File | Short Reason | Category |
|---|---|---|---|---|
| 1 | `test_ag03_retrocompat_red.py::TestRetrocompatibilityRed::test_action_process_without_version_continues` | `tests/test_ag03_retrocompat_red.py` | `expected HTTP 200/422 got 401` — missing X-API-Key header | **RETROCOMPAT** |
| 2 | `test_beta_auth_audit.py::TestBetaAuthAudit::test_missing_key_audit_logged` | `tests/test_beta_auth_audit.py` | `expected reason_code AUTH_MISSING_KEY got AUTH_MISSING_AUTHORIZATION` | **AUDIT** |
| 3 | `test_beta_auth_audit.py::TestBetaAuthAudit::test_invalid_key_audit_logged` | `tests/test_beta_auth_audit.py` | `expected reason_code AUTH_INVALID_KEY got G2_invalid_api_key` | **AUDIT** |
| 4 | `test_concurrency_request_flow_p1_6_aggressive.py::TestP16ConcurrentE2EProcessFlow::test_p1_6_concurrent_process_trace_ids_unique_and_no_audit_failure` | `tests/test_concurrency_request_flow_p1_6_aggressive.py` | `KeyError: 'status'` — response JSON missing "status" field on concurrent 401 responses | **CONCURRENCY** |
| 5 | `test_concurrency_request_flow_p1_6_aggressive.py::TestP16ConcurrentE2EProcessFlow::test_p1_6_concurrent_identical_payload_digest_stable` | `tests/test_concurrency_request_flow_p1_6_aggressive.py` | `Found 30 None digests` — all input_digest values are None (missing X-API-Key) | **CONCURRENCY** |
| 6 | `test_concurrency_request_flow_p1_6_aggressive.py::TestP16ConcurrentE2EProcessFlow::test_p1_6_concurrent_requests_with_action_matrix_toggle_are_safe` | `tests/test_concurrency_request_flow_p1_6_aggressive.py` | `KeyError: 'status'` — response JSON missing "status" field on concurrent 401 responses | **CONCURRENCY** |
| 7 | `test_gate_http_enforcement.py::TestGateEnforcementHTTP::test_process_denies_on_gate_denial` | `tests/test_gate_http_enforcement.py` | `expected HTTP 403 got 200` — patch("app.gate_engine.evaluate_gate") not applied (mock returns ALLOW despite patch) | **MOCK** |
| 8 | `test_gate_http_enforcement.py::TestGateEnforcementHTTP::test_process_handles_gate_exception` | `tests/test_gate_http_enforcement.py` | `expected HTTP 403 got 200` — patch("app.gate_engine.evaluate_gate") side_effect not applied | **MOCK** |
| 9 | `test_gate_pipeline_integration.py::TestGateDenyPreventsExecution::test_gate_deny_no_action_audit` | `tests/test_gate_pipeline_integration.py` | `expected HTTP 403 got 200` — patch("app.gate_engine.evaluate_gate") not applied (mock returns ALLOW despite patch) | **MOCK** |
| 10 | `test_gate_pipeline_integration.py::TestSingleReadInvariant::test_successful_request_uses_cached_payload` | `tests/test_gate_pipeline_integration.py` | `gate input_digest == '' but action_audit input_digest == 'ed887b78fc89...'` — input digest mismatch | **AUDIT** |

---

## ERRORS

**None detected.** All failures are assertion-based (not infrastructure exceptions).

---

## SKIPS

| # | Test Node ID | File | Skip Reason |
|---|---|---|---|
| 1 | `test_api.py::test_health` | `tests/test_api.py` | `Legacy MVP contract; replaced by gate/pipeline tests` |
| 2 | `test_api.py::test_process_success` | `tests/test_api.py` | `Legacy MVP contract; replaced by gate/pipeline tests` |
| 3 | `test_api.py::test_process_empty_rejected` | `tests/test_api.py` | `Legacy MVP contract; replaced by gate/pipeline tests` |

---

## Detailed Failure Analysis

### Category: RETROCOMPAT (1 test)

**Failure #1: test_action_process_without_version_continues**

```
AssertionError: Legacy 'process' action broken: HTTP 401
Expected: [200, 422]
Actual: 401

Gate Audit Log:
{
  "decision": "DENY",
  "profile_id": "G0",
  "matched_rules": ["Authorization header required"],
  "reason_codes": ["AUTH_MISSING_AUTHORIZATION"],
  "trace_id": "214d375c-3513-4025-9056-6158ee45fb0d"
}
```

**Root Cause:** Test sends request WITHOUT X-API-Key header. Gate rejects at G0 (AUTH_MISSING_AUTHORIZATION).

**Status:** Test expects legacy behavior (no auth required), but current gate requires auth.

---

### Category: AUDIT (3 tests: #2, #3, #10)

**Failure #2: test_missing_key_audit_logged**

```
AssertionError: Expected AUTH_MISSING_KEY in reason_codes, got ['AUTH_MISSING_AUTHORIZATION']

Test expectation: reason_codes = ["AUTH_MISSING_KEY"]
Actual reason_codes: ["AUTH_MISSING_AUTHORIZATION"]
```

**Root Cause:** Test expects reason code `AUTH_MISSING_KEY`, but gate emits `AUTH_MISSING_AUTHORIZATION`.

---

**Failure #3: test_invalid_key_audit_logged**

```
AssertionError: Expected AUTH_INVALID_KEY in reason_codes, got ['G2_invalid_api_key']

Test expectation: reason_codes = ["AUTH_INVALID_KEY"]
Actual reason_codes: ["G2_invalid_api_key"]
```

**Root Cause:** Test expects reason code `AUTH_INVALID_KEY`, but gate emits `G2_invalid_api_key` (profile-based naming).

---

**Failure #10: test_successful_request_uses_cached_payload**

```
AssertionError: assert gate_json["input_digest"] == action_json["input_digest"]
gate input_digest: ""
action_audit input_digest: "ed887b78fc8986cfa1802082122f674cccb09a6c8e155b68a32a97775709d27a"

Both have same trace_id (5fc6fe80-e910-461d-95ec-10210b1a1d90) → correlation proven
But input_digest diverges:
  - gate_audit: "" (empty string)
  - action_audit: "ed887b78..." (SHA256 hash)
```

**Root Cause:** Gate is NOT computing input_digest (empty string in log). Action pipeline computes it correctly. Mismatch suggests gate is skipping digest computation.

---

### Category: CONCURRENCY (3 tests: #4, #5, #6)

**Failures #4 & #6: KeyError: 'status'**

```
All 30 concurrent responses return HTTP 401 (missing auth).
Response body: {"error": "unauthorized", "message": "missing_authorization", "trace_id": "...", "reason_codes": [...]}

Test expects: response["body"]["status"] field
Actual response: No "status" field in 401 error response

KeyError when accessing: r["body"]["status"]
```

**Root Cause:** Tests send concurrent POST without X-API-Key header → all get 401 Unauthorized → error response format doesn't include "status" field.

---

**Failure #5: Found 30 None digests**

```
All 30 concurrent requests return HTTP 401.
Response body doesn't include "input_digest" field (only error envelope).

Test expects: body.get("input_digest") to be non-None SHA256 hash
Actual: None (field not present in 401 response)
```

**Root Cause:** Same as #4 & #6 — missing auth header → 401 → no "input_digest" field in error response.

---

### Category: MOCK (3 tests: #7, #8, #9)

**Failures #7, #8, #9: Patch not applied**

```
Test Code:
  with patch("app.gate_engine.evaluate_gate") as mock_gate:
    mock_result = GateResult(decision=GateDecision.DENY, ...)
    mock_gate.return_value = mock_result
    response = client.post("/process", ..., headers={"X-API-Key": "..."})
    assert response.status_code == 403  # FAILS: got 200

Gate Audit Log:
{
  "decision": "ALLOW",  # NOT DENY as patched
  "profile_id": "F2.1",
  "reason_codes": []
}
```

**Root Cause:** Patch target `app.gate_engine.evaluate_gate` is NOT being used by the endpoint. The endpoint calls gate logic through a different code path that doesn't use the patched function. Patch applied to wrong location or gate evaluation happens at import time before patch is applied.

**Evidence:** Despite patch explicitly setting mock to return DENY, gate_audit logs ALLOW consistently. Mock is never called.

---

## Category Summary

| Category | Count | Impact | Priority |
|----------|-------|--------|----------|
| **RETROCOMPAT** | 1 | Legacy test expects no-auth flow (broken by current design) | Medium |
| **AUDIT** | 3 | Reason code names mismatch + input_digest computation gap | High |
| **CONCURRENCY** | 3 | All fail due to missing auth headers (401 responses) | High |
| **MOCK** | 3 | Patch isolation issue — mocks not applied to endpoint calls | Critical |

---

## A1/A2 Regression Check

✅ **A1 Status (test_session_lifecycle.py):** 13/13 PASSED

✅ **A2 Status (test_admin_api.py):** 14/14 PASSED

✅ **Conclusion:** NO regressions. A1/A2 remain SEALED.

---

## Dependency Map

```
RETROCOMPAT (#1)
  ↓ depends on
AUDIT (#2, #3, #10)
  ↓ reason codes must be fixed first
  
CONCURRENCY (#4, #5, #6)
  ↓ all require auth headers to pass
  
MOCK (#7, #8, #9)
  ↓ requires patch isolation (factory pattern or patch location fix)
```

---

## Next Move Recommendation

**Order of Attack:**

1. **MOCK isolation (#7–#9)** — CRITICAL
   - Diagnose why `patch("app.gate_engine.evaluate_gate")` doesn't affect endpoint calls
   - Either fix patch target or implement factory pattern for test isolation
   
2. **AUDIT reason codes (#2–#3)** — HIGH
   - Align test expectations with actual gate reason code names
   - OR align gate reason codes with test expectations (backwards compat)

3. **AUDIT input_digest (#10)** — HIGH
   - Verify gate_request computes input_digest
   - Fix: `input_digest = sha256_json_or_none(body)` in gate_request

4. **CONCURRENCY (#4–#6)** — HIGH
   - Add X-API-Key header to all concurrent requests
   - OR: Mock auth for concurrent tests

5. **RETROCOMPAT (#1)** — MEDIUM
   - Decide: Legacy endpoints (no auth) or deprecate?
   - If keep: Add auth bypass for "process" action
   - If deprecate: Mark test as obsolete

---

## Evidence Availability

All failures have:
- ✅ Full test node IDs
- ✅ Assertion messages (exact error text)
- ✅ Audit logs (gate_audit and action_audit JSON)
- ✅ HTTP status codes
- ✅ Response body samples

Ready for PR assignment and investigation.

---

**Generated:** 2025-12-23  
**Command Executed:** `python -m pytest tests/ -q`  
**Suite Status:** 10 failures (ISOLATED, HIGH SIGNAL), 277 passed, 3 skipped  
**A1/A2 Regression Check:** ✅ SEALED (27/27 passed)  
**Ready for Team Review:** YES  

---

## How to Use This Report

1. **For PR Assignment:** Copy test node IDs from FAILURES table
2. **For Investigation:** Read Detailed Failure Analysis section
3. **For Prioritization:** Follow "Next Move Recommendation" order
4. **For Verification:** All tests have audit logs and evidence

---

## File Location

This inventory was created at: `c:\projetos\techno-os-backend\SPRINT-A-REMAINING-ISSUES.md`
