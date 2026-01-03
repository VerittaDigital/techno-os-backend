#!/bin/bash
# F9.7 STEP3 — Nginx + TLS (Certbot) para api.verittadigital.com
# Modo: Produção Controlada · Fail-Closed · Human-in-the-Loop
# Pré-condições: API viva em 127.0.0.1:8000, DNS configurado, portas 80/443 abertas

set -euo pipefail

# ============================================================================
# BLOCO PRÉ-CERTBOT: Validações + Server Block HTTP
# ============================================================================

TS="$(date -u +%Y%m%d_%H%M%S)"
ART="/opt/techno-os/artifacts/f9_7_tls_${TS}"
sudo mkdir -p "$ART"
sudo chown -R deploy:deploy /opt/techno-os

log(){ echo "[$(date -Is)] $*" | tee -a "$ART/step3.log"; }
die(){ log "ABORT: $*"; exit 1; }

log "========================================================================"
log "STEP3 START - Nginx+TLS for api.verittadigital.com"
log "Artifact dir: $ART"
log "========================================================================"

# 0) Backup nginx
log "0) Backup /etc/nginx"
sudo tar -czf "$ART/nginx_backup_${TS}.tar.gz" /etc/nginx/ 2>/dev/null || true

# 0.1) DNS → VPS (BLOQUEANTE)
log "0.1) Validar DNS api.verittadigital.com"
DNS_IP="$(dig +short api.verittadigital.com A | head -n1 || true)"
VPS_IP="$(curl -4fsS ifconfig.me 2>/dev/null || curl -4fsS icanhazip.com 2>/dev/null || hostname -I | awk '{print $1}')"
[ -n "$DNS_IP" ] || die "DNS A record vazio."
[ -n "$VPS_IP" ] || die "IP público do VPS não identificado."
log "DNS_IP=$DNS_IP | VPS_IP=$VPS_IP"
[ "$DNS_IP" = "$VPS_IP" ] || die "DNS=$DNS_IP não aponta para VPS=$VPS_IP"
log "✓ DNS válido"

# 0.2) Firewall 80/443 (se UFW ativo)
log "0.2) Validar firewall (ufw)"
if command -v ufw >/dev/null 2>&1 && sudo ufw status | grep -q "Status: active"; then
  sudo ufw allow 80/tcp >/dev/null 2>&1 || true
  sudo ufw allow 443/tcp >/dev/null 2>&1 || true
  sudo ufw reload >/dev/null 2>&1 || true
  sudo ufw status | tee "$ART/ufw_status.txt" || true
  log "✓ UFW configurado (80/443 abertos)"
else
  log "UFW inativo ou ausente (OK)."
fi

# 1) API health local (BLOQUEANTE)
log "1) API health local"
curl -fsS http://127.0.0.1:8000/health >/dev/null || die "API não responde localmente"
log "✓ API healthy em 127.0.0.1:8000"

# 2) Nginx ativo (BLOQUEANTE)
log "2) Nginx status"
sudo systemctl status nginx --no-pager | tee "$ART/nginx_status.txt" || die "nginx inativo"
log "✓ Nginx ativo"

# 0.3) Remover site default
log "0.3) Remover default site se existir"
if [ -e /etc/nginx/sites-enabled/default ]; then
  sudo rm -f /etc/nginx/sites-enabled/default || true
  log "✓ Default site removido"
else
  log "Default site não existe (OK)"
fi

# 3) Listeners 80/443 (evidência)
log "3) Listeners 80/443"
sudo ss -ltnp | egrep '(:80|:443)\s' | tee "$ART/ports_ss.txt" || log "Nenhum listener 80/443 ativo ainda"
sudo lsof -i :80 -i :443 2>/dev/null | tee "$ART/ports_lsof.txt" || log "lsof: nenhum processo em 80/443"

# 4) Server block HTTP
log "4) Criar server block HTTP"
NGINX_SITE="/etc/nginx/sites-available/api.verittadigital.com"
sudo tee "$NGINX_SITE" >/dev/null <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name api.verittadigital.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
    }
}
EOF

sudo ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/api.verittadigital.com
sha256sum "$NGINX_SITE" | tee "$ART/nginx_site_sha256.txt" || true
log "✓ Server block criado: $NGINX_SITE"

# 5) nginx -t (BLOQUEANTE)
log "5) nginx -t"
sudo nginx -t 2>&1 | tee "$ART/nginx_test.txt" || die "nginx -t falhou"
log "✓ Nginx config válida"

# 6) reload nginx
log "6) Reload nginx"
sudo systemctl reload nginx
log "✓ Nginx recarregado"

# 7) HTTP externo (BLOQUEANTE)
log "7) Smoke test HTTP externo"
sleep 2
curl -fsS http://api.verittadigital.com/health 2>&1 | tee "$ART/http_health_api.txt" || die "HTTP /health externo falhou"
curl -IfsS http://api.verittadigital.com/health 2>&1 | tee "$ART/http_head_api.txt" || true
log "✓ HTTP /health externo acessível"

log "========================================================================"
log "HUMAN CHECKPOINT: Pré-TLS completo. GO para TLS?"
log "LE_EMAIL=${LE_EMAIL:-NÃO DEFINIDO}"
log "LE_STAGING=${LE_STAGING:-0} (0=produção, 1=staging)"
log "========================================================================"
echo ""
echo "Para continuar com TLS, execute:"
echo "  export LE_EMAIL=\"verittadigital@gmail.com\""
echo "  export LE_STAGING=\"0\""
echo "  bash /opt/techno-os/scripts/f9_7_step3_tls.sh"
echo ""
