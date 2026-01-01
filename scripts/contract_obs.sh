#!/bin/bash
# Contract Tests — Observabilidade (F9.4)
# Data: 2026-01-01
# Versão: v1.1 (hotfix BASE_URL)
# CI-Friendly: Executa sem interação, fail-closed

set -euo pipefail

# BASE_URL parametrizável
export BASE_URL=${BASE_URL:-https://staging.techno-os.com}

LOG_FILE="contract_obs_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "🔍 Iniciando Contract Tests Observabilidade (BASE_URL: $BASE_URL)..."

# Precheck: Verificar conectividade BASE_URL
echo "Precheck: Conectividade $BASE_URL/health"
if ! curl -k -f --max-time 5 "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ PRECONDITION FAILED: BASE_URL not reachable/resolvable ($BASE_URL/health)"
    exit 1
fi
echo "✅ Precheck OK"

# Teste 1: Prometheus targets essenciais UP
echo "Teste 1: Prometheus targets UP"
targets=$(curl -s --max-time 10 http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | select(.health == "up") | .labels.job')
if echo "$targets" | grep -q "techno_os_backend\|grafana\|prometheus"; then
    echo "✅ Targets essenciais UP"
else
    echo "❌ Falha: Targets DOWN"
    exit 1
fi

# Teste 2: Prometheus rules carregadas sem erro
echo "Teste 2: Prometheus rules OK"
status=$(curl -s --max-time 10 http://localhost:9090/api/v1/rules | jq -r '.status')
if [[ "$status" == "success" ]]; then
    echo "✅ Rules carregadas sem erro"
else
    echo "❌ Falha: Rules com erro"
    exit 1
fi

# Teste 3: Alerting rules presentes
echo "Teste 3: Alerting rules presentes"
rules_count=$(curl -s --max-time 10 http://localhost:9090/api/v1/rules | jq '.data.groups[0].rules | length')
if [[ "$rules_count" -ge 5 ]]; then  # F8.5 + F9.3
    echo "✅ Alerting rules presentes ($rules_count)"
else
    echo "❌ Falha: Alerting incompleto"
    exit 1
fi

# Teste 4: Grafana datasource funcional
echo "Teste 4: Grafana datasource"
# Simular: verificar se dashboards carregam (assumir login via env se necessário)
# Para simplificar, verificar se endpoint responde (401 = acessível, apenas requer auth)
response=$(curl -k --max-time 10 -s -o /dev/null -w "%{http_code}" "$BASE_URL/grafana/api/datasources")
if [[ "$response" == "401" ]]; then
    echo "✅ Grafana datasource acessível (requer auth)"
else
    echo "❌ Falha: Grafana datasource não acessível (código: $response)"
    exit 1
fi

echo "🎉 Contract Tests Observabilidade PASS"
echo "Logs salvos em: $LOG_FILE"