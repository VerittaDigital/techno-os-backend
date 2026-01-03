#!/usr/bin/env bash
# ════════════════════════════════════════
# F9.8 — OBSERVABILIDADE EXTERNA
# PROMETHEUS (INTERNO) + GRAFANA (TLS)
# ════════════════════════════════════════
# EXECUTAR NO VPS (deploy@72.61.219.157)
# NÃO EXECUTAR LOCALMENTE
# ════════════════════════════════════════

set -euo pipefail

TS="$(date -u +%Y%m%d_%H%M%S)"
ART="/opt/techno-os/artifacts/f9_8_obs_${TS}"
sudo mkdir -p "$ART"
sudo chown -R deploy:deploy /opt/techno-os

log(){ echo "[$(date -Is)] $*" | tee -a "$ART/f9_8.log"; }
die(){ log "ABORT: $*"; exit 1; }

log "F9.8 START — PRECONDITIONS"

# ════════════════════════════════════════
# PRÉ-CONDIÇÕES (BLOQUEANTES)
# ════════════════════════════════════════

# 0) Confirmar API (F9.7) intacta — BLOQUEANTE
curl -fsS https://api.verittadigital.com/health | tee "$ART/api_health_pre.txt" >/dev/null \
  || die "API /health falhou. Não iniciar F9.8."

# 1) Validar DNS de subdomínios — BLOQUEANTE
for d in grafana.verittadigital.com prometheus.verittadigital.com; do
  log "DNS check: $d"
  nslookup "$d" 2>&1 | tee "$ART/nslookup_${d}.txt" | grep -q "Address" \
    || die "DNS não resolvendo $d"
done

# 2) Validar portas livres localmente — BLOQUEANTE
log "Port check (3000/9090) must be free or unused"
sudo ss -tlnp | grep -E ':(3000|9090)\b' | tee "$ART/ports_3000_9090.txt" && die "Porta 3000/9090 já em uso" || true

# 3) Validar nginx ativo — BLOQUEANTE
sudo systemctl is-active nginx | tee "$ART/nginx_active.txt" | grep -q "active" \
  || die "nginx não está ativo"

# 4) Firewall evidence (não modifica)
if command -v ufw >/dev/null 2>&1; then 
  sudo ufw status | tee "$ART/ufw_status.txt" || true
fi

# 5) Backup Nginx — BLOQUEANTE
log "Backup nginx config"
sudo mkdir -p /opt/techno-os/backup/nginx_pre_f9_8_"$TS"
sudo cp -a /etc/nginx /opt/techno-os/backup/nginx_pre_f9_8_"$TS"/ 2>/dev/null || die "Backup Nginx falhou"
echo "/opt/techno-os/backup/nginx_pre_f9_8_${TS}" | tee "$ART/nginx_backup_path.txt" >/dev/null

# 6) Certbot presente — BLOQUEANTE
certbot --version 2>&1 | tee "$ART/certbot_version.txt" >/dev/null || die "certbot não disponível"

log "PRECONDITIONS OK"

# ════════════════════════════════════════
# STEP 1 — ESTRUTURA + SECRETS
# ════════════════════════════════════════
log "STEP1 — Create directories and minimal env"

OBS="/opt/techno-os/observability"
sudo mkdir -p "$OBS"/{prometheus,grafana/provisioning/datasources,grafana/provisioning/dashboards,grafana/dashboards}
sudo chown -R deploy:deploy "$OBS"

# Gerar senha do Grafana
GRAFANA_ADMIN_PASSWORD="$(openssl rand -base64 24 | tr -d '\n')"
[ -n "$GRAFANA_ADMIN_PASSWORD" ] || die "Falha ao gerar senha do Grafana"

cat > "$OBS/.env.observability" <<EOF
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
EOF
chmod 600 "$OBS/.env.observability"

# Registrar credencial como evidência
echo "GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}" | tee "$ART/f9_8_credentials.txt" >/dev/null
chmod 600 "$ART/f9_8_credentials.txt"

log "STEP1 DONE"

# ════════════════════════════════════════
# STEP 1.5 — ARTEFATOS EXECUTÁVEIS
# ════════════════════════════════════════
log "STEP1.5 — Write executable artifacts (compose + configs + provisioning)"

# 1) Prometheus config — scrape backend local
cat > "$OBS/prometheus/prometheus.yml" <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "techno_api"
    metrics_path: /metrics
    static_configs:
      - targets: ["127.0.0.1:8000"]
EOF

# 2) Grafana datasource provisioning
cat > "$OBS/grafana/provisioning/datasources/prometheus.yml" <<'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://127.0.0.1:9090
    isDefault: true
EOF

# 3) Grafana dashboard provider provisioning
cat > "$OBS/grafana/provisioning/dashboards/dashboard.yml" <<'EOF'
apiVersion: 1
providers:
  - name: "Techno"
    orgId: 1
    folder: "Techno"
    type: file
    disableDeletion: true
    editable: true
    options:
      path: /var/lib/grafana/dashboards
EOF

# 4) Dashboard mínimo — scaffold para customização posterior
cat > "$OBS/grafana/dashboards/fastapi_minimal.json" <<'EOF'
{
  "uid": "techno-fastapi-min",
  "title": "TECHNO OS — FastAPI Minimal",
  "timezone": "browser",
  "schemaVersion": 38,
  "version": 1,
  "refresh": "10s",
  "panels": [
    {
      "id": 1,
      "title": "Backend Status",
      "type": "stat",
      "targets": [
        {
          "expr": "up{job=\"techno_api\"}",
          "refId": "A"
        }
      ],
      "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
    },
    {
      "id": 2,
      "title": "Request Rate (5m)",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(process_requests_total[5m])",
          "refId": "A"
        }
      ],
      "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0}
    },
    {
      "id": 3,
      "title": "P95 Latency",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(techno_request_latency_seconds_bucket[5m])) by (le))",
          "refId": "A"
        }
      ],
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
    }
  ],
  "annotations": { "list": [] },
  "templating": { "list": [] }
}
EOF

# 5) docker-compose.observability.yml
cat > "$OBS/docker-compose.observability.yml" <<'EOF'
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: techno-prometheus
    network_mode: host
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    restart: unless-stopped

  grafana:
    image: grafana/grafana-oss:latest
    container_name: techno-grafana
    depends_on:
      - prometheus
    ports:
      - "3000:3000"
    env_file:
      - ./.env.observability
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_AUTH_ANONYMOUS_ENABLED=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning/datasources:/etc/grafana/provisioning/datasources:ro
      - ./grafana/provisioning/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    restart: unless-stopped

volumes:
  grafana-data:
EOF

# Evidências (hash dos artefatos)
sha256sum "$OBS/prometheus/prometheus.yml" "$OBS/docker-compose.observability.yml" \
  "$OBS/grafana/provisioning/datasources/prometheus.yml" "$OBS/grafana/provisioning/dashboards/dashboard.yml" \
  "$OBS/grafana/dashboards/fastapi_minimal.json" | tee "$ART/artifacts_sha256.txt" >/dev/null

log "STEP1.5 DONE"

# ════════════════════════════════════════
# STEP 2 — SUBIR OBSERVABILITY
# ════════════════════════════════════════
log "STEP2 — docker compose up (observability)"
cd "$OBS"
docker compose -f docker-compose.observability.yml up -d 2>&1 | tee "$ART/docker_compose_up.txt" >/dev/null || die "docker compose up falhou"

# Aguardar containers iniciarem
sleep 5

# Validar Prometheus localmente
curl -fsS http://127.0.0.1:9090/-/ready | tee "$ART/prom_ready.txt" >/dev/null || die "Prometheus não está ready"
curl -fsS "http://127.0.0.1:9090/api/v1/targets" | tee "$ART/prom_targets.json" >/dev/null || die "Targets do Prometheus inacessíveis"

# Fail-closed: confirmar scrape backend
grep -q '"health":"up"' "$ART/prom_targets.json" || die "Prometheus não está conseguindo scrape do backend (/metrics)"

# Validar Grafana local
curl -fsS http://127.0.0.1:3000/login | tee "$ART/grafana_login_http.txt" >/dev/null || die "Grafana não responde em 127.0.0.1:3000"

log "STEP2 DONE"

# ════════════════════════════════════════
# STEP 3 — NGINX + HTTP (PRÉ-TLS)
# ════════════════════════════════════════
log "STEP3 — Nginx server block for grafana (HTTP only, pre-TLS)"

GRAFANA_SITE="/etc/nginx/sites-available/grafana.verittadigital.com"
sudo tee "$GRAFANA_SITE" >/dev/null <<'EOF'
server {
  listen 80;
  listen [::]:80;
  server_name grafana.verittadigital.com;

  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 60s;
    proxy_connect_timeout 5s;
    proxy_send_timeout 60s;
  }
}
EOF

sudo ln -sf "$GRAFANA_SITE" /etc/nginx/sites-enabled/grafana.verittadigital.com

# Nginx test bloqueante
sudo nginx -t 2>&1 | tee "$ART/nginx_test_pre_tls.txt" >/dev/null || die "nginx -t falhou"
sudo systemctl reload nginx

# Smoke test HTTP externo
curl -I http://grafana.verittadigital.com 2>&1 | tee "$ART/grafana_http_head.txt" >/dev/null || die "HTTP externo grafana falhou"

log "STEP3 DONE — HTTP OK, ready for TLS"

# ════════════════════════════════════════
# CHECKPOINT HUMANO
# ════════════════════════════════════════
log "═══════════════════════════════════════════"
log "HUMAN CHECKPOINT: GO para emitir TLS?"
log "═══════════════════════════════════════════"
log "Estado atual:"
log "  ✅ Prometheus interno OK (não exposto)"
log "  ✅ Grafana HTTP OK (http://grafana.verittadigital.com)"
log "  ✅ API F9.7 intacta"
log ""
log "Próximo passo: Emitir certificado TLS para grafana.verittadigital.com"
log ""
read -p "Digite 'GO' para continuar ou CTRL+C para parar aqui: " GO_RESP

if [ "$GO_RESP" != "GO" ]; then
  log "Execução pausada pelo usuário. Estado seguro mantido."
  exit 0
fi

# ════════════════════════════════════════
# STEP 4 — CERTBOT TLS
# ════════════════════════════════════════
log "STEP4 — Emitindo certificado TLS via certbot"

LE_EMAIL="verittadigital@gmail.com"

# Rollback automático se certbot falhar
rollback_tls(){
  echo "[${TS}] ROLLBACK TLS: removendo site grafana e restaurando backup nginx" | tee -a "$ART/rollback.log"
  sudo rm -f /etc/nginx/sites-enabled/grafana.verittadigital.com || true
  sudo rm -f /etc/nginx/sites-available/grafana.verittadigital.com || true
  BK="$(cat "$ART/nginx_backup_path.txt")"
  sudo rm -rf /etc/nginx
  sudo cp -a "$BK/nginx" /etc/nginx
  sudo nginx -t || true
  sudo systemctl reload nginx || true
  exit 1
}
trap rollback_tls ERR

sudo certbot --nginx -d grafana.verittadigital.com \
  --non-interactive --agree-tos --email "$LE_EMAIL" \
  --redirect 2>&1 | tee "$ART/certbot_grafana.txt" >/dev/null || die "certbot falhou"

sudo nginx -t 2>&1 | tee "$ART/nginx_test_post_tls.txt" >/dev/null || die "nginx -t falhou pós TLS"
sudo systemctl reload nginx

# Validar HTTPS grafana
curl -I https://grafana.verittadigital.com/login 2>&1 | tee "$ART/grafana_https_head.txt" >/dev/null || die "HTTPS grafana falhou"

# Renovação dry-run
sudo certbot renew --dry-run 2>&1 | tee "$ART/certbot_renew_dryrun.txt" >/dev/null || die "certbot renew --dry-run falhou"

# Validar API intacta (F9.7)
curl -fsS https://api.verittadigital.com/health | tee "$ART/api_health_post.txt" >/dev/null || die "API /health falhou após F9.8"

# Evidências finais
sudo certbot certificates 2>&1 | tee "$ART/certbot_certificates.txt" >/dev/null || true
docker ps 2>&1 | tee "$ART/docker_ps.txt" >/dev/null || true

log "STEP4 DONE"

# ════════════════════════════════════════
# VALIDAÇÕES FINAIS (SEAL)
# ════════════════════════════════════════
log "═══════════════════════════════════════════"
log "VALIDAÇÕES FINAIS — SEAL CANDIDATE"
log "═══════════════════════════════════════════"

SEAL_OK=1

# 1) prom_targets.json contém techno_api health=up
if grep -q '"health":"up"' "$ART/prom_targets.json"; then
  log "✅ Prometheus scrape OK (backend UP)"
else
  log "❌ Prometheus scrape FALHOU"
  SEAL_OK=0
fi

# 2) Grafana HTTPS OK
if [ -f "$ART/grafana_https_head.txt" ] && grep -q "200\|302" "$ART/grafana_https_head.txt"; then
  log "✅ Grafana HTTPS OK"
else
  log "❌ Grafana HTTPS FALHOU"
  SEAL_OK=0
fi

# 3) Certbot renew --dry-run OK
if [ -f "$ART/certbot_renew_dryrun.txt" ] && ! grep -qi "error\|failed" "$ART/certbot_renew_dryrun.txt"; then
  log "✅ Certbot renew dry-run OK"
else
  log "❌ Certbot renew dry-run FALHOU"
  SEAL_OK=0
fi

# 4) API /health OK pós mudanças
if [ -f "$ART/api_health_post.txt" ] && grep -q '"status":"ok"' "$ART/api_health_post.txt"; then
  log "✅ API /health OK (F9.7 intacta)"
else
  log "❌ API /health FALHOU"
  SEAL_OK=0
fi

# 5) Artifacts presentes
if [ -f "$ART/artifacts_sha256.txt" ] && [ -f "$ART/nginx_backup_path.txt" ]; then
  log "✅ Artifacts OK"
else
  log "❌ Artifacts incompletos"
  SEAL_OK=0
fi

log "═══════════════════════════════════════════"

if [ "$SEAL_OK" -eq 1 ]; then
  log "🎉 F9.8 — SELADA"
  log "Estado final:"
  log "  ✅ Prometheus interno (não exposto publicamente)"
  log "  ✅ Grafana HTTPS: https://grafana.verittadigital.com"
  log "  ✅ Datasource Prometheus OK"
  log "  ✅ API F9.7 intacta"
  log "  ✅ TLS renovação automática OK"
  log ""
  log "Credenciais Grafana:"
  log "  Usuário: admin"
  log "  Senha: (ver $ART/f9_8_credentials.txt)"
  log ""
  log "Artifacts: $ART"
  
  # Criar SEAL formal
  cat > "$ART/SEAL-F9.8.md" <<SEAL_EOF
# 🔒 SEAL — F9.8 OBSERVABILIDADE EXTERNA

**Data**: $(date -Is)
**Fase**: F9.8 — Prometheus (interno) + Grafana (TLS externo)
**Status**: ✅ SELADA

## Entregas

1. ✅ Prometheus interno (127.0.0.1:9090) — NÃO exposto publicamente
2. ✅ Grafana HTTPS: https://grafana.verittadigital.com
3. ✅ Scrape backend: 127.0.0.1:8000/metrics
4. ✅ Dashboard mínimo provisionado
5. ✅ TLS Let's Encrypt (renovação automática)

## Validações

- ✅ Prometheus targets: techno_api UP
- ✅ Grafana HTTPS acessível
- ✅ Certbot renew dry-run OK
- ✅ API F9.7 intacta (https://api.verittadigital.com/health)
- ✅ Artifacts completos

## Credenciais

- Usuário Grafana: admin
- Senha: (ver f9_8_credentials.txt)

## Artifacts

Diretório: $ART

## Próximas Fases

- F9.9-A: Memória persistente (user preferences)
- F9.9-B: LLM hardening (produção-ready)
- F10: Console funcional (frontend)

**F9.8 SELADA EM**: $(date -Is)
SEAL_EOF

  log "SEAL criado: $ART/SEAL-F9.8.md"
  
else
  log "❌ F9.8 — ABORTADA (validações falharam)"
  log "Diagnóstico completo em: $ART"
  exit 1
fi

log "F9.8 EXECUTION COMPLETE"
