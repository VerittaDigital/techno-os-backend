#!/usr/bin/env bash
# F9.10: Backup automatizado completo (PostgreSQL + Prometheus + Grafana)
# Base: F9.9-C (apenas postgres) → F9.10 (3 volumes)
# Governança: fail-closed (set -e), retention 7 dias

set -euo pipefail

BACKUP_DIR="/opt/techno-os/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "${BACKUP_DIR}"

echo "=== F9.10 BACKUP OBSERVABILITY (3 volumes) ==="
echo "Timestamp: ${TIMESTAMP}"

# 1. PostgreSQL (dados estruturados)
echo "Backing up postgres_data..."
docker run --rm \
  -v techno-os-backend_postgres_data:/data:ro \
  -v "${BACKUP_DIR}":/backup \
  alpine:3.20 \
  tar czf /backup/postgres_${TIMESTAMP}.tar.gz -C /data .

ln -sf postgres_${TIMESTAMP}.tar.gz "${BACKUP_DIR}/postgres_latest.tar.gz"
echo "✅ PostgreSQL backup: postgres_${TIMESTAMP}.tar.gz"

# 2. Prometheus (métricas históricas)
echo "Backing up prometheus_data..."
docker run --rm \
  -v techno-os-backend_prometheus_data:/data:ro \
  -v "${BACKUP_DIR}":/backup \
  alpine:3.20 \
  tar czf /backup/prometheus_${TIMESTAMP}.tar.gz -C /data .

ln -sf prometheus_${TIMESTAMP}.tar.gz "${BACKUP_DIR}/prometheus_latest.tar.gz"
echo "✅ Prometheus backup: prometheus_${TIMESTAMP}.tar.gz"

# 3. Grafana (dashboards + datasources)
echo "Backing up grafana_data..."
docker run --rm \
  -v techno-os-backend_grafana_data:/data:ro \
  -v "${BACKUP_DIR}":/backup \
  alpine:3.20 \
  tar czf /backup/grafana_${TIMESTAMP}.tar.gz -C /data .

ln -sf grafana_${TIMESTAMP}.tar.gz "${BACKUP_DIR}/grafana_latest.tar.gz"
echo "✅ Grafana backup: grafana_${TIMESTAMP}.tar.gz"

# Retention: 7 dias
echo "Applying 7-day retention policy..."
find "${BACKUP_DIR}" -name "postgres_*.tar.gz" -mtime +7 -delete
find "${BACKUP_DIR}" -name "prometheus_*.tar.gz" -mtime +7 -delete
find "${BACKUP_DIR}" -name "grafana_*.tar.gz" -mtime +7 -delete

echo "=== BACKUP COMPLETO (3 volumes) ==="
ls -lh "${BACKUP_DIR}"/*_latest.tar.gz 2>/dev/null || echo "No backups yet (first run)"
