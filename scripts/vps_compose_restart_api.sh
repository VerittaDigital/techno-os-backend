#!/bin/bash
# VPS Compose Restart API Script
# Fail-closed, no pruning

set -euo pipefail

echo "Checking compose status..."
if ! docker-compose ps | grep -q "techno-os-api"; then
    echo "API service not running. Starting..."
    docker-compose up -d api
else
    echo "Restarting API service..."
    docker-compose restart api
fi

echo "Waiting for health..."
sleep 5
if curl -s http://localhost:8000/health | grep -q '"status":"ok"'; then
    echo "API restarted successfully."
else
    echo "API restart failed."
    exit 1
fi