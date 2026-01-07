# Phase 8: Notion Share Audit

## Overview
Phase 8 implements E2E validation gate with permissions diagnostics, caching, and stable reason codes for Notion read-only integration.

## Changes
- **Backend self_test**: Added caching (TTL 30s), timing, specific HTTP status mapping (401→NOTION_AUTH_FAILED, 403→NOTION_FORBIDDEN, 404→NOTION_NOT_SHARED, 429→RATE_LIMITED).
- **Schema**: New result format with name, status, code, message_safe, duration_ms.
- **Console UI**: Updated to render new fields, added copy summary button.
- **Tests**: Updated for new schema.
- **Smoke**: Validates schema presence.

## Validation
- Anti-network: Only Notion API calls.
- Secret scan: Clean.
- Tests: Pass.
- Smoke: Requires backend running (status envelope validated).

## Commit
- Backend: c53f92a
- Console: 110a970