#!/bin/bash
# F9.7 Step 2 — Deploy (após editar .env.prod)
set -euo pipefail

ts(){ date -u +%Y%m%d_%H%M%S; }
LOG="/opt/techno-os/artifacts/f9_7_deploy_$(ts).log"
log(){ echo "[$(date -Is)] $*" | tee -a "$LOG"; }
die(){ echo "[$(date -Is)] ABORT: $*" | tee -a "$LOG"; exit 1; }

rollback() {
  log "Executando rollback..."
  cd /opt/techno-os/app/backend
  docker compose -f docker-compose.yml -f docker-compose.prod.yml down || true
  exit 1
}

log "PHASE 1 — validar .env.prod"
cd /opt/techno-os/app/backend || die "Diretório backend não encontrado"

test -f /opt/techno-os/env/.env.prod || die ".env.prod não encontrado. Execute f9_7_step1_prepare.sh primeiro"

grep -q "CHANGE_ME" /opt/techno-os/env/.env.prod && die ".env.prod contém placeholders não preenchidos"
grep -q "POSTGRES_PASSWORD=" /opt/techno-os/env/.env.prod || die "POSTGRES_PASSWORD ausente"
grep -q "DATABASE_URL=" /opt/techno-os/env/.env.prod || die "DATABASE_URL ausente"
grep -q "VERITTA_BETA_API_KEY=" /opt/techno-os/env/.env.prod || die "VERITTA_BETA_API_KEY ausente"
log "✅ Secrets validados"

log "PHASE 2 — criar docker-compose.prod.yml override"
cat > docker-compose.prod.yml <<'YML'
services:
  api:
    command: ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
    env_file:
      - /opt/techno-os/env/.env.prod
    volumes: []
  postgres:
    env_file:
      - /opt/techno-os/env/.env.prod
    ports: []
YML

log "Checksums de configs:"
sha256sum docker-compose.prod.yml docker-compose.yml | tee -a "$LOG"

log "PHASE 3 — validar config final"
docker compose -f docker-compose.yml -f docker-compose.prod.yml config > /dev/null || die "Config inválida"
log "✅ Config validada"

log "PHASE 4 — subir stack"
trap rollback ERR
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build 2>&1 | tee -a "$LOG"
trap - ERR

log "Aguardando inicialização..."
sleep 8

log "PHASE 5 — verificar saúde"
docker compose ps | tee -a "$LOG"

log "Health check com retry..."
for i in {1..15}; do
  if docker exec techno-os-api curl -fsS http://localhost:8000/health 2>/dev/null | tee -a "$LOG"; then
    log "✅ Health check OK (tentativa $i)"
    log "✅ DEPLOY CONCLUÍDO. API rodando em http://localhost:8000"
    log "📋 Logs: docker compose logs -f"
    log "📄 Log completo: $LOG"
    exit 0
  fi
  log "Aguardando... ($i/15)"
  sleep 4
done

log "Health falhou. Coletando logs..."
docker logs --tail 300 techno-os-api 2>&1 | tee -a "$LOG"
die "Health check falhou após 15 tentativas"
