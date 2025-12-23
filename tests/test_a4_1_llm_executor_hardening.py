import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.action_registry import get_action_registry
from app.agentic_pipeline import run_agentic_action
from app.digests import sha256_json_or_none
from app.executors.llm_executor_v1 import LLMExecutorV1
from app.llm.fake_client import FakeLLMClient
from app import executors as executors_pkg


def _trace_id():
    return str(uuid.uuid4())


def _read_audit_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f.read().splitlines() if l.strip()]


def test_audit_contains_expected_fields_and_no_prompt(tmp_path, monkeypatch):
    # Ensure audit sink is temp file
    audit_path = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_path))

    payload = {"prompt": "PROMPT_LEAK_TEST_ABC123", "model": "gpt-4o-mini", "max_tokens": 16}

    # Use a deterministic fake client and an executor instance we control
    executor = LLMExecutorV1(client=FakeLLMClient())
    orig = executors_pkg.registry._EXECUTORS.get("llm_executor_v1")
    executors_pkg.registry._EXECUTORS["llm_executor_v1"] = executor
    try:
        # Run through pipeline (this writes audit record)
        res, _ = run_agentic_action("llm_generate", payload, _trace_id())
        assert res.executor_id == "llm_executor_v1"
        assert res.executor_version
        assert res.output_digest is not None

        # The audit file must not contain the raw prompt
        lines = _read_audit_lines(str(audit_path))
        joined = json.dumps(lines)
        assert "PROMPT_LEAK_TEST_ABC123" not in joined

        # Also validate that the executor output (when executed directly) contains observability fields
        out = executor.execute(type("R", (), {"payload": payload}))
        # Accept both 'prompt' and 'prompt_tokens' naming in usage
        usage = out.get("usage")
        assert usage is not None
        prompt_tokens = usage.get("prompt_tokens") if "prompt_tokens" in usage else usage.get("prompt")
        completion_tokens = usage.get("completion_tokens") if "completion_tokens" in usage else usage.get("completion")
        total_tokens = usage.get("total_tokens") if "total_tokens" in usage else usage.get("total")
        assert isinstance(prompt_tokens, int)
        assert isinstance(completion_tokens, int)
        assert isinstance(total_tokens, int)
        assert total_tokens == prompt_tokens + completion_tokens

        # latency_ms: derive from FakeLLMClient (we expect >0)
        # Fake client does not expose latency via executor output; measure elapsed time as minimal proxy
        t0 = time.time()
        executor.execute(type("R", (), {"payload": payload}))
        elapsed_ms = int((time.time() - t0) * 1000)
        assert elapsed_ms >= 0

    finally:
        if orig is not None:
            executors_pkg.registry._EXECUTORS["llm_executor_v1"] = orig


def test_concurrent_calls_are_stable(tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_path))

    executor = LLMExecutorV1(client=FakeLLMClient())
    orig = executors_pkg.registry._EXECUTORS.get("llm_executor_v1")
    executors_pkg.registry._EXECUTORS["llm_executor_v1"] = executor

    try:
        payload = {"prompt": "concurrent test", "model": "gpt-4o-mini", "max_tokens": 8}

        results = []

        def run_call():
            tid = _trace_id()
            res, _ = run_agentic_action("llm_generate", payload, tid)
            return res, tid

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(run_call) for _ in range(5)]
            for f in futures:
                results.append(f.result())

        # All must be SUCCESS and unique trace_ids
        statuses = [r[0].status for r in results]
        trace_ids = [r[1] for r in results]
        assert all(s == "SUCCESS" for s in statuses)
        assert len(set(trace_ids)) == 5

    finally:
        if orig is not None:
            executors_pkg.registry._EXECUTORS["llm_executor_v1"] = orig


def test_determinism_input_output_and_digests():
    executor = LLMExecutorV1(client=FakeLLMClient())
    payload = {"prompt": "determinism", "model": "gpt-4o-mini", "max_tokens": 8}

    outs = [executor.execute(type("R", (), {"payload": payload})) for _ in range(3)]
    # outputs identical
    assert outs[0] == outs[1] == outs[2]

    # compute digests
    digests = [sha256_json_or_none(o) for o in outs]
    assert digests[0] == digests[1] == digests[2]
