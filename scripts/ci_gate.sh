#!/bin/bash
# F9.5 CI READINESS GATE - TECHNO OS BACKEND
# Idempotent CI Gate Script - Fail-Closed Execution
# BASE_URL parametrizable for staging/production
# Logs all steps for auditability

set -euo pipefail

# Default BASE_URL (localhost staging)
BASE_URL="${BASE_URL:-https://localhost}"

# Artifacts directory (configurable)
ARTIFACTS_DIR="${ARTIFACTS_DIR:-artifacts/f9_5}"

# Healthcheck flags
REQUIRE_HEALTHCHECK="${REQUIRE_HEALTHCHECK:-1}"
CURL_INSECURE="${CURL_INSECURE:-1}"
HEALTHCHECK_TIMEOUT="${HEALTHCHECK_TIMEOUT:-10}"

# Timestamp for logs
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$ARTIFACTS_DIR/ci_gate_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date +%Y-%m-%d\ %H:%M:%S) - $*" | tee -a "$LOG_FILE"
}

# Error function (fail-closed)
error() {
    echo -e "${RED}❌ ERROR: $*${NC}" | tee -a "$LOG_FILE"
    echo "Logs salvos em: $LOG_FILE"
    exit 1
}

# Success function
success() {
    echo -e "${GREEN}✅ $*${NC}" | tee -a "$LOG_FILE"
}

# Warning function
warning() {
    echo -e "${YELLOW}⚠️  WARNING: $*${NC}" | tee -a "$LOG_FILE"
}

# Precheck function
precheck() {
    if [ "$REQUIRE_HEALTHCHECK" -eq 0 ]; then
        warning "Healthcheck desabilitado (REQUIRE_HEALTHCHECK=0)"
        return 0
    fi

    log "🔍 Precheck: Conectividade $BASE_URL/health (timeout: ${HEALTHCHECK_TIMEOUT}s)"
    CURL_OPTS="-s --max-time $HEALTHCHECK_TIMEOUT"
    if [ "$CURL_INSECURE" -eq 1 ]; then
        CURL_OPTS="$CURL_OPTS -k"
    fi
    if ! curl $CURL_OPTS "$BASE_URL/health" > /dev/null; then
        error "Precheck falhou - serviço não acessível em $BASE_URL"
    fi
    success "Precheck OK"
}

# Pytest execution
run_pytest() {
    log "🧪 Executando pytest..."
    if ! python -m pytest -q 2>&1 | tee -a "$LOG_FILE"; then
        error "Pytest falhou"
    fi
    success "Pytest OK"
}

# Flake8 execution (critical only)
run_flake8() {
    log "🔍 Executando flake8 (críticos)..."
    if ! flake8 app tests --select=E9,F63,F7,F82 2>&1 | tee -a "$LOG_FILE"; then
        error "Flake8 falhou"
    fi
    success "Flake8 OK"
}

# Mypy execution (baseline check)
run_mypy() {
    log "🔍 Executando mypy (baseline check)..."
    # Count errors - must not exceed baseline
    OUTPUT=$(mypy app --ignore-missing-imports --no-implicit-optional 2>&1 || true)
    echo "$OUTPUT" > "$ARTIFACTS_DIR/mypy_full_${TIMESTAMP}.txt"
    ERROR_COUNT=$(echo "$OUTPUT" | grep -c "error:" || true)
    BASELINE=73
    if [ "$ERROR_COUNT" -gt "$BASELINE" ]; then
        echo "$OUTPUT" | tee -a "$LOG_FILE"
        error "Mypy falhou - $ERROR_COUNT erros (baseline: $BASELINE)"
    fi
    success "Mypy OK ($ERROR_COUNT erros, baseline: $BASELINE)"
}

# Smoke HTTPS test
run_smoke() {
    log "🚀 Executando smoke HTTPS..."
    if ! bash scripts/smoke_https.sh 2>&1 | tee -a "$LOG_FILE"; then
        error "Smoke HTTPS falhou"
    fi
    success "Smoke HTTPS OK"
}

# Contract Observabilidade
run_contract_obs() {
    log "🔍 Executando contract observabilidade..."
    if ! bash scripts/contract_obs.sh 2>&1 | tee -a "$LOG_FILE"; then
        error "Contract Observabilidade falhou"
    fi
    success "Contract Observabilidade OK"
}

# Contract Segurança
run_contract_sec() {
    log "🔒 Executando contract segurança..."
    if ! bash scripts/contract_sec.sh 2>&1 | tee -a "$LOG_FILE"; then
        error "Contract Segurança falhou"
    fi
    success "Contract Segurança OK"
}

# Main execution
main() {
    # Ensure artifacts directory exists
    mkdir -p "$ARTIFACTS_DIR"

    log "🚀 Iniciando CI Gate F9.5 - TECHNO OS BACKEND"
    log "BASE_URL: $BASE_URL"
    log "ARTIFACTS_DIR: $ARTIFACTS_DIR"
    log "REQUIRE_HEALTHCHECK: $REQUIRE_HEALTHCHECK"
    log "CURL_INSECURE: $CURL_INSECURE"
    log "Timestamp: $TIMESTAMP"
    log "Log file: $LOG_FILE"

    # Precheck
    precheck

    # Core tests
    run_pytest
    run_flake8
    run_mypy

    # Integration tests
    run_smoke
    run_contract_obs
    run_contract_sec

    # Success
    log "🎉 CI GATE F9.5 PASS - TODOS TESTES OK"
    log "Logs salvos em: $LOG_FILE"
    echo -e "${GREEN}🎉 CI GATE F9.5 PASS${NC}"
}

# Execute main
main "$@"