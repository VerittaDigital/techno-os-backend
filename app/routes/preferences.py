"""User preferences API routes (F9.9-A).

Endpoints:
- GET /api/v1/preferences: Retrieve user's current preferences
- PUT /api/v1/preferences: Update user's preferences (partial update)

Governance:
- user_id extracted from F2.3 auth (never from request body)
- Fail-closed validation (enum allowlists)
- No-log policy (preference values never logged)
- Privacy-by-design (explicit state only)
"""

import hashlib
import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies.auth import get_user_from_gate
from app.env import get_database_url
from app.models.user_preference import UserPreference, Base
from app.schemas.preferences import (
    PreferencesGetResponse,
    PreferencesPutRequest,
    PreferencesPutResponse,
)

# Router configuration
router = APIRouter(prefix="/api/v1", tags=["preferences"])

# Database setup (reuse connection from main app if available)
engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_user_id(user_id: str) -> str:
    """Hash user_id for logging (privacy-by-design).
    
    Returns first 8 chars of SHA256 hash for log correlation.
    """
    return hashlib.sha256(user_id.encode()).hexdigest()[:8]


@router.get(
    "/preferences",
    response_model=PreferencesGetResponse,
    summary="Get user preferences",
    description="Retrieve current preferences for authenticated user (F2.3 auth required)"
)
async def get_preferences(
    request: Request,
    user_id: str = Depends(get_user_from_gate),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/preferences
    
    Returns user's current preferences.
    Null values indicate preference not set.
    
    Auth: Requires F2.3 Bearer token + X-VERITTA-USER-ID header.
    """
    trace_id = getattr(request.state, "trace_id", str(uuid4()))
    
    try:
        # Query existing preferences
        pref = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()
        
        if pref is None:
            # No preferences set yet - return defaults (all null)
            logging.info(
                f"action=preferences_get user_id_hash={hash_user_id(user_id)} "
                f"status=not_found trace_id={trace_id}"
            )
            return PreferencesGetResponse(
                user_id=user_id,
                tone=None,
                output_format=None,
                language=None,
            )
        
        # Return existing preferences (NO logging of values)
        logging.info(
            f"action=preferences_get user_id_hash={hash_user_id(user_id)} "
            f"status=success trace_id={trace_id}"
        )
        
        return PreferencesGetResponse(
            user_id=user_id,
            tone=pref.tone_preference,
            output_format=pref.output_format,
            language=pref.language,
        )
    
    except SQLAlchemyError as e:
        # Database error - fail-closed
        logging.error(
            f"action=preferences_get user_id_hash={hash_user_id(user_id)} "
            f"status=db_error trace_id={trace_id} error={type(e).__name__}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to retrieve preferences",
                "trace_id": trace_id,
            }
        )


@router.put(
    "/preferences",
    response_model=PreferencesPutResponse,
    summary="Update user preferences",
    description="Update preferences for authenticated user (partial update supported)"
)
async def put_preferences(
    request: Request,
    body: PreferencesPutRequest,
    user_id: str = Depends(get_user_from_gate),
    db: Session = Depends(get_db),
):
    """
    PUT /api/v1/preferences
    
    Updates user preferences (partial update - only specified fields).
    Creates preference record if it doesn't exist (upsert).
    
    Auth: Requires F2.3 Bearer token + X-VERITTA-USER-ID header.
    
    Fail-closed:
    - Invalid enum value → HTTP 400
    - user_id in payload → HTTP 400 (rejected by schema, not accepted)
    - Database error → HTTP 500
    """
    trace_id = getattr(request.state, "trace_id", str(uuid4()))
    
    # Reject if user_id appears in raw body (fail-closed security)
    raw_body = await request.body()
    if b"user_id" in raw_body:
        logging.warning(
            f"action=preferences_put user_id_hash={hash_user_id(user_id)} "
            f"status=rejected_user_id_in_payload trace_id={trace_id}"
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": "bad_request",
                "message": "user_id cannot be specified in request body",
                "trace_id": trace_id,
            }
        )
    
    try:
        # Query existing preferences
        pref = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()
        
        if pref is None:
            # Create new preference record (upsert)
            pref = UserPreference(
                preference_id=str(uuid4()),
                user_id=user_id,
                tone_preference=body.tone.value if body.tone else None,
                output_format=body.output_format.value if body.output_format else None,
                language=body.language.value if body.language else None,
            )
            db.add(pref)
            action_type = "create"
        else:
            # Update existing preferences (partial update)
            if body.tone is not None:
                pref.tone_preference = body.tone.value
            if body.output_format is not None:
                pref.output_format = body.output_format.value
            if body.language is not None:
                pref.language = body.language.value
            action_type = "update"
        
        db.commit()
        db.refresh(pref)
        
        # Log success (NO preference values)
        logging.info(
            f"action=preferences_put user_id_hash={hash_user_id(user_id)} "
            f"status=success type={action_type} trace_id={trace_id}"
        )
        
        return PreferencesPutResponse(
            user_id=user_id,
            tone=pref.tone_preference,
            output_format=pref.output_format,
            language=pref.language,
            message="Preferences updated successfully",
        )
    
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(
            f"action=preferences_put user_id_hash={hash_user_id(user_id)} "
            f"status=db_error trace_id={trace_id} error={type(e).__name__}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to update preferences",
                "trace_id": trace_id,
            }
        )
