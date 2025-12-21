"""Basic tests for the FastAPI endpoints.

These tests act as a quick audit: behaviour is predictable and schema-stable.

LEGACY STATUS (2025-12-21):
These tests validate the original MVP /process contract with "processed"/"length"/"original" fields.
The current production contract uses the V-COF governed pipeline (gate + agentic_pipeline)
with ActionResult schema (status/trace_id/output_digest/reason_codes).

The legacy MVP endpoint has been retired. These tests are preserved for historical reference
but marked as skipped to avoid breaking CI.

Current equivalent tests:
- tests/test_gate_http_enforcement.py (28 tests)
- tests/test_gate_pipeline_integration.py (8 tests)
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

# Skip entire module - legacy MVP contract no longer in production
pytestmark = pytest.mark.skip(reason="Legacy MVP contract; replaced by gate/pipeline tests")


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_process_success():
    r = client.post("/process", json={"text": " hello "})
    assert r.status_code == 200
    data = r.json()
    assert data["processed"] == "HELLO"
    assert data["length"] == 5
    assert data["original"] == " hello "


def test_process_empty_rejected():
    r = client.post("/process", json={"text": ""})
    # Pydantic validation rejects empty string and FastAPI returns 422
    assert r.status_code == 422
