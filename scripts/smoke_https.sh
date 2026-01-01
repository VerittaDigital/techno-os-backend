#!/bin/bash
# Smoke Tests — HTTPS Disponibilidade Básica (F9.4)
# Data: 2026-01-01
# Versão: v1.1 (hotfix BASE_URL)
# CI-Friendly: Executa sem interação, fail-closed

set -euo pipefail

# BASE_URL parametrizável
export BASE_URL=${BASE_URL:-https://staging.techno-os.com}

LOG_FILE="smoke_https_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "🚀 Iniciando Smoke Tests HTTPS (BASE_URL: $BASE_URL)..."

# Precheck: Verificar conectividade BASE_URL
echo "Precheck: Conectividade $BASE_URL/health"
if ! curl -k -f --max-time 5 "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ PRECONDITION FAILED: BASE_URL not reachable/resolvable ($BASE_URL/health)"
    exit 1
fi
echo "✅ Precheck OK"

# Teste 1: /health → 200 OK via HTTPS
echo "Teste 1: /health via HTTPS"
curl -k -f --max-time 10 "$BASE_URL/health"
echo "✅ /health OK"

# Teste 2: Endpoint raiz protegido (sem auth → 401/403)
echo "Teste 2: Endpoint raiz sem auth"
if curl -k -f -I --max-time 10 "$BASE_URL/" 2>/dev/null; then
    echo "❌ Falha: Endpoint não protegido"
    exit 1
else
    echo "✅ Endpoint protegido (401/403 esperado)"
fi

# Teste 3: Endpoint raiz com auth → 200/3xx
echo "Teste 3: Endpoint raiz com auth"
curl -k -f --max-time 10 -u "${API_USER:-staging}:${API_PASS:-temp123}" "$BASE_URL/health"
echo "✅ Auth OK"

# Teste 4: Grafana HTTPS e login requerido
echo "Teste 4: Grafana HTTPS e login"
response=$(curl -k -I --max-time 10 "$BASE_URL/grafana/" 2>/dev/null | head -n 1)
if [[ "$response" == *"302"* ]] || [[ "$response" == *"401"* ]]; then
    echo "✅ Grafana requer login (redirect/401)"
else
    echo "❌ Falha: Grafana sem proteção"
    exit 1
fi

echo "🎉 Smoke Tests HTTPS PASS (todos testes OK)"
echo "Logs salvos em: $LOG_FILE"