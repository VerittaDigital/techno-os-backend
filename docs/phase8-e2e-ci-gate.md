# Phase 8: E2E CI Gate

## Overview
E2E validation gate for production readiness, ensuring fail-closed behavior and operator diagnostics without secrets.

## Features
- **Caching**: Prevents rate limits with 30s TTL.
- **Diagnostics**: Distinguishes permission issues (403/404) from auth (401) and rate limits (429).
- **Timing**: Measures response times.
- **Sanitization**: No URLs or IDs in responses.

## Implementation
- Backend: notion_client.py self_test updated.
- Console: UI renders code, message_safe, duration_ms.
- Envelope: Stable, sanitized trace_id.

## Gate Criteria
- All surfaces pass or blocked with known codes.
- No raw errors exposed.
- Cache reduces API calls.

## Evidence
- Tests pass.
- Smoke validates schema.
- Commits: backend c53f92a, console 110a970.