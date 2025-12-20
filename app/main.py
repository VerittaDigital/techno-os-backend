"""Minimal FastAPI application for the Techno OS repository.

Design notes:
- Keep endpoints small and deterministic.
- Validate inputs with Pydantic and return stable JSON responses.
- Fail safely with clear, non-technical messages.
"""
from fastapi import FastAPI, HTTPException

from .schemas import ProcessRequest, ProcessResponse

app = FastAPI(title="Techno OS API", version="0.1.0")


@app.get("/health", tags=["health"])
def health():
    """Lightweight health check used by orchestration and tests."""
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse, tags=["processing"])
def process(payload: ProcessRequest):
    """Deterministic text processing endpoint.

    - Keeps behaviour explicit and side-effect free.
    - Validates input to guarantee stable response schema.
    """
    text = payload.text.strip()
    if not text:
        # Fail-safe user-focused message; no stack traces exposed.
        raise HTTPException(status_code=400, detail="`text` must not be empty after trimming.")

    processed = text.upper()
    return ProcessResponse(original=payload.text, processed=processed, length=len(processed))
