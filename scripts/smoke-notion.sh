#!/bin/bash
# scripts/smoke-notion.sh
# Smoke test: health then notion endpoints

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="your-api-key-placeholder"

echo "Smoke: Health check"
curl -X GET "$BASE_URL/health"

echo -e "\nSmoke: Notion agents (expect blocked or success)"
RESPONSE=$(curl -s -X GET "$BASE_URL/v1/notion/agents" \
  -H "X-API-Key: $API_KEY" \
  -H "X-Request-ID: $(uuidgen)" \
  -H "X-Timestamp: $(date -Iseconds)" \
  -H "X-Client-Version: smoke-test")

echo "Status: $(echo $RESPONSE | jq -r '.status')"
echo "Trace ID: $(echo $RESPONSE | jq -r '.trace_id')"