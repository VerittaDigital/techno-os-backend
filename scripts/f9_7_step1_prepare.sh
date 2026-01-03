#!/bin/bash
# F9.7 Step 1 — Preparar ambiente (não interativo)
set -euo pipefail

ts(){ date -u +%Y%m%d_%H%M%S; }
LOG="/tmp/f9_7_prep_$(ts).log"
log(){ echo "[$(date -Is)] $*" | tee -a "$LOG"; }
die(){ echo "[$(date -Is)] ABORT: $*" | tee -a "$LOG"; exit 1; }

log "PHASE A — sanity checks"
mkdir -p /opt/techno-os/artifacts
LOG="/opt/techno-os/artifacts/f9_7_prep_$(ts).log"

cd /opt/techno-os/app/backend || die "Diretório backend não encontrado"
test -f docker-compose.yml || die "docker-compose.yml não encontrado"

log "Validando Docker e Compose..."
command -v docker >/dev/null || die "Docker não instalado"
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 não disponível"
log "Docker OK: $(docker --version)"
log "Compose OK: $(docker compose version --short 2>/dev/null || echo 'v2')"

log "PHASE A.5 — backup estado anterior"
if docker compose ps 2>/dev/null | grep -q "techno-os"; then
  log "Containers existentes detectados. Criando backup..."
  docker compose -f docker-compose.yml logs > "/opt/techno-os/artifacts/backup_logs_$(ts).txt" || true
  log "Parando containers existentes..."
  docker compose -f docker-compose.yml down || log "WARN: down falhou"
fi

log "PHASE B — criar template .env.prod"
mkdir -p /opt/techno-os/env

if [ -f /opt/techno-os/env/.env.prod ]; then
  log "✅ .env.prod já existe"
  exit 0
fi

cat > /opt/techno-os/env/.env.prod <<'EOF'
ENV=production
DEBUG=false
LOG_LEVEL=info

POSTGRES_DB=techno_os
POSTGRES_USER=techno_user
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD

DATABASE_URL=postgresql://techno_user:CHANGE_ME_STRONG_PASSWORD@postgres:5432/techno_os

VERITTA_HOST=0.0.0.0
VERITTA_PORT=8000
VERITTA_BETA_API_KEY=CHANGE_ME_64_CHAR_KEY
VERITTA_PROFILES_FINGERPRINT=f92d5263e1dbe67375a7ade4210877d4f38a2bcf5b3f312039b60904e25e2299
VERITTA_ADMIN_API_KEY=CHANGE_ME_64_CHAR_KEY
VERITTA_AUDIT_LOG_PATH=/var/log/veritta/audit.log
EOF

chmod 600 /opt/techno-os/env/.env.prod
log "✅ Template criado em /opt/techno-os/env/.env.prod"
log "📝 EDITE O ARQUIVO com nano e depois execute f9_7_step2_deploy.sh"
