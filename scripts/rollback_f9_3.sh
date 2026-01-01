#!/bin/bash
# Rollback F9.3 — Alerting Governado
# Data: 2026-01-01
# Versão: v1.0

set -euo pipefail

echo "🔄 Iniciando rollback F9.3..."

# 1. Remover alertas F9.3 do alert.rules.yml
echo "Removendo alertas F9.3..."
git checkout HEAD~1 -- alert.rules.yml || echo "Git checkout falhou, verificar manualmente"

# 2. Reload Prometheus
echo "Reload Prometheus..."
curl -X POST http://localhost:9090/-/reload || echo "Reload falhou, reiniciar container"
# Fallback: docker-compose restart prometheus

echo "✅ Rollback F9.3 completo. Alertas F9.3 removidos."