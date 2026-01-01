#!/bin/bash
# Rollback F9.4.1 — Retorna ao baseline F9.4 PASS LOCAL

set -euo pipefail

echo "🔄 Iniciando rollback F9.4.1..."

# Verificação git status limpo
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ ERRO: Git status não está limpo. Commit ou stash mudanças primeiro."
    exit 1
fi

# Checkout para baseline
echo "📅 Voltando para checkpoint/F9_4_PASS_LOCAL_2026-01-01..."
git checkout checkpoint/F9_4_PASS_LOCAL_2026-01-01

# Re-run F9.4 para confirmar retorno
echo "🧪 Re-executando F9.4 scripts para confirmar rollback..."
export BASE_URL=https://localhost
./scripts/smoke_https.sh
./scripts/contract_obs.sh
./scripts/contract_sec.sh

echo "✅ Rollback F9.4.1 completo. Sistema em estado F9.4 PASS LOCAL."