import uuid
from app.agentic_pipeline import run_agentic_action
from app.executors.registry import _EXECUTORS
from app.executors.composite_executor_v1 import CompositeExecutorV1
from app.executors.llm_executor_v1 import LLMExecutorV1


def _trace_id():
    return str(uuid.uuid4())


def test_plan_digest_deterministic():
    comp = CompositeExecutorV1()
    plan = {"plan": {"steps": [{"name": "s", "executor_id": "noop_executor_v1", "input": {}, "merge": "replace"}]}, "input": {}}
    out1 = comp.execute(type("R", (), {"payload": plan, "trace_id": _trace_id()}))
    out2 = comp.execute(type("R", (), {"payload": plan, "trace_id": _trace_id()}))
    assert out1["plan"]["digest"] == out2["plan"]["digest"]


def test_max_steps_exceeded():
    comp = CompositeExecutorV1()
    steps = [{"name": f"s{i}", "executor_id": "noop_executor_v1", "input": {}, "merge": "replace"} for i in range(10)]
    payload = {"plan": {"steps": steps}, "input": {}, "limits": {"max_steps": 5}}
    res, _ = run_agentic_action("composite_run", payload, _trace_id())
    assert res.status == "FAILED"


def test_max_total_payload_bytes_pre_run(tmp_path, monkeypatch):
    audit = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit))
    comp = CompositeExecutorV1()
    big_input = {"x": "A" * 70000}
    payload = {"plan": {"steps": [{"name": "s", "executor_id": "noop_executor_v1", "input": {}, "merge": "replace"}]}, "input": big_input, "limits": {"max_total_payload_bytes": 65536}}
    res, _ = run_agentic_action("composite_run", payload, _trace_id())
    assert res.status == "FAILED"


def test_max_llm_calls_exceeded():
    comp = CompositeExecutorV1()
    # monkeypatch registry to include llm executor with LLM capability
    orig = _EXECUTORS.get("llm_executor_v1")
    _EXECUTORS["llm_executor_v1"] = LLMExecutorV1()
    steps = [
        {"name": "s1", "executor_id": "llm_executor_v1", "input": {}, "merge": "replace"},
        {"name": "s2", "executor_id": "llm_executor_v1", "input": {}, "merge": "replace"},
        {"name": "s3", "executor_id": "llm_executor_v1", "input": {}, "merge": "replace"},
    ]
    payload = {"plan": {"steps": steps}, "input": {}, "limits": {"max_llm_calls": 2}}
    try:
        res, _ = run_agentic_action("composite_run", payload, _trace_id())
        assert res.status == "FAILED"
    finally:
        if orig is not None:
            _EXECUTORS["llm_executor_v1"] = orig


def test_version_drift():
    comp = CompositeExecutorV1()
    # require impossible version
    steps = [{"name": "s", "executor_id": "noop_executor_v1", "min_executor_version": "9.9.9", "input": {}, "merge": "replace"}]
    payload = {"plan": {"steps": steps}, "input": {}}
    res, _ = run_agentic_action("composite_run", payload, _trace_id())
    assert res.status == "FAILED"


def test_privacy_sentinel_not_in_audit(tmp_path, monkeypatch):
    audit = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit))
    comp = CompositeExecutorV1()
    orig = _EXECUTORS.get("composite_executor_v1")
    _EXECUTORS["composite_executor_v1"] = comp
    try:
        payload = {"plan": {"steps": [{"name": "s", "executor_id": "noop_executor_v1", "input": {"echo": "SENSITIVE_PROMPT_123"}, "merge": "replace"}]}, "input": {}}
        res, _ = run_agentic_action("composite_run", payload, _trace_id())
        assert res.status == "SUCCESS"
        content = audit.read_text()
        assert "SENSITIVE_PROMPT_123" not in content
        # audit should contain plan.digest only
        assert "digest" in content
    finally:
        if orig is not None:
            _EXECUTORS["composite_executor_v1"] = orig
