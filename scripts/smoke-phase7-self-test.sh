#!/bin/bash

# Smoke test for Phase 7 Self-Test

echo "Testing gateway health..."
HEALTH_RESP=$(curl -s -H "X-Request-ID: $(uuidgen)" -H "X-Timestamp: $(date -Iseconds)" -H "X-Client-Version: backend-phase7-self-test" http://localhost:8000/health)
echo "Health: $HEALTH_RESP"

echo -e "\nTesting Notion self-test..."
SELF_RESP=$(curl -s -H "X-API-Key: test-key" -H "X-Request-ID: $(uuidgen)" -H "X-Timestamp: $(date -Iseconds)" -H "X-Client-Version: backend-phase7-self-test" http://localhost:8000/v1/notion/self_test)

STATUS=$(echo "$SELF_RESP" | jq -r '.status')
TRACE_ID=$(echo "$SELF_RESP" | jq -r '.trace_id')

echo "Status: $STATUS"
echo "Trace ID (sanitized): $(echo "$TRACE_ID" | sed 's/\(token\|apikey\|signature\|secret\|password\|pwd\)=[^&]*/\1=***/g' | sed 's/\(\w\+\):\([^@]\+\)@/\1:***@/g')"

if [[ "$STATUS" == "success" || "$STATUS" == "blocked" ]]; then
  echo "Envelope valid."
else
  echo "BLOCKED: Invalid status."
  exit 1
fi

echo "Smoke complete."