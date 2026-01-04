#!/bin/bash
# VPS Deployment & Smoke Test — F11-SEALED-v1.0
# Purpose: Deploy F11 to VPS and collect evidence
# Usage: ssh root@srv1241381.hstgr.cloud 'bash -s' < vps_deploy_f11.sh

set -euo pipefail

EVIDENCE_DIR="/tmp/f11-evidence-$(date +%s)"
mkdir -p "$EVIDENCE_DIR"

log() {
    echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] $*" | tee -a "$EVIDENCE_DIR/deployment.log"
}

collect_evidence() {
    local desc="$1"
    local file="$2"
    log "Collecting: $desc"
    cat "$file" > "$EVIDENCE_DIR/$(basename $file)" 2>/dev/null || log "  ⚠ File not found: $file"
}

# PHASE 1: Pre-deployment state
log "=== PHASE 1: PRE-DEPLOYMENT STATE ==="
cd /app/techno-os-backend || { log "ERROR: /app/techno-os-backend not found"; exit 1; }

log "Current git state:"
git log --oneline --decorate -5 | tee -a "$EVIDENCE_DIR/pre_git_log.txt"
git status --short | tee -a "$EVIDENCE_DIR/pre_git_status.txt"

log "Current running services:"
docker compose ps | tee -a "$EVIDENCE_DIR/pre_docker_ps.txt"

# PHASE 2: Fetch and checkout F11-SEALED-v1.0
log "=== PHASE 2: DEPLOYING F11-SEALED-v1.0 ==="
log "Fetching tags from origin..."
git fetch --tags --force

log "Checking out tag F11-SEALED-v1.0..."
git checkout F11-SEALED-v1.0 | tee -a "$EVIDENCE_DIR/checkout.log"

log "Post-checkout git state:"
git log --oneline --decorate -3 | tee -a "$EVIDENCE_DIR/post_git_log.txt"
git show --no-patch --format=fuller F11-SEALED-v1.0 | tee -a "$EVIDENCE_DIR/tag_info.txt"

# PHASE 3: Rebuild and restart
log "=== PHASE 3: SERVICE RESTART ==="
log "Stopping services..."
docker compose down | tee -a "$EVIDENCE_DIR/docker_down.log"

log "Rebuilding containers..."
docker compose build | tee -a "$EVIDENCE_DIR/docker_build.log"

log "Starting services..."
docker compose up -d | tee -a "$EVIDENCE_DIR/docker_up.log"

log "Waiting 10s for service initialization..."
sleep 10

log "Post-restart service status:"
docker compose ps | tee -a "$EVIDENCE_DIR/post_docker_ps.txt"

# PHASE 4: Health check
log "=== PHASE 4: HEALTH CHECK ==="
for i in {1..10}; do
    if curl -fsS http://localhost:8000/health > /dev/null 2>&1; then
        log "✓ Health check passed (attempt $i)"
        break
    fi
    log "  Retry $i/10..."
    sleep 2
done

curl -fsS http://localhost:8000/health | tee "$EVIDENCE_DIR/health_response.json" || {
    log "ERROR: Health check failed after 10 attempts"
    exit 1
}

# PHASE 5: Smoke tests
log "=== PHASE 5: SMOKE TESTS ==="

# Export environment for smoke test
export VERITTA_BETA_API_KEY="$(grep VERITTA_BETA_API_KEY .env | cut -d'=' -f2-)"
export API_BASE="http://localhost:8000"
export AUDIT_LOG_PATH="/app/logs/audit.log"

if [ -f smoke_test_cp11_3.sh ]; then
    log "Executing smoke_test_cp11_3.sh..."
    bash smoke_test_cp11_3.sh 2>&1 | tee "$EVIDENCE_DIR/smoke_test_output.txt"
else
    log "⚠ smoke_test_cp11_3.sh not found, skipping"
fi

# PHASE 6: Evidence collection
log "=== PHASE 6: EVIDENCE COLLECTION ==="

collect_evidence "Uvicorn logs (last 100 lines)" "/app/logs/api.log"
collect_evidence "Audit log (last 50 lines)" "/app/logs/audit.log"

# Audit log analysis
if [ -f /app/logs/audit.log ]; then
    log "Audit log analysis:"
    echo "Total entries: $(wc -l < /app/logs/audit.log)" | tee -a "$EVIDENCE_DIR/audit_analysis.txt"
    echo "G8_UNKNOWN_ACTION: $(grep -c 'G8_UNKNOWN_ACTION' /app/logs/audit.log || echo 0)" | tee -a "$EVIDENCE_DIR/audit_analysis.txt"
    echo "G10_BODY_PARSE_ERROR: $(grep -c 'G10_BODY_PARSE_ERROR' /app/logs/audit.log || echo 0)" | tee -a "$EVIDENCE_DIR/audit_analysis.txt"
    echo "ALLOW decisions: $(grep -c '"decision":"ALLOW"' /app/logs/audit.log || echo 0)" | tee -a "$EVIDENCE_DIR/audit_analysis.txt"
    
    log "Audit log sample (last 10 entries):"
    tail -10 /app/logs/audit.log | tee "$EVIDENCE_DIR/audit_sample.jsonl"
fi

# PHASE 7: Final verification
log "=== PHASE 7: FINAL VERIFICATION ==="
log "Git commit deployed:"
git log --oneline --decorate -1 | tee -a "$EVIDENCE_DIR/deployed_commit.txt"

log "Docker image info:"
docker compose images | tee -a "$EVIDENCE_DIR/docker_images.txt"

log "Container uptime:"
docker compose ps --format "table {{.Service}}\t{{.Status}}" | tee -a "$EVIDENCE_DIR/container_status.txt"

# PHASE 8: Package evidence
log "=== PHASE 8: PACKAGING EVIDENCE ==="
cd /tmp
tar czf "f11-evidence-$(date +%Y%m%d-%H%M%S).tar.gz" "$(basename $EVIDENCE_DIR)"
log "Evidence packaged: $(ls -lh f11-evidence-*.tar.gz | tail -1)"

log "=== DEPLOYMENT COMPLETE ==="
log "Evidence directory: $EVIDENCE_DIR"
log "Next step: Review evidence and approve CP-11.3"

# Print summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "F11 DEPLOYMENT SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$EVIDENCE_DIR/deployed_commit.txt"
echo ""
cat "$EVIDENCE_DIR/audit_analysis.txt"
echo ""
echo "Evidence: $EVIDENCE_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
