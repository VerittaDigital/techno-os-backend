#!/bin/bash
# F9.7 v3.4 — PRODUÇÃO CONTROLADA (correção do compose DEV -> PROD)
# Corrigido conforme parecer técnico 2026-01-03

set -euo pipefail

ts(){ date -u +%Y%m%d_%H%M%S; }
LOG="/tmp/f9_7_init_$(ts).log"  # temp log until artifacts dir created
log(){ echo "[$(date -Is)] $*" | tee -a "$LOG"; }
die(){ echo "[$(date -Is)] ABORT: $*" | tee -a "$LOG"; exit 1; }

# Rollback function
rollback() {
  log "Executando rollback..."
  docker compose -f docker-compose.yml -f docker-compose.prod.yml down || true
  log "Rollback completo. Verifique logs em $LOG"
  exit 1
}

log "PHASE A — sanity checks"

# CORREÇÃO 1: Criar artifacts dir antes de usar LOG
mkdir -p /opt/techno-os/artifacts
LOG="/opt/techno-os/artifacts/f9_7_prodfix_$(ts).log"

cd /opt/techno-os/app/backend
test -f docker-compose.yml || die "docker-compose.yml não encontrado"

# CORREÇÃO 2: Validar Docker disponível
log "Validando Docker e Compose..."
command -v docker >/dev/null || die "Docker não instalado"
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 não disponível"
log "Docker OK: $(docker --version)"
log "Compose OK: $(docker compose version --short 2>/dev/null || echo 'v2')"

# CORREÇÃO 3: Backup antes de deploy
log "PHASE A.5 — backup estado anterior"
if docker compose ps 2>/dev/null | grep -q "techno-os-api"; then
  log "Containers existentes detectados. Criando backup..."
  docker compose -f docker-compose.yml logs > "/opt/techno-os/artifacts/backup_logs_$(ts).txt" || true
  log "Parando containers existentes..."
  docker compose -f docker-compose.yml down || log "WARN: down falhou, continuando..."
fi

log "PHASE B — criar .env.prod (NO VPS, sem expor no chat)"
mkdir -p /opt/techno-os/env

if [ ! -f /opt/techno-os/env/.env.prod ]; then
  touch /opt/techno-os/env/.env.prod
  chmod 600 /opt/techno-os/env/.env.prod
  
  log "Criando template .env.prod..."
  cat > /opt/techno-os/env/.env.prod <<'EOF'
ENV=production
DEBUG=false
LOG_LEVEL=info

# escolha uma senha forte
POSTGRES_DB=techno_os
POSTGRES_USER=techno_user
POSTGRES_PASSWORD=__COLOQUE_SENHA_FORTE__

# usando service name 'postgres' da rede docker
DATABASE_URL=postgresql://techno_user:__MESMA_SENHA__@postgres:5432/techno_os
EOF
  
  log "Abra e preencha agora: nano /opt/techno-os/env/.env.prod"
  read -r -p "Quando terminar de editar o .env.prod no nano, digite GO: " GO
  [ "${GO:-}" = "GO" ] || die "Sem GO humano"
else
  log ".env.prod já existe, reutilizando..."
  read -r -p "Confirme uso do .env.prod existente (GO para continuar): " GO
  [ "${GO:-}" = "GO" ] || die "Sem GO humano"
fi

# CORREÇÃO 4: Validar .env.prod preenchido
log "PHASE B.5 — validar secrets preenchidos"
grep -q "__COLOQUE_SENHA_FORTE__" /opt/techno-os/env/.env.prod && die ".env.prod contém placeholders não preenchidos"
grep -q "POSTGRES_PASSWORD=" /opt/techno-os/env/.env.prod || die "POSTGRES_PASSWORD ausente em .env.prod"
grep -q "DATABASE_URL=" /opt/techno-os/env/.env.prod || die "DATABASE_URL ausente em .env.prod"
log "Secrets validados OK"

log "PHASE C — criar override de produção (docker-compose.prod.yml)"
cat > docker-compose.prod.yml <<'YML'
services:
  api:
    # modo PROD: sem reload, sem bind mounts, config via env_file
    command: ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
    env_file:
      - /opt/techno-os/env/.env.prod
    volumes: []   # remove bind mounts DEV
  postgres:
    # usa env_file e não expõe 5432 pra fora
    env_file:
      - /opt/techno-os/env/.env.prod
    ports: []     # remove published 5432 (fica só na rede docker)
YML

# Auditoria de configs
log "Gerando checksums de configs..."
sha256sum docker-compose.prod.yml | tee -a "$LOG"
sha256sum docker-compose.yml | tee -a "$LOG"
sha256sum /opt/techno-os/env/.env.prod | tee -a "$LOG"

log "PHASE D — validar config final"
docker compose -f docker-compose.yml -f docker-compose.prod.yml config | head -n 120 | tee -a "$LOG"

log "PHASE E — subir stack (prod override)"
trap rollback ERR  # auto-rollback em falha
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build 2>&1 | tee -a "$LOG"
trap - ERR  # desabilita trap após sucesso

log "Aguardando inicialização dos containers..."
sleep 5

log "PHASE F — verificar saúde"
docker compose ps | tee -a "$LOG"

log "Logs recentes dos containers:"
docker compose logs --tail 100 | tee -a "$LOG"

# CORREÇÃO 5: Health check com retry
log "Testando health interno do container api (com retry)..."
for i in {1..10}; do
  if docker exec techno-os-api curl -fsS http://localhost:8000/health 2>/dev/null | tee -a "$LOG"; then
    log "✅ Health check OK (tentativa $i)"
    break
  fi
  if [ "$i" -eq 10 ]; then
    log "Logs finais da API:"
    docker logs --tail 200 techno-os-api | tee -a "$LOG"
    die "Health check falhou após 10 tentativas"
  fi
  log "Aguardando startup... (tentativa $i/10)"
  sleep 3
done

log "✅ OK: API saudável em 8000 (interno). Próximo: Nginx reverse proxy + TLS."
log "📋 Log completo disponível em: $LOG"
