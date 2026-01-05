"""Pydantic schemas for user preferences API (F9.9-A).

Schemas enforce fail-closed validation with allowlist enums.
API uses simplified field names (tone, output_format, language).
DB uses full names (tone_preference, output_format, language).
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ToneEnum(str, Enum):
    """Allowed tone preferences (fail-closed allowlist)."""
    institucional = "institucional"
    tecnico = "tecnico"
    casual = "casual"


class OutputFormatEnum(str, Enum):
    """Allowed output format preferences (fail-closed allowlist)."""
    json = "json"
    markdown = "markdown"
    checklist = "checklist"


class LanguageEnum(str, Enum):
    """Allowed language preferences (fail-closed allowlist)."""
    pt_br = "pt-BR"
    en_us = "en-US"


class PreferencesPutRequest(BaseModel):
    """Request body for PUT /api/v1/preferences.
    
    All fields are optional (partial update).
    user_id is NEVER accepted in payload (extracted from auth header).
    """
    tone: Optional[ToneEnum] = Field(None, description="Preferred tone (institucional/tecnico/casual)")
    output_format: Optional[OutputFormatEnum] = Field(None, description="Preferred output format")
    language: Optional[LanguageEnum] = Field(None, description="Preferred language")
    
    @field_validator("tone", "output_format", "language", mode="before")
    @classmethod
    def reject_empty_strings(cls, v):
        """Convert empty strings to None (treat as unset)."""
        if v == "":
            return None
        return v


class PreferencesGetResponse(BaseModel):
    """Response for GET /api/v1/preferences.
    
    Returns current preferences for authenticated user.
    Null values indicate preference not set.
    """
    model_config = {"json_schema_extra": {
        "example": {
            "user_id": "u_12345678",
            "tone": "institucional",
            "output_format": "markdown",
            "language": "pt-BR"
        }
    }}
    
    user_id: str = Field(..., description="User identifier (from auth)")
    tone: Optional[str] = Field(None, description="Current tone preference")
    output_format: Optional[str] = Field(None, description="Current output format preference")
    language: Optional[str] = Field(None, description="Current language preference")


class PreferencesPutResponse(BaseModel):
    """Response for PUT /api/v1/preferences.
    
    Echoes back updated preferences.
    """
    user_id: str = Field(..., description="User identifier")
    tone: Optional[str] = Field(None, description="Updated tone preference")
    output_format: Optional[str] = Field(None, description="Updated output format preference")
    language: Optional[str] = Field(None, description="Updated language preference")
    message: str = Field("Preferences updated successfully", description="Success message")
