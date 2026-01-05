#!/bin/bash
# F11-SEALED-v1.0 VPS Deployment — Manual Execution Script
# Execute directly on VPS: bash f11_vps_manual.sh
# This script implements fail-closed deployment with complete evidence collection

set -e  # Exit on any error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date -u +"%Y-%m-%d %H:%M:%S UTC")]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Evidence directory
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
EVIDENCE_DIR="/tmp/f11-evidence-$TIMESTAMP"
mkdir -p "$EVIDENCE_DIR"
log "Evidence directory: $EVIDENCE_DIR"

# BLOCK 0: Environment verification
log "=== BLOCK 0: ENVIRONMENT VERIFICATION ==="
echo "Host: $(hostname)" | tee "$EVIDENCE_DIR/host_info.txt"
echo "Date: $(date)" | tee -a "$EVIDENCE_DIR/host_info.txt"
echo "User: $(whoami)" | tee -a "$EVIDENCE_DIR/host_info.txt"
echo "PWD: $(pwd)" | tee -a "$EVIDENCE_DIR/host_info.txt"

# BLOCK 1: Repository verification
log "=== BLOCK 1: REPOSITORY VERIFICATION ==="
cd /app/techno-os-backend || error "Repository path not found: /app/techno-os-backend"
log "Repository path: $(pwd)"
git rev-parse --is-inside-work-tree || error "Not a git repository"

# BLOCK 2: Fetch and checkout sealed tag
log "=== BLOCK 2: CHECKOUT F11-SEALED-v1.0 ==="
log "Current state before checkout:"
git log --oneline --decorate -3 | tee "$EVIDENCE_DIR/pre_checkout_log.txt"

log "Fetching tags..."
git fetch --all --tags

log "Checking out F11-SEALED-v1.0..."
git checkout -f F11-SEALED-v1.0 | tee "$EVIDENCE_DIR/checkout_output.txt"

log "Deployed tag:"
git describe --tags --always --dirty | tee "$EVIDENCE_DIR/deployed_tag.txt"

log "Deployed commit:"
git rev-parse HEAD | tee "$EVIDENCE_DIR/deployed_commit.txt"

log "Commit details:"
git log --oneline --decorate -1 | tee "$EVIDENCE_DIR/deployed_commit_detail.txt"

# BLOCK 3: Pre-deployment state capture
log "=== BLOCK 3: PRE-DEPLOYMENT STATE ==="
log "Capturing current container state..."
docker compose ps > "$EVIDENCE_DIR/compose_ps_before.txt" 2>&1 || warn "Failed to capture docker state"

log "Capturing current git state..."
git log --oneline --decorate -5 > "$EVIDENCE_DIR/git_log_deployed.txt"

# BLOCK 4: Controlled restart
log "=== BLOCK 4: SERVICE RESTART ==="
log "Stopping services..."
docker compose down | tee "$EVIDENCE_DIR/compose_down.log"

log "Building (no cache)..."
docker compose build --no-cache 2>&1 | tee "$EVIDENCE_DIR/compose_build.log"

log "Starting services..."
docker compose up -d | tee "$EVIDENCE_DIR/compose_up.log"

log "Waiting 10s for initialization..."
sleep 10

log "Post-restart container state:"
docker compose ps | tee "$EVIDENCE_DIR/compose_ps_after.txt"

# BLOCK 5: Health check (fail-closed)
log "=== BLOCK 5: HEALTH CHECK ==="
for i in {1..10}; do
    if curl -fsS http://localhost:8000/health > "$EVIDENCE_DIR/health_response.json" 2>&1; then
        log "✓ Health check passed (attempt $i)"
        cat "$EVIDENCE_DIR/health_response.json"
        break
    fi
    if [ $i -eq 10 ]; then
        error "Health check failed after 10 attempts"
    fi
    warn "Retry $i/10..."
    sleep 2
done

# BLOCK 6: Smoke test CP-11.3
log "=== BLOCK 6: SMOKE TEST CP-11.3 ==="
if [ ! -f smoke_test_cp11_3.sh ]; then
    warn "smoke_test_cp11_3.sh not found, creating minimal version..."
    cat > /tmp/smoke_cp11_3_minimal.sh <<'SMOKE'
#!/bin/bash
set -e
API_KEY="${VERITTA_BETA_API_KEY}"
API_BASE="http://localhost:8000"

echo "Test 1: Valid POST /process"
curl -fsS -X POST "$API_BASE/process" -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d '{"text":"smoke test"}' || exit 1
echo "✓"

echo "Test 2: POST /unknown-route (404)"
curl -sS -X POST "$API_BASE/unknown-route" -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d '{"test":"data"}' -w "%{http_code}" | grep -q 404 || exit 1
echo "✓"

echo "Test 3: GET /process (405)"
curl -sS -X GET "$API_BASE/process" -H "X-API-Key: $API_KEY" -w "%{http_code}" | grep -q 405 || exit 1
echo "✓"

echo "Test 4: Malformed JSON (422)"
curl -sS -X POST "$API_BASE/process" -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d '{"text":"unclosed' -w "%{http_code}" | grep -q 422 || exit 1
echo "✓"

echo "Test 5: GET /health"
curl -fsS "$API_BASE/health" || exit 1
echo "✓"

echo "✓ CP-11.3 APPROVED (minimal)"
SMOKE
    bash /tmp/smoke_cp11_3_minimal.sh 2>&1 | tee "$EVIDENCE_DIR/smoke_test_output.txt"
else
    log "Running smoke_test_cp11_3.sh..."
    export VERITTA_BETA_API_KEY="$(grep '^VERITTA_BETA_API_KEY=' .env 2>/dev/null | cut -d'=' -f2- || grep '^VERITTA_BETA_API_KEY=' /opt/techno-os/env/.env.prod 2>/dev/null | cut -d'=' -f2- || echo 'MISSING')"
    export API_BASE="http://localhost:8000"
    bash smoke_test_cp11_3.sh 2>&1 | tee "$EVIDENCE_DIR/smoke_test_output.txt"
fi

# BLOCK 7: Audit log analysis
log "=== BLOCK 7: AUDIT LOG ANALYSIS ==="

# Discover audit log path
AUDIT_PATH=$(grep '^VERITTA_AUDIT_LOG_PATH=' /opt/techno-os/env/.env.prod 2>/dev/null | cut -d'=' -f2- || \
             grep '^VERITTA_AUDIT_LOG_PATH=' .env 2>/dev/null | cut -d'=' -f2- || \
             echo "/app/techno-os-backend/audit.log")

log "Audit log path: $AUDIT_PATH"
echo "$AUDIT_PATH" > "$EVIDENCE_DIR/audit_path.txt"

if [ ! -f "$AUDIT_PATH" ]; then
    # Try alternative locations
    for alt in "./audit.log" "/app/logs/audit.log" "/var/log/techno-os/audit.log"; do
        if [ -f "$alt" ]; then
            AUDIT_PATH="$alt"
            log "Found audit log at: $AUDIT_PATH"
            break
        fi
    done
fi

if [ -f "$AUDIT_PATH" ]; then
    log "Capturing audit log tail (last 200 lines)..."
    tail -200 "$AUDIT_PATH" > "$EVIDENCE_DIR/audit_tail.jsonl"
    
    log "Analyzing audit log..."
    cat > /tmp/analyze_audit.py <<'PYANALYSIS'
import json, sys, re

if len(sys.argv) < 3:
    print("Usage: python3 analyze_audit.py <audit_log_path> <output_path>")
    sys.exit(1)

path = sys.argv[1]
out = sys.argv[2]

uuid_re = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")

g8 = g10 = allow = deny = uuid_ok = total = 0

with open(path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except:
            continue
        
        total += 1
        
        decision = obj.get("decision", "")
        if decision == "ALLOW":
            allow += 1
        elif decision == "DENY":
            deny += 1
        
        reason_codes = obj.get("reason_codes", [])
        if "G8_UNKNOWN_ACTION" in reason_codes:
            g8 += 1
        if "G10_BODY_PARSE_ERROR" in reason_codes:
            g10 += 1
        
        trace_id = obj.get("trace_id", "")
        if isinstance(trace_id, str) and uuid_re.match(trace_id):
            uuid_ok += 1

with open(out, "w") as w:
    w.write(f"TOTAL:{total}\n")
    w.write(f"ALLOW:{allow}\n")
    w.write(f"DENY:{deny}\n")
    w.write(f"G8:{g8}\n")
    w.write(f"G10:{g10}\n")
    w.write(f"UUID_TRACE_OK:{uuid_ok}\n")

print(open(out).read(), end='')
PYANALYSIS
    
    python3 /tmp/analyze_audit.py "$AUDIT_PATH" "$EVIDENCE_DIR/audit_analysis.txt"
    
    log "Audit analysis result:"
    cat "$EVIDENCE_DIR/audit_analysis.txt"
else
    error "Audit log not found at: $AUDIT_PATH"
fi

# BLOCK 8: Container logs
log "=== BLOCK 8: CONTAINER LOGS ==="
docker compose logs --no-color --tail 200 > "$EVIDENCE_DIR/compose_logs_tail.txt" 2>&1 || warn "Failed to capture container logs"

# BLOCK 9: Approval criteria
log "=== BLOCK 9: APPROVAL CRITERIA ==="

APPROVAL=true

# Parse audit analysis
if [ -f "$EVIDENCE_DIR/audit_analysis.txt" ]; then
    G8_COUNT=$(grep '^G8:' "$EVIDENCE_DIR/audit_analysis.txt" | cut -d: -f2)
    G10_COUNT=$(grep '^G10:' "$EVIDENCE_DIR/audit_analysis.txt" | cut -d: -f2)
    ALLOW_COUNT=$(grep '^ALLOW:' "$EVIDENCE_DIR/audit_analysis.txt" | cut -d: -f2)
    UUID_COUNT=$(grep '^UUID_TRACE_OK:' "$EVIDENCE_DIR/audit_analysis.txt" | cut -d: -f2)
    
    echo "Approval Criteria Check:" | tee "$EVIDENCE_DIR/approval_criteria.txt"
    echo "  G8 >= 2: $G8_COUNT" | tee -a "$EVIDENCE_DIR/approval_criteria.txt"
    echo "  G10 >= 1: $G10_COUNT" | tee -a "$EVIDENCE_DIR/approval_criteria.txt"
    echo "  ALLOW >= 1: $ALLOW_COUNT" | tee -a "$EVIDENCE_DIR/approval_criteria.txt"
    echo "  UUID >= 1: $UUID_COUNT" | tee -a "$EVIDENCE_DIR/approval_criteria.txt"
    
    [ "$G8_COUNT" -ge 2 ] || { warn "G8 count < 2"; APPROVAL=false; }
    [ "$G10_COUNT" -ge 1 ] || { warn "G10 count < 1"; APPROVAL=false; }
    [ "$ALLOW_COUNT" -ge 1 ] || { warn "ALLOW count < 1"; APPROVAL=false; }
    [ "$UUID_COUNT" -ge 1 ] || { warn "UUID count < 1"; APPROVAL=false; }
fi

# Check smoke test
if grep -q "CP-11.3 APPROVED" "$EVIDENCE_DIR/smoke_test_output.txt" 2>/dev/null; then
    echo "  Smoke Test: PASSED" | tee -a "$EVIDENCE_DIR/approval_criteria.txt"
else
    warn "Smoke test did not show APPROVED"
    APPROVAL=false
fi

# Final verdict
log "=== FINAL VERDICT ==="
if [ "$APPROVAL" = true ]; then
    echo "✅ CP-11.3 VPS APPROVED" | tee "$EVIDENCE_DIR/final_verdict.txt"
    log "All criteria met. Deployment successful."
else
    echo "❌ CP-11.3 VPS FAILED" | tee "$EVIDENCE_DIR/final_verdict.txt"
    error "Some criteria not met. Review evidence and consider rollback."
fi

# Package evidence
log "=== PACKAGING EVIDENCE ==="
cd /tmp
tar czf "f11-evidence-$TIMESTAMP.tar.gz" "$(basename $EVIDENCE_DIR)"
log "Evidence package: /tmp/f11-evidence-$TIMESTAMP.tar.gz"
log "Evidence directory: $EVIDENCE_DIR"

# Summary
log "=== DEPLOYMENT SUMMARY ==="
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "F11-SEALED-v1.0 VPS DEPLOYMENT COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$EVIDENCE_DIR/deployed_tag.txt"
cat "$EVIDENCE_DIR/deployed_commit.txt"
echo ""
cat "$EVIDENCE_DIR/audit_analysis.txt"
echo ""
cat "$EVIDENCE_DIR/final_verdict.txt"
echo ""
echo "Evidence: $EVIDENCE_DIR"
echo "Package: /tmp/f11-evidence-$TIMESTAMP.tar.gz"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
