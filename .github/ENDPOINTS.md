# Endpoints (minimal)

## /health (GET)
- Purpose: lightweight health check for orchestration and tests.
- Response: { "status": "ok" }

## /process (POST)
- Purpose: deterministic text processing with input validation.
- Request JSON schema (Pydantic `ProcessRequest`):
  - `text`: string, required, non-empty after trimming
- Response JSON schema (Pydantic `ProcessResponse`):
  - `original`: original text
  - `processed`: processed text (uppercase)
  - `length`: length of processed text

### Run locally (example)
1. Create a virtualenv and install deps:

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. Run the app with Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

3. Test endpoints:
- Health: `GET http://localhost:8000/health`
- Process: `POST http://localhost:8000/process` with JSON `{ "text": "hello" }`

Notes:
- Behaviour is deterministic and side-effect free (no storage).
- Validation is handled with Pydantic to preserve a stable JSON contract.

## Notes
This document describes the initial MVP endpoints and may evolve as the system grows.
