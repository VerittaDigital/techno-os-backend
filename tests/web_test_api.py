"""Basic tests for the FastAPI endpoints.

These tests act as a quick audit: behaviour is predictable and schema-stable.
"""
from fastapi.testclient import TestClient

from app.main import app


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
