"""User Preferences CRUD endpoints (F9.9-A).

Implements:
- GET /api/v1/preferences/{user_id} — retrieve preferences
- PUT /api/v1/preferences/{user_id} — create or update (upsert)
- DELETE /api/v1/preferences/{user_id} — delete preferences

Governance V-COF:
- Gate F2.3 Bearer token authentication (via Depends(gate_request))
- Anti-enumeration: user_id must match X-VERITTA-USER-ID header (403 if mismatch)
- Memória dignificada: explicit preferences only (tone, format, language)
- LGPD compliance: DELETE endpoint for user control
"""

from typing import Any, Dict
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user_preference import UserPreferenceModel
from app.schemas.user_preference import UserPreferenceUpdate, UserPreferenceResponse


router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


async def gate_dependency(request: Request, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Gate F2.3 dependency (local wrapper to avoid circular import)."""
    from app.main import gate_request
    return await gate_request(request, background_tasks)


def _validate_user_id(path_user_id: str, request: Request) -> None:
    """Anti-enumeration: validate user_id from path matches X-VERITTA-USER-ID header.
    
    Args:
        path_user_id: user_id from URL path
        request: FastAPI request object
        
    Raises:
        HTTPException: 403 if user_id mismatch (anti-enumeration)
    """
    header_user_id = request.headers.get("X-VERITTA-USER-ID")
    if not header_user_id or path_user_id != header_user_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: user_id mismatch"
        )


@router.get("/{user_id}", response_model=UserPreferenceResponse)
async def get_preferences(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    gate_data: Dict[str, Any] = Depends(gate_dependency),
):
    """GET /api/v1/preferences/{user_id} — retrieve user preferences.
    
    Args:
        user_id: user identifier (from URL path)
        request: FastAPI request object
        db: database session
        gate_data: Gate F2.3 validation result
        
    Returns:
        UserPreferenceResponse: preference object with all fields
        
    Raises:
        HTTPException: 403 if user_id mismatch, 404 if not found
    """
    # Anti-enumeration validation
    _validate_user_id(user_id, request)
    
    # Query database
    preference = db.query(UserPreferenceModel).filter(
        UserPreferenceModel.user_id == user_id
    ).first()
    
    if not preference:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    return preference


@router.put("/{user_id}", response_model=UserPreferenceResponse, status_code=200)
async def update_preferences(
    user_id: str,
    payload: UserPreferenceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    gate_data: Dict[str, Any] = Depends(gate_dependency),
):
    """PUT /api/v1/preferences/{user_id} — create or update preferences (upsert).
    
    Args:
        user_id: user identifier (from URL path)
        payload: preference update payload
        request: FastAPI request object
        db: database session
        gate_data: Gate F2.3 validation result
        
    Returns:
        UserPreferenceResponse: created/updated preference object
        
    Raises:
        HTTPException: 403 if user_id mismatch, 422 if validation fails
    """
    # Anti-enumeration validation
    _validate_user_id(user_id, request)
    
    # Check if preference exists
    preference = db.query(UserPreferenceModel).filter(
        UserPreferenceModel.user_id == user_id
    ).first()
    
    if preference:
        # UPDATE: update existing preference
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(preference, key, value)
        db.commit()
        db.refresh(preference)
        return preference
    else:
        # INSERT: create new preference
        new_preference = UserPreferenceModel(
            preference_id=str(uuid4()),
            user_id=user_id,
            **payload.model_dump(exclude_unset=True)
        )
        db.add(new_preference)
        db.commit()
        db.refresh(new_preference)
        return new_preference


@router.delete("/{user_id}", status_code=204)
async def delete_preferences(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    gate_data: Dict[str, Any] = Depends(gate_dependency),
):
    """DELETE /api/v1/preferences/{user_id} — delete user preferences (LGPD compliance).
    
    Args:
        user_id: user identifier (from URL path)
        request: FastAPI request object
        db: database session
        gate_data: Gate F2.3 validation result
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: 403 if user_id mismatch, 404 if not found
    """
    # Anti-enumeration validation
    _validate_user_id(user_id, request)
    
    # Query database
    preference = db.query(UserPreferenceModel).filter(
        UserPreferenceModel.user_id == user_id
    ).first()
    
    if not preference:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    # Delete preference
    db.delete(preference)
    db.commit()
    
    return None  # 204 No Content
