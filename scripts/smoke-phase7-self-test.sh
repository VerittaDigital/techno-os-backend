#!/bin/bash

# Smoke test for Phase 8 E2E Validation Gate

echo "Testing gateway health..."
HEALTH_RESP=$(curl -s -H "X-Request-ID: $(uuidgen)" -H "X-Timestamp: $(date -Iseconds)" -H "X-Client-Version: backend-phase8-e2e-gate" http://localhost:8000/health)
echo "Health: $HEALTH_RESP"

echo -e "\nTesting Notion self-test..."
SELF_RESP=$(curl -s -H "X-API-Key: test-key" -H "X-Request-ID: $(uuidgen)" -H "X-Timestamp: $(date -Iseconds)" -H "X-Client-Version: backend-phase8-e2e-gate" http://localhost:8000/v1/notion/self_test)

STATUS=$(echo "$SELF_RESP" | jq -r '.status')
TRACE_ID=$(echo "$SELF_RESP" | jq -r '.trace_id')
DATA=$(echo "$SELF_RESP" | jq -r '.data')

echo "Status: $STATUS"
echo "Trace ID (sanitized): $(echo "$TRACE_ID" | sed 's/\(token\|apikey\|signature\|secret\|password\|pwd\)=[^&]*/\1=***/g' | sed 's/\(\w\+\):\([^@]\+\)@/\1:***@/g')"

if [[ "$STATUS" == "success" || "$STATUS" == "blocked" ]]; then
  echo "Envelope valid."
else
  echo "BLOCKED: Invalid status."
  exit 1
fi

# Validate new schema: each item has name, status, code, message_safe, duration_ms
if echo "$DATA" | jq -e 'all(.[]; has("name") and has("status") and has("code") and has("message_safe") and has("duration_ms"))' > /dev/null; then
  echo "Schema valid."
else
  echo "BLOCKED: Invalid schema."
  exit 1
fi

echo "Smoke complete."