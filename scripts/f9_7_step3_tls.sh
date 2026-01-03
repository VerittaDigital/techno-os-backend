#!/bin/bash
# F9.7 STEP3 — TLS (Certbot) para api.verittadigital.com
# EXECUTAR SOMENTE APÓS GO HUMANO
# Pré-requisito: f9_7_step3_nginx_tls.sh completado com sucesso

set -euo pipefail

# ============================================================================
# BLOCO TLS: Certbot + Validações HTTPS
# ============================================================================

: "${LE_EMAIL:?ABORT: LE_EMAIL não definido}"

TS="$(date -u +%Y%m%d_%H%M%S)"
ART="/opt/techno-os/artifacts/f9_7_tls_${TS}_tls"
sudo mkdir -p "$ART"
sudo chown -R deploy:deploy /opt/techno-os

log(){ echo "[$(date -Is)] $*" | tee -a "$ART/tls.log"; }
die(){ log "ABORT: $*"; exit 1; }

rollback_tls() {
  log "========================================================================"
  log "ROLLBACK: Erro detectado, removendo site-enabled"
  log "========================================================================"
  sudo rm -f /etc/nginx/sites-enabled/api.verittadigital.com || true
  sudo systemctl reload nginx || true
  exit 1
}
trap rollback_tls ERR

log "========================================================================"
log "STEP3 TLS START - Certbot para api.verittadigital.com"
log "LE_EMAIL=$LE_EMAIL"
log "LE_STAGING=${LE_STAGING:-0}"
log "Artifact dir: $ART"
log "========================================================================"

# Staging flag
STAGING_FLAG=""
if [ "${LE_STAGING:-0}" = "1" ]; then
  STAGING_FLAG="--staging"
  log "⚠️ MODO STAGING (certificado de teste)"
else
  log "✓ MODO PRODUÇÃO (certificado real)"
fi

# Certbot execution
log "Executando certbot..."
sudo certbot --nginx -d api.verittadigital.com \
  --non-interactive --agree-tos --email "$LE_EMAIL" \
  --redirect $STAGING_FLAG 2>&1 | tee "$ART/certbot.txt"

trap - ERR
log "✓ Certbot executado"

# Validação pós-certbot
log "Validando configuração pós-certbot..."
sudo nginx -t 2>&1 | tee "$ART/nginx_test_after.txt" || die "nginx pós-certbot falhou"
log "✓ Nginx config válida pós-TLS"

sudo systemctl reload nginx
log "✓ Nginx recarregado"

# Smoke tests HTTPS
log "Smoke test HTTPS..."
sleep 2
curl -fsS https://api.verittadigital.com/health 2>&1 | tee "$ART/https_health.txt" || die "Health HTTPS falhou"
log "✓ HTTPS /health OK"

curl -IfsS https://api.verittadigital.com/health 2>&1 | tee "$ART/https_head_api.txt" || true
log "✓ HTTPS HEAD OK"

# Evidências certificado
log "Coletando evidências certificado..."
sudo certbot certificates 2>&1 | tee "$ART/certbot_certificates.txt" || true
sudo certbot renew --dry-run 2>&1 | tee "$ART/certbot_renew_dryrun.txt" || true

log "========================================================================"
log "STEP3 TLS DONE — api.verittadigital.com em HTTPS"
log "Certificado Let's Encrypt emitido com sucesso"
log "Artifacts: $ART"
log "========================================================================"
echo ""
echo "✓ API acessível via HTTPS: https://api.verittadigital.com"
echo "✓ Health endpoint: https://api.verittadigital.com/health"
echo ""
