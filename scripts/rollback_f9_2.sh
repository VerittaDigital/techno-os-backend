#!/bin/bash
# Rollback F9.2 — Auth & Access Control
# Data: 2026-01-01
# Versão: v1.0

set -euo pipefail

echo "🔄 Iniciando rollback F9.2..."

# 1. Parar containers
echo "Parando Nginx e Grafana..."
docker-compose -f docker-compose.nginx.yml down
docker-compose -f docker-compose.grafana.yml down

# 2. Restaurar configs
echo "Restaurando nginx.conf..."
git checkout HEAD~1 -- nginx/nginx.conf || echo "Git checkout falhou, verificar manualmente"

echo "Restaurando docker-compose.grafana.yml..."
git checkout HEAD~1 -- docker-compose.grafana.yml || echo "Git checkout falhou, verificar manualmente"

# 3. Remover .htpasswd
echo "Removendo .htpasswd..."
rm -f nginx/.htpasswd

# 4. Restart stack
echo "Reiniciando stack..."
docker-compose -f docker-compose.grafana.yml up -d
docker-compose -f docker-compose.nginx.yml up -d

echo "✅ Rollback F9.2 completo. Sistema retornado ao estado pré-F9.2."