#!/bin/bash
# F9.9-C: Backup automatizado de dados observabilidade
# 
# Gera backups compactados de volumes Docker:
# - postgres_data (database)
# - Futuro: prometheus_data, grafana_data (quando docker-compose incluir)
#
# Retenção: 7 dias
# Cron sugerido: 0 2 * * * /opt/techno-os/scripts/backup_observability.sh

set -e  # Fail-closed: abort on error

BACKUP_DIR="${BACKUP_DIR:-/opt/techno-os/backups/observability}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Criar diretório se não existir
mkdir -p "${BACKUP_DIR}"

echo "✅ Iniciando backup: ${TIMESTAMP}"

# Backup PostgreSQL data
echo "📦 Backup PostgreSQL..."
docker run --rm \
  -v techno-os-backend_postgres_data:/data:ro \
  -v "${BACKUP_DIR}":/backup \
  alpine:latest \
  tar czf /backup/postgres_${TIMESTAMP}.tar.gz -C /data .

echo "✅ PostgreSQL backup: postgres_${TIMESTAMP}.tar.gz"

# Futuro (F9.10+): Prometheus e Grafana
# Quando docker-compose incluir esses services:
# docker run --rm \
#   -v techno-os-backend_prometheus_data:/data:ro \
#   -v "${BACKUP_DIR}":/backup \
#   alpine:latest \
#   tar czf /backup/prometheus_${TIMESTAMP}.tar.gz -C /data .
#
# docker run --rm \
#   -v techno-os-backend_grafana_data:/data:ro \
#   -v "${BACKUP_DIR}":/backup \
#   alpine:latest \
#   tar czf /backup/grafana_${TIMESTAMP}.tar.gz -C /data .

# Retenção: remover backups > 7 dias
echo "🗑️ Aplicando retenção (7 dias)..."
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +7 -delete

# Atualizar symlinks latest
ln -sf postgres_${TIMESTAMP}.tar.gz "${BACKUP_DIR}/postgres_latest.tar.gz"
# ln -sf prometheus_${TIMESTAMP}.tar.gz "${BACKUP_DIR}/prometheus_latest.tar.gz"
# ln -sf grafana_${TIMESTAMP}.tar.gz "${BACKUP_DIR}/grafana_latest.tar.gz"

echo "✅ Backup concluído: ${TIMESTAMP}"
echo "📁 Diretório: ${BACKUP_DIR}"
ls -lh "${BACKUP_DIR}"/postgres_${TIMESTAMP}.tar.gz
