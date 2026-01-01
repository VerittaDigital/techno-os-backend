#!/bin/bash
# F9.5 OPTIONAL: Security Scan with Bandit
# Requires: pip install bandit

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="bandit_${TIMESTAMP}.log"

log() {
    echo "$(date +%Y-%m-%d\ %H:%M:%S) - $*" | tee -a "$LOG_FILE"
}

error() {
    echo "❌ ERROR: $*" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo "✅ $*" | tee -a "$LOG_FILE"
}

# Check if bandit is installed
if ! command -v bandit >/dev/null 2>&1; then
    error "bandit não instalado. Instale com: pip install bandit"
fi

log "🔒 Executando security scan com bandit..."
bandit -r app -f json -o bandit_report.json | tee -a "$LOG_FILE"

success "Bandit scan completo (report: bandit_report.json)"
log "Logs salvos em: $LOG_FILE"