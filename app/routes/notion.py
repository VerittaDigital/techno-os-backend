"""app/routes/notion.py - Notion read-only endpoints (fail-closed)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Dict

from app.integrations.notion_client import (
    get_agents, get_arcontes, get_audit, get_actions, get_evidence, get_pipelines, get_docs, get_governance
)

router = APIRouter(prefix="/v1/notion", tags=["notion"])

async def validate_headers(request: Request):
    """Fail-closed: require X-Request-ID and X-Client-Version."""
    if not request.headers.get("X-Request-ID"):
        raise HTTPException(status_code=400, detail="BLOCKED: Missing X-Request-ID")
    if not request.headers.get("X-Client-Version"):
        raise HTTPException(status_code=400, detail="BLOCKED: Missing X-Client-Version")

@router.get("/agents", dependencies=[Depends(validate_headers)])
async def list_agents() -> List[Dict]:
    try:
        return await get_agents()
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            raise HTTPException(status_code=403, detail="BLOCKED: MISSING_CONFIG")
        raise HTTPException(status_code=500, detail="BLOCKED: Internal error")

@router.get("/arcontes", dependencies=[Depends(validate_headers)])
async def list_arcontes() -> List[Dict]:
    try:
        return await get_arcontes()
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            raise HTTPException(status_code=403, detail="BLOCKED: MISSING_CONFIG")
        raise HTTPException(status_code=500, detail="BLOCKED: Internal error")

@router.get("/audit", dependencies=[Depends(validate_headers)])
async def list_audit() -> List[Dict]:
    try:
        return await get_audit()
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            raise HTTPException(status_code=403, detail="BLOCKED: MISSING_CONFIG")
        raise HTTPException(status_code=500, detail="BLOCKED: Internal error")

@router.get("/actions", dependencies=[Depends(validate_headers)])
async def list_actions() -> List[Dict]:
    try:
        return await get_actions()
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            raise HTTPException(status_code=403, detail="BLOCKED: MISSING_CONFIG")
        raise HTTPException(status_code=500, detail="BLOCKED: Internal error")

@router.get("/evidence", dependencies=[Depends(validate_headers)])
async def list_evidence() -> List[Dict]:
    try:
        return await get_evidence()
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            raise HTTPException(status_code=403, detail="BLOCKED: MISSING_CONFIG")
        raise HTTPException(status_code=500, detail="BLOCKED: Internal error")

@router.get("/pipelines", dependencies=[Depends(validate_headers)])
async def list_pipelines() -> List[Dict]:
    try:
        return await get_pipelines()
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            raise HTTPException(status_code=403, detail="BLOCKED: MISSING_CONFIG")
        raise HTTPException(status_code=500, detail="BLOCKED: Internal error")

@router.get("/docs", dependencies=[Depends(validate_headers)])
async def list_docs() -> List[Dict]:
    try:
        return await get_docs()
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            raise HTTPException(status_code=403, detail="BLOCKED: MISSING_CONFIG")
        raise HTTPException(status_code=500, detail="BLOCKED: Internal error")

@router.get("/governance", dependencies=[Depends(validate_headers)])
async def list_governance() -> List[Dict]:
    try:
        return await get_governance()
    except Exception as e:
        if str(e) == "MISSING_CONFIG":
            raise HTTPException(status_code=403, detail="BLOCKED: MISSING_CONFIG")
        raise HTTPException(status_code=500, detail="BLOCKED: Internal error")