import uuid

from app.llm.fake_client import FakeLLMClient
from app.executors.llm_executor_v1 import LLMExecutorV1
from app.action_registry import get_action_registry
from app.agentic_pipeline import run_agentic_action
from app.executors import registry as exec_registry


def _trace_id() -> str:
    return str(uuid.uuid4())


def test_registry_contains_llm_generate():
    registry = get_action_registry()
    assert "llm_generate" in registry.actions
    meta = registry.actions["llm_generate"]
    assert meta["executor"] == "llm_executor_v1"


def test_happy_path_fake_llm(tmp_path, monkeypatch):
    # Use temp audit log to inspect persisted audits
    audit_path = tmp_path / "audit.log"
    monkeypatch.setenv("VERITTA_AUDIT_LOG_PATH", str(audit_path))

    # Ensure registry executor uses FakeLLMClient by default
    # Run via pipeline to exercise audit
    payload = {"prompt": "hello world", "model": "gpt-4o-mini", "max_tokens": 16}
    res, _ = run_agentic_action("llm_generate", payload, _trace_id())
    assert res.status == "SUCCESS"

    # Audit file should not contain raw prompt
    content = audit_path.read_text()
    assert "hello world" not in content


def test_policy_violation_results_in_failed(monkeypatch):
    # disallowed model
    payload = {"prompt": "hi", "model": "gpt-3.5", "max_tokens": 16}
    res, _ = run_agentic_action("llm_generate", payload, _trace_id())
    assert res.status == "FAILED"


def test_timeout_simulated(monkeypatch):
    # Replace registry entry with an executor using a fake client that times out
    timed_executor = LLMExecutorV1(client=FakeLLMClient(simulate_timeout=True))
    # Swap into registry and restore after
    orig = exec_registry._EXECUTORS.get("llm_executor_v1")
    exec_registry._EXECUTORS["llm_executor_v1"] = timed_executor
    try:
        payload = {"prompt": "hi", "model": "gpt-4o-mini", "max_tokens": 16}
        res, _ = run_agentic_action("llm_generate", payload, _trace_id())
        # Timeout in executor should surface as FAILED by pipeline
        assert res.status == "FAILED"
    finally:
        if orig is not None:
            exec_registry._EXECUTORS["llm_executor_v1"] = orig


def test_determinism_of_fake_client():
    client = FakeLLMClient()
    a = client.generate(prompt="same prompt", model="gpt-4o-mini", temperature=0.0, max_tokens=10, timeout_s=1)
    b = client.generate(prompt="same prompt", model="gpt-4o-mini", temperature=0.0, max_tokens=10, timeout_s=1)
    assert a["text"] == b["text"]
