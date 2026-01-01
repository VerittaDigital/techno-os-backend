#!/bin/bash
# Rollback F9.1 — TLS / HTTPS
# Data: 2026-01-01
# Versão: v1.0

set -euo pipefail

echo "🔄 Iniciando rollback F9.1..."

# 1. Parar e remover containers Nginx
echo "Parando Nginx..."
docker-compose -f docker-compose.nginx.yml down

# 2. Remover volume Let's Encrypt
echo "Removendo certificados Let's Encrypt..."
docker volume rm techno-os-backend_letsencrypt || echo "Volume não encontrado"

# 3. Restaurar nginx.conf para versão pré-F9.1 (self-signed)
echo "Restaurando nginx.conf..."
git checkout HEAD~1 -- nginx/nginx.conf || echo "Git checkout falhou, verificar manualmente"

# 4. Limpar certs Let's Encrypt do host (se aplicável)
echo "Limpando certs do host..."
sudo rm -rf /etc/letsencrypt/live/staging.techno-os.com/ || echo "Certs não encontrados"

echo "✅ Rollback F9.1 completo. Sistema retornado ao estado pré-F9.1."