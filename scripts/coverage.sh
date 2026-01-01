#!/bin/bash
# F9.5 OPTIONAL: Coverage Report
# Requires: pip install pytest-cov

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="coverage_${TIMESTAMP}.log"

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

# Check if pytest-cov is installed
if ! python -c "import pytest_cov" 2>/dev/null; then
    error "pytest-cov não instalado. Instale com: pip install pytest-cov"
fi

log "📊 Executando coverage report..."
python -m pytest --cov=app --cov-report=html --cov-report=term | tee -a "$LOG_FILE"

success "Coverage report gerado (HTML: htmlcov/index.html)"
log "Logs salvos em: $LOG_FILE"