"""Pydantic schemas for user preferences (F9.9-A)."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class UserPreferenceUpdate(BaseModel):
    """Schema for updating preferences (PUT /api/v1/preferences/{user_id}).
    
    All fields are optional (partial update support).
    Validation patterns enforce allowed values only.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "tone_preference": "institutional",
            "output_format": "checklist",
            "language": "pt-BR"
        }
    })
    
    tone_preference: Optional[str] = Field(
        None,
        pattern="^(institutional|technical|conversational)$",
        description="Tone: institutional|technical|conversational"
    )
    output_format: Optional[str] = Field(
        None,
        pattern="^(text|bullet_points|checklist|table|structured)$",
        description="Format: text|bullet_points|checklist|table|structured"
    )
    language: Optional[str] = Field(
        None,
        pattern="^(pt-BR|en-US)$",
        description="Language: pt-BR|en-US"
    )


class UserPreferenceResponse(BaseModel):
    """Schema for returning preferences (GET /api/v1/preferences/{user_id})."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "preference_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user123",
                "tone_preference": "institutional",
                "output_format": "bullet_points",
                "language": "pt-BR",
                "created_at": "2026-01-04T10:00:00Z",
                "updated_at": "2026-01-04T11:30:00Z"
            }
        }
    )
    
    preference_id: str
    user_id: str
    tone_preference: Optional[str]
    output_format: Optional[str]
    language: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
