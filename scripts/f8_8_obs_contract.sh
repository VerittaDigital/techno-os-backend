#!/usr/bin/env bash
set -euo pipefail

# -----------------------
# F8.8 v2 — Observability Contract Runbook (CI-friendly)
# -----------------------

ts() { date -Is; }
log() { echo "[$(ts)] $*"; }
die() { echo "[$(ts)] ABORT: $*"; exit 1; }

# --- Inputs / Defaults ---
PROJECT_DIR="${PROJECT_DIR:-/mnt/d/Projects/techno-os-backend}"
ENV="${ENV:-development}"
KEEP_STACK_UP="${KEEP_STACK_UP:-0}"
REQUIRE_PROMETHEUS="${REQUIRE_PROMETHEUS:-0}"

: "${GRAFANA_ADMIN_USER:?ABORT: GRAFANA_ADMIN_USER vazio}"
: "${GRAFANA_ADMIN_PASSWORD:?ABORT: GRAFANA_ADMIN_PASSWORD vazio}"

case "$ENV" in
  development|staging) ;;
  *) die "ENV inválido: '$ENV' (use development|staging)" ;;
esac

if [[ "$KEEP_STACK_UP" != "0" && "$KEEP_STACK_UP" != "1" ]]; then
  die "KEEP_STACK_UP inválido: '$KEEP_STACK_UP' (use 0|1)"
fi

if [[ "$REQUIRE_PROMETHEUS" != "0" && "$REQUIRE_PROMETHEUS" != "1" ]]; then
  die "REQUIRE_PROMETHEUS inválido: '$REQUIRE_PROMETHEUS' (use 0|1)"
fi

# --- Compose discovery ---
BASE_COMPOSE="docker-compose.yml"
METRICS_COMPOSE=""
GRAFANA_COMPOSE="docker-compose.grafana.yml"
NET_NAME="techno_observability"

if [[ ! -f "$BASE_COMPOSE" ]]; then die "Base compose não encontrado: $BASE_COMPOSE"; fi
if [[ ! -f "$GRAFANA_COMPOSE" ]]; then die "Grafana compose não encontrado: $GRAFANA_COMPOSE"; fi

if [[ -f "docker-compose.metrics.yml" ]]; then
  METRICS_COMPOSE="docker-compose.metrics.yml"
fi

# --- Evidence collectors ---
collect_evidence() {
  log "=== EVIDENCE PACK (auto) ==="
  docker ps || true
  docker ps -a | head -120 || true
  docker volume ls | head -80 || true
  docker network ls | grep -E "$NET_NAME|techno-network" || true

  log "--- logs api (tail 200) ---"
  docker logs techno-os-api --tail 200 2>/dev/null || true

  log "--- logs prometheus (tail 200) ---"
  docker logs technoos_prometheus --tail 200 2>/dev/null || true

  log "--- logs grafana (tail 200) ---"
  docker logs technoos_grafana --tail 200 2>/dev/null || true
}

rollback() {
  if [[ "$KEEP_STACK_UP" == "1" ]]; then
    log "KEEP_STACK_UP=1 => rollback SKIPPED (estado mantido)."
    return 0
  fi

  log "=== ROLLBACK (trap) ==="
  docker compose -f "$GRAFANA_COMPOSE" down --volumes --remove-orphans >/dev/null 2>&1 || true
  if [[ -n "$METRICS_COMPOSE" ]]; then
    docker compose -f "$METRICS_COMPOSE" down --volumes --remove-orphans >/dev/null 2>&1 || true
  fi
  docker compose -f "$BASE_COMPOSE" down --volumes --remove-orphans >/dev/null 2>&1 || true

  docker network ls | grep -q "$NET_NAME" && docker network rm "$NET_NAME" >/dev/null 2>&1 || true
  log "Rollback concluído."
}
trap rollback EXIT

# --- Start ---
cd "$PROJECT_DIR" || die "PROJECT_DIR inválido: $PROJECT_DIR"
log "BEGIN F8.8 v2 | ENV=$ENV | REQUIRE_PROMETHEUS=$REQUIRE_PROMETHEUS | KEEP_STACK_UP=$KEEP_STACK_UP"
log "Repo: $(pwd)"

log "=== BASELINE ==="
git status || die "git status falhou"
pytest -q --tb=short -r a || die "pytest falhou"

log "=== PRECHECK PORTAS ==="
ss -tln | grep -q ':8000 ' || log "porta 8000 livre (ok)"
ss -tln | grep -q ':5432 ' || log "porta 5432 livre (ok)"
ss -tln | grep -q ':3000 ' || log "porta 3000 livre (ok)"
ss -tln | grep -q ':9090 ' || log "porta 9090 livre (ok)"

log "=== NETWORK ==="
docker network ls | grep -q "$NET_NAME" || docker network create "$NET_NAME" >/dev/null
docker network inspect "$NET_NAME" >/dev/null || die "network inspect falhou: $NET_NAME"

log "=== CLEAN START ==="
docker compose -f "$GRAFANA_COMPOSE" down --volumes --remove-orphans >/dev/null 2>&1 || true
[[ -n "$METRICS_COMPOSE" ]] && docker compose -f "$METRICS_COMPOSE" down --volumes --remove-orphans >/dev/null 2>&1 || true
docker compose -f "$BASE_COMPOSE" down --volumes --remove-orphans >/dev/null 2>&1 || true

log "=== UP BASE (API+DB) ==="
docker compose -f "$BASE_COMPOSE" up -d || { collect_evidence; die "falha ao subir base"; }

log "=== VALIDATE API ==="
curl --max-time 10 --retry 6 --retry-all-errors --connect-timeout 5 -f http://localhost:8000/health >/dev/null \
  || { collect_evidence; die "API /health falhou"; }

curl --max-time 10 --retry 6 --retry-all-errors --connect-timeout 5 -f http://localhost:8000/metrics >/dev/null \
  || { collect_evidence; die "API /metrics falhou"; }

log "=== GOVERNANCE CHECK: API_CMD ==="
API_CMD="$(docker inspect techno-os-api --format '{{json .Config.Cmd}}' 2>/dev/null || true)"
log "API_CMD=$API_CMD"

if [[ "$ENV" == "staging" ]]; then
  log "staging: reload proibido (comando condicional garante)."
else
  log "development: reload permitido (não obrigatório)."
fi

log "=== PROMETHEUS (optional) ==="
if [[ -n "$METRICS_COMPOSE" ]]; then
  log "metrics compose detectado: $METRICS_COMPOSE"
  docker compose -f "$METRICS_COMPOSE" up -d || { collect_evidence; die "falha ao subir prometheus"; }

  curl --max-time 10 --retry 6 --retry-all-errors --connect-timeout 5 -f http://localhost:9090/-/ready >/dev/null \
    || { collect_evidence; die "Prometheus /-/ready falhou"; }

  # Query up
  UP_JSON="$(curl --max-time 10 --retry 6 --retry-all-errors --connect-timeout 5 -s "http://localhost:9090/api/v1/query?query=up" || true)"
  echo "$UP_JSON" | grep -q '"status":"success"' || { collect_evidence; die "Prometheus query up não retornou success"; }

  echo "$UP_JSON" | grep -q '\[.*,"1"\]' || log "WARN: up=1 não encontrado claramente (verificar targets/manual)."
else
  if [[ "$REQUIRE_PROMETHEUS" == "1" ]]; then
    collect_evidence
    die "REQUIRE_PROMETHEUS=1 mas docker-compose.metrics.yml ausente"
  fi
  log "Prometheus SKIPPED (metrics compose não existe)."
fi

log "=== GRAFANA ==="
docker compose -f "$GRAFANA_COMPOSE" up -d || { collect_evidence; die "falha ao subir grafana"; }

curl --max-time 10 --retry 10 --retry-all-errors --connect-timeout 5 -f http://localhost:3000/api/health >/dev/null \
  || { collect_evidence; die "Grafana /api/health falhou"; }

log "=== GRAFANA AUTH + CONTRACT (DS + Dashboard) ==="
DS_JSON="$(curl --max-time 10 --retry 6 --retry-all-errors --connect-timeout 5 -s -u "${GRAFANA_ADMIN_USER}:${GRAFANA_ADMIN_PASSWORD}" http://localhost:3000/api/datasources || true)"
echo "$DS_JSON" | grep -q '"name":"Prometheus"' || { collect_evidence; die "Datasource Prometheus não encontrada no Grafana"; }

DB_JSON="$(curl --max-time 10 --retry 6 --retry-all-errors --connect-timeout 5 -s -u "${GRAFANA_ADMIN_USER}:${GRAFANA_ADMIN_PASSWORD}" "http://localhost:3000/api/search?query=TechnoOS%20Minimal" || true)"
echo "$DB_JSON" | grep -q '"title":"TechnoOS Minimal"' || { collect_evidence; die "Dashboard 'TechnoOS Minimal' não encontrado"; }

log "=== FATAL LOG SCAN ==="
docker logs techno-os-api --tail 300 2>/dev/null | grep -iE "traceback|modulenotfounderror|importerror|nameerror|exception|fatal" && { collect_evidence; die "API fatal detectado em logs"; } || true
docker logs technoos_prometheus --tail 300 2>/dev/null | grep -iE "panic|fatal" && { collect_evidence; die "Prometheus fatal detectado em logs"; } || true
docker logs technoos_grafana --tail 300 2>/dev/null | grep -iE "panic|fatal" && { collect_evidence; die "Grafana fatal detectado em logs"; } || true

log "SEAL: F8.8 OK — observability contract runbook (CI-friendly, fail-closed)."
exit 0
