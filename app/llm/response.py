"""LLM Response standardization (F9.9-B, V-COF governed).

LLMResponse Pydantic normaliza respostas de todos os providers.
"""

from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator


class TokenUsage(BaseModel):
    """Token usage breakdown (OpenAI compatible)."""

    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)


class LLMResponse(BaseModel):
    """LLM response standard (F9.9-B normalized contract).
    
    Todos os adapters devem retornar LLMResponse.
    """

    text: str = Field(..., description="Generated text content")
    model: str = Field(..., description="Model used for generation")
    usage: Optional[TokenUsage] = Field(None, description="Token usage stats")
    latency_ms: float = Field(..., ge=0, description="Request latency in milliseconds")
    provider: str = Field(..., description="Provider name (openai, anthropic, etc)")

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        """Fail-closed: text nunca vazio."""
        if not v or not v.strip():
            raise ValueError("LLM response text cannot be empty")
        return v
