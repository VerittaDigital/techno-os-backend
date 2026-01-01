import uuid

from app.agentic_pipeline import run_agentic_action
from app.action_registry import get_action_registry
from app.action_router import route_action
from app.executors.registry import _EXECUTORS
from app.executors.composite_executor_v1 import CompositeExecutorV1


def _trace_id():
    return str(uuid.uuid4())


def test_registry_and_routing():
    registry = get_action_registry()
    assert "composite_run" in registry.actions
    assert registry.actions["composite_run"]["executor"] == "composite_executor_v1"
    assert route_action("composite_run") == "composite_executor_v1"


def test_happy_path_two_steps(tmp_path, monkeypatch):
    # Use temp audit log
    audit_path = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_path))

    # Ensure composite registered
    comp = CompositeExecutorV1()
    orig = _EXECUTORS.get("composite_executor_v1")
    _EXECUTORS["composite_executor_v1"] = comp

    # ensure rule evaluator and noop exist (they are in registry by default)
    try:
        plan = {
            "plan": {"steps": [
                {"name": "step1", "executor_id": "rule_evaluator_v1", "input": {"rules": [{"field":"x","op":"==","value":1}], "input": {"x":1}}, "merge": "merge_under", "output_key": "rules"},
                {"name": "step2", "executor_id": "noop_executor_v1", "input": {}, "merge": "merge_under", "output_key": "noop"}
            ]},
            "input": {},
        }

        # Run via pipeline to get audit/status
        res, _ = run_agentic_action("composite_run", plan, _trace_id())
        assert res.status == "SUCCESS"

        # Execute directly to inspect output
        out = comp.execute(type("R", (), {"payload": plan, "trace_id": _trace_id()}))
        assert out["composite"]["steps_executed"] == 2
        assert isinstance(out["steps"][0]["output_digest"], str)
        assert isinstance(out["result_digest"], str)
    finally:
        if orig is not None:
            _EXECUTORS["composite_executor_v1"] = orig


def test_validation_failures(monkeypatch):
    # empty steps
    payload = {"plan": {"steps": []}, "input": {}}
    res, _ = run_agentic_action("composite_run", payload, _trace_id())
    assert res.status == "FAILED"

    # too many steps
    payload = {"plan": {"steps": [{} for _ in range(20)]}, "input": {}}
    res, _ = run_agentic_action("composite_run", payload, _trace_id())
    assert res.status == "FAILED"


def test_fail_closed_step_runtime(monkeypatch):
    # monkeypatch a failing executor
    class Failer:
        version = "1.0.0"
        def execute(self, req):
            raise RuntimeError("boom")

    orig = _EXECUTORS.get("rule_evaluator_v1")
    _EXECUTORS["rule_evaluator_v1"] = Failer()
    try:
        plan = {"plan": {"steps": [{"name": "bad", "executor_id": "rule_evaluator_v1", "input": {}, "merge": "replace"}]}, "input": {}}
        res, _ = run_agentic_action("composite_run", plan, _trace_id())
        assert res.status == "FAILED"
    finally:
        if orig is not None:
            _EXECUTORS["rule_evaluator_v1"] = orig


def test_privacy_no_prompt_leak(tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_path))

    comp = CompositeExecutorV1()
    orig = _EXECUTORS.get("composite_executor_v1")
    _EXECUTORS["composite_executor_v1"] = comp
    try:
        payload = {"plan": {"steps": [{"name": "s1", "executor_id": "noop_executor_v1", "input": {"echo": "SENSITIVE_PROMPT_123"}, "merge": "replace"}]}, "input": {}}
        res, _ = run_agentic_action("composite_run", payload, _trace_id())
        assert res.status == "SUCCESS"
        content = audit_path.read_text()
        assert "SENSITIVE_PROMPT_123" not in content
    finally:
        if orig is not None:
            _EXECUTORS["composite_executor_v1"] = orig


def test_determinism():
    comp = CompositeExecutorV1()
    payload = {"plan": {"steps": [{"name": "s", "executor_id": "noop_executor_v1", "input": {}, "merge": "replace"}]}, "input": {}}
    out1 = comp.execute(type("R", (), {"payload": payload, "trace_id": _trace_id()}))
    out2 = comp.execute(type("R", (), {"payload": payload, "trace_id": _trace_id()}))
    assert out1["result_digest"] == out2["result_digest"]
    assert out1["steps"][0]["output_digest"] == out2["steps"][0]["output_digest"]
