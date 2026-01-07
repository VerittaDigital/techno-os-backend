"""app/routes/notion.py - Notion read-only endpoints (fail-closed)."""

from fastapi import APIRouter, Depends, Request, Response
from typing import List, Dict
import uuid
import json
import os

from app.integrations.notion_client import (
    get_agents, get_arcontes, get_audit, get_actions, get_evidence, get_pipelines, get_docs, get_governance_summary, self_test
)

router = APIRouter(prefix="/v1/notion", tags=["notion"])

async def validate_headers(request: Request):
    """Fail-closed: require all headers, return trace_id."""
    trace_id = str(uuid.uuid4())
    missing = []
    x_api_key = request.headers.get("X-API-Key")
    if not request.headers.get("X-Request-ID"):
        missing.append("X-Request-ID")
    if not request.headers.get("X-Timestamp"):
        missing.append("X-Timestamp")
    if not request.headers.get("X-Client-Version"):
        missing.append("X-Client-Version")
    if not x_api_key:
        missing.append("X-API-Key")
    if missing:
        return Response(
            status_code=200,
            content='{"status": "blocked", "reason": "Missing required headers: ' + ', '.join(missing) + '", "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    # Check API key value if env is set
    expected_key = os.environ.get("VERITTA_BETA_API_KEY")
    if expected_key and x_api_key != expected_key:
        return Response(
            status_code=200,
            content='{"status": "blocked", "reason": "Invalid API key", "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    return trace_id

@router.get("/agents")
async def list_agents(trace_id_or_response = Depends(validate_headers)):
    if isinstance(trace_id_or_response, Response):
        return trace_id_or_response
    trace_id = trace_id_or_response
    try:
        data = await get_agents()
        return Response(
            status_code=200,
            content='{"status": "success", "data": ' + str(data).replace("'", '"') + ', "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            return Response(
                status_code=200,
                content='{"status": "blocked", "reason": "Notion not configured", "trace_id": "' + trace_id + '"}',
                media_type="application/json",
                headers={"X-Trace-Id": trace_id}
            )
        return Response(
            status_code=200,
            content='{"status": "error", "message": "Internal error", "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )

@router.get("/arcontes")
async def list_arcontes(trace_id_or_response = Depends(validate_headers)):
    if isinstance(trace_id_or_response, Response):
        return trace_id_or_response
    trace_id = trace_id_or_response
    try:
        data = await get_arcontes()
        return Response(
            status_code=200,
            content='{"status": "success", "data": ' + str(data).replace("'", '"') + ', "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            return Response(
                status_code=200,
                content='{"status": "blocked", "reason": "Notion not configured", "trace_id": "' + trace_id + '"}',
                media_type="application/json",
                headers={"X-Trace-Id": trace_id}
            )
        return Response(
            status_code=200,
            content='{"status": "error", "message": "Internal error", "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )

@router.get("/audit")
async def list_audit(trace_id_or_response = Depends(validate_headers)):
    if isinstance(trace_id_or_response, Response):
        return trace_id_or_response
    trace_id = trace_id_or_response
    try:
        data = await get_audit()
        return Response(
            status_code=200,
            content='{"status": "success", "data": ' + str(data).replace("'", '"') + ', "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            return Response(
                status_code=200,
                content='{"status": "blocked", "reason": "Notion not configured", "trace_id": "' + trace_id + '"}',
                media_type="application/json",
                headers={"X-Trace-Id": trace_id}
            )
        return Response(
            status_code=200,
            content='{"status": "error", "message": "Internal error", "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )

@router.get("/actions")
async def list_actions(trace_id_or_response = Depends(validate_headers)):
    if isinstance(trace_id_or_response, Response):
        return trace_id_or_response
    trace_id = trace_id_or_response
    try:
        data = await get_actions()
        return Response(
            status_code=200,
            content='{"status": "success", "data": ' + str(data).replace("'", '"') + ', "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            return Response(
                status_code=200,
                content='{"status": "blocked", "reason": "Notion not configured", "trace_id": "' + trace_id + '"}',
                media_type="application/json",
                headers={"X-Trace-Id": trace_id}
            )
        return Response(
            status_code=200,
            content='{"status": "error", "message": "Internal error", "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )

@router.get("/evidence")
async def list_evidence(trace_id_or_response = Depends(validate_headers)):
    if isinstance(trace_id_or_response, Response):
        return trace_id_or_response
    trace_id = trace_id_or_response
    try:
        data = await get_evidence()
        return Response(
            status_code=200,
            content='{"status": "success", "data": ' + str(data).replace("'", '"') + ', "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            return Response(
                status_code=200,
                content='{"status": "blocked", "reason": "Notion not configured", "trace_id": "' + trace_id + '"}',
                media_type="application/json",
                headers={"X-Trace-Id": trace_id}
            )
        return Response(
            status_code=200,
            content='{"status": "error", "message": "Internal error", "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )

@router.get("/docs")
async def list_docs(trace_id_or_response = Depends(validate_headers)):
    if isinstance(trace_id_or_response, Response):
        return trace_id_or_response
    trace_id = trace_id_or_response
    try:
        data = await get_docs()
        return Response(
            status_code=200,
            content='{"status": "success", "data": ' + str(data).replace("'", '"') + ', "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            return Response(
                status_code=200,
                content='{"status": "blocked", "reason": "Notion not configured", "trace_id": "' + trace_id + '"}',
                media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
        return Response(
            status_code=200,
            content='{"status": "error", "message": "Internal error", "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )

@router.get("/governance/summary")
async def list_governance_summary(trace_id_or_response = Depends(validate_headers)):
    if isinstance(trace_id_or_response, Response):
        return trace_id_or_response
    trace_id = trace_id_or_response
    try:
        data = await get_governance_summary()
        return Response(
            status_code=200,
            content='{"status": "success", "data": ' + str(data).replace("'", '"') + ', "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            return Response(
                status_code=200,
                content='{"status": "blocked", "reason": "Notion not configured", "trace_id": "' + trace_id + '"}',
                media_type="application/json",
                headers={"X-Trace-Id": trace_id}
            )
        return Response(
            status_code=200,
            content='{"status": "error", "message": "Internal error", "trace_id": "' + trace_id + '"}',
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )

@router.get("/self_test")
async def self_test_endpoint(trace_id_or_response = Depends(validate_headers)):
    if isinstance(trace_id_or_response, Response):
        return trace_id_or_response
    trace_id = trace_id_or_response
    try:
        checks = await self_test()
        overall_status = "success" if all(c["status"] == "pass" for c in checks) else "blocked"
        return Response(
            status_code=200,
            content=json.dumps({"status": overall_status, "data": checks, "trace_id": trace_id}),
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    except Exception as e:
        return Response(
            status_code=200,
            content=json.dumps({"status": "error", "message": "Internal error", "trace_id": trace_id}),
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
@router.get("/config_summary")
async def config_summary_endpoint(trace_id_or_response = Depends(validate_headers)):
    if isinstance(trace_id_or_response, Response):
        return trace_id_or_response
    trace_id = trace_id_or_response
    try:
        summary = {
            "notion_token_present": bool(os.getenv("NOTION_TOKEN")),
            "whitelist_loaded": True,  # Assuming always loaded
            "cache_ttl_seconds": 30,
            "client_version_seen": None  # From header if present
        }
        return Response(
            status_code=200,
            content=json.dumps({"status": "success", "data": summary, "trace_id": trace_id}),
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )
    except Exception as e:
        return Response(
            status_code=200,
            content=json.dumps({"status": "error", "message": "Internal error", "trace_id": trace_id}),
            media_type="application/json",
            headers={"X-Trace-Id": trace_id}
        )