"""Pydantic schemas for the processing endpoint.

Comments explain design reasoning (por que), not what the code does.
"""
from pydantic import BaseModel, Field, field_validator


class ProcessRequest(BaseModel):
    # Preserve the original text exactly as provided by the client while ensuring
    # it is non-empty after trimming. This keeps the API echo stable and avoids
    # surprising mutations.
    text: str = Field(..., description="Texto de entrada (não vazio)")

    @field_validator("text")
    @classmethod
    def not_empty_after_trim(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("text must be a string")
        if v.strip() == "":
            raise ValueError("text must not be empty after trimming")
        return v


class ProcessResponse(BaseModel):
    original: str = Field(..., description="Texto original do usuário (somente para eco)")
    processed: str = Field(..., description="Texto processado")
    length: int = Field(..., description="Comprimento do texto processado")

class ErrorResponse(BaseModel):
    """Normalized error envelope (G11)."""
    error: str = Field(..., description="Error code/category")
    message: str = Field(..., description="User-friendly message (no secrets)")
    trace_id: str = Field(..., description="Request trace ID for correlation")
    reason_codes: list[str] = Field(default_factory=list, description="Audit reason codes")