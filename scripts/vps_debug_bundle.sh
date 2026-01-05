#!/bin/bash
# VPS Debug Bundle Script
# Safe, no secrets, operator-controlled

set -euo pipefail

TS=$(date +%Y%m%d_%H%M%S)
BUNDLE_DIR="/tmp/techno-os-debug-bundle-${TS}"
mkdir -p "$BUNDLE_DIR"

echo "Creating debug bundle in $BUNDLE_DIR"

# Docker ps table
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" > "$BUNDLE_DIR/docker_ps.txt"

# Last 300 lines of api logs
docker logs --tail 300 techno-os-api > "$BUNDLE_DIR/api_logs_tail.txt" 2>&1 || echo "Failed to get logs" > "$BUNDLE_DIR/api_logs_tail.txt"

# Health endpoint
curl -s http://localhost:8000/health > "$BUNDLE_DIR/health.txt" || echo "Health check failed" > "$BUNDLE_DIR/health.txt"

# Compose config (redacted, no env)
docker-compose config | grep -v -E "(environment|env_file)" > "$BUNDLE_DIR/compose_config_redacted.yml" || echo "Compose config failed" > "$BUNDLE_DIR/compose_config_redacted.yml"

echo "Bundle created. To retrieve: scp -r deploy@<VPS_IP>:$BUNDLE_DIR ./local_bundle"

# Optional scp back (commented for safety)
# scp -r "$BUNDLE_DIR" ./local_bundle