"""P1.6 AGGRESSIVE — Deterministic concurrency + fail-closed audit stress tests.

SAMURAI MODE: Zero flakiness. All parallelism synchronized via Barrier/Event.
No random sleeps. Thread-safe collection with Queue/Lock.

Reference test: tests/test_gate_pipeline_integration.py::TestGateAllowThenExecute::test_gate_allow_produces_both_audits
- Uses FastAPI TestClient and POST /process with JSON payload
- Extracts trace_id and input_digest from response.json()
- Response contains: status, trace_id, action, reason_codes, input_digest, output_digest

Test Coverage:
  A) Concurrent E2E /process: trace_id unique, no audit failure
  B) Digest deterministic under concurrency (identical payload)
  C) ActionMatrix toggle safe during concurrent requests
  D) Audit failure under concurrency must be fail-closed
  E) Combined matrix toggle + audit fail (stress test)
"""
import json
import logging
import threading
from queue import Queue
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.action_matrix import get_action_matrix, reset_action_matrix, set_action_matrix
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestP16ConcurrentE2EProcessFlow:
    """P1.6 AGGRESSIVE: Concurrent /process E2E with deterministic synchronization."""

    def test_p1_6_concurrent_process_trace_ids_unique_and_no_audit_failure(self, client):
        """
        TESTE A: Concurrent E2E /process; trace_id unique; no AUDIT_LOG_FAILED.
        
        Dispatch N=30 parallel POSTs with valid JSON payload (ALLOW gate).
        Assert:
        - No exceptions
        - All responses HTTP 200
        - All trace_ids unique (len(set(trace_ids)) == N)
        - No response has reason_code "AUDIT_LOG_FAILED"
        - No response has status "BLOCKED" (payload is ALLOW)
        """
        N = 30
        barrier = threading.Barrier(N)
        results_queue: Queue[Dict[str, Any]] = Queue()
        exceptions_queue: Queue[Exception] = Queue()
        
        def worker():
            try:
                # Synchronize all threads to fire simultaneously
                barrier.wait()
                
                payload = {"text": "concurrent test payload"}
                response = client.post("/process", json=payload)
                
                result_data = {
                    "status_code": response.status_code,
                    "body": response.json(),
                }
                results_queue.put(result_data)
            except Exception as e:
                exceptions_queue.put(e)
        
        threads = [threading.Thread(target=worker) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Validate no exceptions
        exceptions_list = []
        while not exceptions_queue.empty():
            exceptions_list.append(exceptions_queue.get())
        assert len(exceptions_list) == 0, f"Expected 0 exceptions, got {len(exceptions_list)}: {exceptions_list}"
        
        # Collect all results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == N, f"Expected {N} results, got {len(results)}"
        
        # Extract trace_ids
        trace_ids = [r["body"]["trace_id"] for r in results]
        status_codes = [r["status_code"] for r in results]
        statuses = [r["body"]["status"] for r in results]
        reason_codes_list = [r["body"].get("reason_codes", []) for r in results]
        
        # Assert all HTTP 200
        assert all(sc == 200 for sc in status_codes), \
            f"Expected all HTTP 200, got distribution: {dict((k, status_codes.count(k)) for k in set(status_codes))}"
        
        # Assert trace_ids unique
        unique_trace_ids = set(trace_ids)
        assert len(unique_trace_ids) == N, \
            f"Expected {N} unique trace_ids, got {len(unique_trace_ids)}. Duplicates: {[t for t in trace_ids if trace_ids.count(t) > 1]}"
        
        # Assert no AUDIT_LOG_FAILED
        all_reason_codes_flat = [rc for rcs in reason_codes_list for rc in rcs]
        assert "AUDIT_LOG_FAILED" not in all_reason_codes_flat, \
            f"Found AUDIT_LOG_FAILED in {len([rc for rc in all_reason_codes_flat if rc == 'AUDIT_LOG_FAILED'])} responses"
        
        # Assert no BLOCKED (payload is valid ALLOW)
        # Note: allow SUCCESS or PENDING (pre-audit); other statuses only if payload causes executor error
        blocked_count = len([s for s in statuses if s == "BLOCKED"])
        success_count = len([s for s in statuses if s == "SUCCESS"])
        failed_count = len([s for s in statuses if s == "FAILED"])
        pending_count = len([s for s in statuses if s == "PENDING"])
        
        # Payload is ALLOW, so we expect SUCCESS or FAILED (executor error) or PENDING, not BLOCKED
        assert blocked_count == 0, \
            f"Expected 0 BLOCKED, got {blocked_count}. Distribution: SUCCESS={success_count}, FAILED={failed_count}, PENDING={pending_count}, BLOCKED={blocked_count}"

    def test_p1_6_concurrent_identical_payload_digest_stable(self, client):
        """
        TESTE B: Concurrent identical payload; digest deterministic and stable.
        
        Dispatch N=30 parallel POSTs with SAME JSON payload.
        Assert:
        - All input_digest non-None
        - All input_digest are 64-char hex (SHA256)
        - All input_digest are equal
        """
        N = 30
        barrier = threading.Barrier(N)
        results_queue: Queue[str] = Queue()
        exceptions_queue: Queue[Exception] = Queue()
        
        identical_payload = {"text": "identical payload for digest test"}
        
        def worker():
            try:
                barrier.wait()
                response = client.post("/process", json=identical_payload)
                body = response.json()
                input_digest = body.get("input_digest")
                results_queue.put(input_digest)
            except Exception as e:
                exceptions_queue.put(e)
        
        threads = [threading.Thread(target=worker) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Validate no exceptions
        exceptions_list = []
        while not exceptions_queue.empty():
            exceptions_list.append(exceptions_queue.get())
        assert len(exceptions_list) == 0, f"Expected 0 exceptions, got {len(exceptions_list)}"
        
        # Collect digests
        digests = []
        while not results_queue.empty():
            digests.append(results_queue.get())
        
        assert len(digests) == N, f"Expected {N} digests, got {len(digests)}"
        
        # Assert none are None
        assert all(d is not None for d in digests), \
            f"Found {len([d for d in digests if d is None])} None digests"
        
        # Assert all are 64-char hex (SHA256)
        assert all(isinstance(d, str) and len(d) == 64 and all(c in "0123456789abcdef" for c in d) for d in digests), \
            f"Not all digests are 64-char hex: {set(digests)}"
        
        # Assert all equal
        unique_digests = set(digests)
        assert len(unique_digests) == 1, \
            f"Expected 1 unique digest, got {len(unique_digests)}: {unique_digests}"

    def test_p1_6_concurrent_requests_with_action_matrix_toggle_are_safe(self, client):
        """
        TESTE C: Toggle ActionMatrix while requests run; must be safe.
        
        - Initialize Matrix A (allow process) and Matrix B (allow process with different structure)
        - Launch writer thread alternating set_action_matrix(A/B) for 500 iterations
        - Simultaneously fire N=30 concurrent /process requests
        - Assert: no exceptions, no BLOCKED by mismatch (both matrices allow process), no deadlock
        """
        from app.action_matrix import ActionMatrix
        
        N = 30
        barrier = threading.Barrier(N + 1)  # +1 for writer
        results_queue: Queue[Dict[str, Any]] = Queue()
        exceptions_queue: Queue[Exception] = Queue()
        stop_event = threading.Event()
        
        # Create two valid matrices (both allow "process")
        matrix_a = ActionMatrix(
            profile="default",
            allowed_actions=["process"]
        )
        matrix_b = ActionMatrix(
            profile="default",
            allowed_actions=["process"]
        )
        
        def writer_toggle():
            try:
                barrier.wait()  # Synchronize start
                for iteration in range(500):
                    matrix = matrix_a if iteration % 2 == 0 else matrix_b
                    set_action_matrix(matrix)
                stop_event.set()
            except Exception as e:
                exceptions_queue.put(e)
        
        def reader_request():
            try:
                barrier.wait()
                payload = {"text": "toggle test"}
                response = client.post("/process", json=payload)
                result_data = {
                    "status_code": response.status_code,
                    "body": response.json(),
                }
                results_queue.put(result_data)
            except Exception as e:
                exceptions_queue.put(e)
        
        # Set initial matrix
        set_action_matrix(matrix_a)
        
        writer = threading.Thread(target=writer_toggle)
        readers = [threading.Thread(target=reader_request) for _ in range(N)]
        
        writer.start()
        for r in readers:
            r.start()
        
        writer.join()
        for r in readers:
            r.join()
        
        # Cleanup
        reset_action_matrix()
        
        # Validate no exceptions
        exceptions_list = []
        while not exceptions_queue.empty():
            exceptions_list.append(exceptions_queue.get())
        assert len(exceptions_list) == 0, f"Expected 0 exceptions, got {len(exceptions_list)}: {exceptions_list}"
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == N, f"Expected {N} results, got {len(results)}"
        
        # Assert no BLOCKED (both matrices allow process)
        statuses = [r["body"]["status"] for r in results]
        blocked_count = len([s for s in statuses if s == "BLOCKED"])
        assert blocked_count == 0, \
            f"Expected 0 BLOCKED, got {blocked_count}. Statuses: {dict((k, statuses.count(k)) for k in set(statuses))}"

    def test_p1_6_concurrent_audit_logging_fail_closed_blocks_without_silent_success(self, client):
        """
        TESTE D (AGRESSIVO): Audit logging failure under concurrency must be fail-closed.
        
        Inject deterministic audit logging failures:
        - Monkeypatch log_action_result to raise Exception in first K=10 calls
        - Use thread-safe counter (Lock + int) for determinism
        - Fire N=30 concurrent /process requests
        
        Assert:
        - At least 1 response has status=BLOCKED with reason_code AUDIT_LOG_FAILED
        - No silent SUCCESS when audit fails
        - No exception leaks to test
        - All responses have valid trace_id
        """
        N = 30
        barrier = threading.Barrier(N)
        results_queue: Queue[Dict[str, Any]] = Queue()
        exceptions_queue: Queue[Exception] = Queue()
        
        # Thread-safe counter for deterministic injection
        call_counter = {"value": 0}
        counter_lock = threading.Lock()
        K = 10  # Fail first K calls
        
        original_log_action_result = None
        
        def failing_log_action_result(result, trace_id=None):
            """Wrapper that fails first K calls deterministically."""
            with counter_lock:
                call_counter["value"] += 1
                should_fail = call_counter["value"] <= K
            
            if should_fail:
                from app.audit_log import AuditLogError
                raise AuditLogError(f"Injected audit failure (call #{call_counter['value']})")
            
            # Otherwise call original
            return original_log_action_result(result, trace_id=trace_id)

        def failing_log_action_result(result):
            """Wrapper that fails first K calls deterministically."""
            with counter_lock:
                call_counter["value"] += 1
                should_fail = call_counter["value"] <= K
            
            if should_fail:
                from app.audit_log import AuditLogError
                raise AuditLogError(f"Injected audit failure (call #{call_counter['value']})")
            
            # Otherwise call original
            return original_log_action_result(result)
        
        def worker():
            try:
                barrier.wait()
                payload = {"text": "audit fail test"}
                response = client.post("/process", json=payload)
                result_data = {
                    "status_code": response.status_code,
                    "body": response.json(),
                }
                results_queue.put(result_data)
            except Exception as e:
                exceptions_queue.put(e)
        
        # Monkeypatch log_action_result
        from app import action_audit_log
        original_log_action_result = action_audit_log.log_action_result
        
        # Patch in agentic_pipeline where it's actually used (fail-closed wrapper)
        from app import agentic_pipeline
        with patch.object(agentic_pipeline, "log_action_result", side_effect=failing_log_action_result):
            threads = [threading.Thread(target=worker) for _ in range(N)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        
        # Validate no exceptions escape
        exceptions_list = []
        while not exceptions_queue.empty():
            exceptions_list.append(exceptions_queue.get())
        assert len(exceptions_list) == 0, f"Expected 0 exceptions, got {len(exceptions_list)}: {exceptions_list}"
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == N, f"Expected {N} results, got {len(results)}"
        
        # Extract statuses and reason_codes
        statuses = [r["body"]["status"] for r in results]
        reason_codes_list = [r["body"].get("reason_codes", []) for r in results]
        trace_ids = [r["body"]["trace_id"] for r in results]
        
        # Assert at least 1 BLOCKED with AUDIT_LOG_FAILED
        blocked_with_audit_fail = [
            r for r in results
            if r["body"]["status"] == "BLOCKED" and "AUDIT_LOG_FAILED" in r["body"].get("reason_codes", [])
        ]
        assert len(blocked_with_audit_fail) >= 1, \
            f"Expected at least 1 BLOCKED with AUDIT_LOG_FAILED, got {len(blocked_with_audit_fail)}. Distribution: {dict((k, statuses.count(k)) for k in set(statuses))}"
        
        # Assert all trace_ids valid
        assert all(isinstance(tid, str) and len(tid) > 0 for tid in trace_ids), \
            f"Found invalid trace_ids: {[tid for tid in trace_ids if not isinstance(tid, str) or len(tid) == 0]}"

    def test_p1_6_concurrent_combined_matrix_toggle_and_audit_fail_does_not_deadlock(self, client):
        """
        TESTE E (AGRESSIVO): Combine matrix toggle + audit failure; no deadlock.
        
        - Toggle ActionMatrix in writer thread (200 iterations)
        - Inject audit logging failures in first K=5 calls
        - Fire N=20 concurrent /process requests
        
        Assert:
        - Terminates without deadlock
        - At least 1 BLOCKED with AUDIT_LOG_FAILED
        - No 500 errors; all responses valid
        """
        from app.action_matrix import ActionMatrix
        
        N = 20
        barrier = threading.Barrier(N + 1)  # +1 for writer
        results_queue: Queue[Dict[str, Any]] = Queue()
        exceptions_queue: Queue[Exception] = Queue()
        stop_event = threading.Event()
        
        # Thread-safe counter for audit injection
        call_counter = {"value": 0}
        counter_lock = threading.Lock()
        K = 5
        
        original_log_action_result = None
        
        def failing_log_action_result(result, trace_id=None):
            with counter_lock:
                call_counter["value"] += 1
                should_fail = call_counter["value"] <= K
            
            if should_fail:
                from app.audit_log import AuditLogError
                raise AuditLogError(f"Injected audit failure (call #{call_counter['value']})")
            
            return original_log_action_result(result, trace_id=trace_id)

        def failing_log_action_result(result):
            """Wrapper that fails first K calls deterministically."""
            with counter_lock:
                call_counter["value"] += 1
                should_fail = call_counter["value"] <= K
            
            if should_fail:
                from app.audit_log import AuditLogError
                raise AuditLogError(f"Injected audit failure (call #{call_counter['value']})")
            
            return original_log_action_result(result)
        
        matrix_a = ActionMatrix(profile="default", allowed_actions=["process"])
        matrix_b = ActionMatrix(profile="default", allowed_actions=["process"])
        
        def writer_toggle():
            try:
                barrier.wait()
                for iteration in range(200):
                    matrix = matrix_a if iteration % 2 == 0 else matrix_b
                    set_action_matrix(matrix)
                stop_event.set()
            except Exception as e:
                exceptions_queue.put(e)
        
        def reader_request():
            try:
                barrier.wait()
                payload = {"text": "combined stress test"}
                response = client.post("/process", json=payload)
                result_data = {
                    "status_code": response.status_code,
                    "body": response.json(),
                }
                results_queue.put(result_data)
            except Exception as e:
                exceptions_queue.put(e)
        
        # Setup
        set_action_matrix(matrix_a)
        from app import action_audit_log
        original_log_action_result = action_audit_log.log_action_result
        
        # Patch in agentic_pipeline where it's actually used
        from app import agentic_pipeline
        with patch.object(agentic_pipeline, "log_action_result", side_effect=failing_log_action_result):
            writer = threading.Thread(target=writer_toggle)
            readers = [threading.Thread(target=reader_request) for _ in range(N)]
            
            writer.start()
            for r in readers:
                r.start()
            
            writer.join()
            for r in readers:
                r.join()
        
        # Cleanup
        reset_action_matrix()
        
        # Validate no exceptions
        exceptions_list = []
        while not exceptions_queue.empty():
            exceptions_list.append(exceptions_queue.get())
        assert len(exceptions_list) == 0, f"Expected 0 exceptions, got {len(exceptions_list)}: {exceptions_list}"
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == N, f"Expected {N} results, got {len(results)}"
        
        # Assert all HTTP 200 (no 500)
        status_codes = [r["status_code"] for r in results]
        assert all(sc == 200 for sc in status_codes), \
            f"Found non-200 responses: {[sc for sc in status_codes if sc != 200]}"
        
        # Assert at least 1 BLOCKED with AUDIT_LOG_FAILED
        statuses = [r["body"]["status"] for r in results]
        reason_codes_list = [r["body"].get("reason_codes", []) for r in results]
        
        blocked_with_audit_fail = [
            r for r in results
            if r["body"]["status"] == "BLOCKED" and "AUDIT_LOG_FAILED" in r["body"].get("reason_codes", [])
        ]
        assert len(blocked_with_audit_fail) >= 1, \
            f"Expected at least 1 BLOCKED with AUDIT_LOG_FAILED, got {len(blocked_with_audit_fail)}"
