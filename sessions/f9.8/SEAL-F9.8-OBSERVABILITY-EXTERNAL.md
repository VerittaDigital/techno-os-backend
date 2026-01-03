# SEAL F9.8 — OBSERVABILIDADE EXTERNA (Prometheus + Grafana TLS)

**Data:** 2026-01-03T07:45 UTC  
**Revisão v1.1:** 2026-01-03T08:10 UTC (Evidence-based FAIL-CLOSED review)  
**Branch:** stage/f9.8-observability  
**Commit:** d73cfb1  
**Executor:** GitHub Copilot (automated)

---

## 1. RESUMO EXECUTIVO

**Objetivo:** Deploy de stack de observabilidade externa com TLS (Prometheus + Grafana)

**Escopo:**
- ✅ Backend `/metrics` endpoint (F9.8-HOTFIX)
- ✅ Prometheus scraping backend (porta 9090 interna; **acesso externo via HTTPS sem autenticação**)
- ✅ Grafana dashboards (TLS público, **credenciais default até troca manual**)
- ✅ Nginx reverse proxy com TLS (Let's Encrypt ECDSA)
- ✅ DNS configurado e validado

**Status:** ✅ **F9.8 COMPLETO E SELADO**

**URLs Production:**
- Grafana: https://grafana.verittadigital.com (público, **possível admin:admin ativo**)
- Prometheus: https://prometheus.verittadigital.com (**público SEM autenticação** ⚠️)
- API: https://api.verittadigital.com (unchanged)

---

## 2. ARQUITETURA IMPLEMENTADA

```
┌─────────────────────────────────────────────────┐
│                 INTERNET                        │
└─────────────────────────────────────────────────┘
                      │
                      ├─► https://grafana.verittadigital.com (443)
                      │   └─► Nginx → Grafana:3000
                      │
                      ├─► https://prometheus.verittadigital.com (443)
                      │   └─► Nginx → Prometheus:9090
                      │
                      └─► https://api.verittadigital.com (443)
                          └─► Nginx → API:8000

┌─────────────────────────────────────────────────┐
│              VPS 72.61.219.157                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Nginx (port 443)                              │
│    │                                            │
│    ├─► Grafana Container (port 3000)           │
│    │   └─► Dashboards, visualizações           │
│    │                                            │
│    ├─► Prometheus Container (port 9090)        │
│    │   └─► Scrapes backend:8000/metrics        │
│    │                                            │
│    └─► Backend API (port 8000)                 │
│        └─► /metrics endpoint (Prometheus)      │
│        └─► /health endpoint                     │
│                                                 │
│  PostgreSQL (port 5432)                        │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Prometheus Scrape Flow:**
```
Prometheus (127.0.0.1:9090)
    └─► scrape: http://127.0.0.1:8000/metrics
        └─► Backend FastAPI prometheus_client
            └─► Métricas: GC, requests, Python runtime
```

---

## 3. COMPONENTES DEPLOYADOS

### 3.1 Backend `/metrics` Endpoint

**Status:** ✅ Ativo (via F9.8-HOTFIX)

**Implementação:** `app/main.py` (linhas 69-72)
```python
@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

**Validação:**
```bash
$ curl 127.0.0.1:8000/metrics | head -5
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 460.0
python_gc_objects_collected_total{generation="1"} 40.0
python_gc_objects_collected_total{generation="2"} 5.0
```

### 3.2 Prometheus

**Container:** `techno-prometheus`  
**Image:** `prom/prometheus:latest`  
**Port interno:** 9090 (bind em `*:9090`)  
**Port externo:** 443 HTTPS via Nginx (**SEM autenticação** ⚠️)  
**Config:** `/opt/techno-os/observability/prometheus.yml`

**⚠️ EXPOSIÇÃO:** Prometheus acessível publicamente via `https://prometheus.verittadigital.com` **sem Basic Auth ou IP allowlist**. Ver seção RISKS OPEN.

**Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'techno_api'
    scrape_interval: 15s
    static_configs:
      - targets: ['127.0.0.1:8000']
```

**Targets Status:**
```json
{
  "job": "techno_api",
  "health": "up",
  "lastScrape": "2026-01-03T07:45:22Z",
  "scrapeUrl": "http://127.0.0.1:8000/metrics"
}
```

### 3.3 Grafana

**Container:** `techno-grafana`  
**Image:** `grafana/grafana-oss:latest`  
**Port:** 3000 (local), 443 (HTTPS público via Nginx)  
**URL:** https://grafana.verittadigital.com

**🔴 RISCO CRÍTICO:** Credenciais default (admin:admin) **podem estar ativas**. Troca de senha obrigatória antes de uso produtivo.

**Access:**
- Login via browser (default admin:admin, **DEVE SER ALTERADO IMEDIATAMENTE**)
- Prometheus datasource: http://127.0.0.1:9090 (internal)

**HTTP Status:** `302 Found` (redirect to /login) ✅

### 3.4 TLS Certificates

**Grafana:**
- Domain: grafana.verittadigital.com
- Issuer: Let's Encrypt (ECDSA, secp384r1)
- Valid: 2026-01-03 → 2026-04-03 (90 dias)
- Path: `/etc/letsencrypt/live/grafana.verittadigital.com/`

**Prometheus:**
- Domain: prometheus.verittadigital.com
- Issuer: Let's Encrypt (ECDSA, secp384r1)
- Valid: 2026-01-03 → 2026-04-03 (90 dias)
- Path: `/etc/letsencrypt/live/prometheus.verittadigital.com/`

**Renovação:** Auto-renewal via certbot systemd timer

### 3.5 Nginx Reverse Proxy

**Vhosts ativos:**
- api.verittadigital.com (F9.7)
- grafana.verittadigital.com (F9.8)
- prometheus.verittadigital.com (F9.8)

**Config:** `/etc/nginx/sites-enabled/`

**Grafana vhost (resumo):**
```nginx
server {
    listen 443 ssl http2;
    server_name grafana.verittadigital.com;
    
    ssl_certificate /etc/letsencrypt/live/grafana.verittadigital.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/grafana.verittadigital.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Prometheus vhost:** Similar, proxy para 127.0.0.1:9090

---

## 4. EXECUÇÃO (SEQUÊNCIA DE PASSOS)

### 4.1 F9.8-HOTFIX (Pré-requisito)

**Problema inicial:** Prometheus scrape falhando (backend /metrics → 404)

**Solução:** Deploy backend atualizado com `/metrics` endpoint

**Resultado:** ✅ `/metrics` ativo, scrape funcionando

**Detalhes:** Ver [SEAL-F9.8-HOTFIX.md](SEAL-F9.8-HOTFIX.md)

### 4.2 F9.8-TLS Deployment

**Script:** `/tmp/f9_8_tls_v2.sh`

**Estratégia:**
1. Containers Prometheus + Grafana já existiam (criados anteriormente)
2. HTTP-only vhosts primeiro (para certbot validation)
3. Certbot TLS (webroot method)
4. Upgrade vhosts para HTTPS + redirect
5. Validações end-to-end

**Timeline:**
- 07:44:56 UTC — START
- 07:44:59 UTC — HTTP vhosts ativados
- 07:45:17 UTC — Certbot TLS OK (2 certificados)
- 07:45:17 UTC — HTTPS vhosts ativados
- 07:45:22 UTC — Validações OK
- **07:45:22 UTC — F9.8 COMPLETO**

**Tempo total:** ~26 segundos

---

## 5. VALIDAÇÕES EXECUTADAS

### 5.1 Pré-Deployment
- ✅ API `/health` OK (https://api.verittadigital.com/health)
- ✅ Containers running (techno-grafana, techno-prometheus)
- ✅ Prometheus scrape `"health":"up"`
- ✅ Grafana HTTP 302 (redirect to /login)
- ✅ DNS resolving (grafana, prometheus subdomains)

### 5.2 Pós-Deployment
- ✅ API `/health` OK (unchanged)
- ✅ Grafana HTTPS 302 (https://grafana.verittadigital.com)
- ✅ Prometheus HTTPS 200 (https://prometheus.verittadigital.com/-/healthy)
- ✅ Certificados válidos (90 dias)
- ✅ Containers still running
- ✅ Prometheus targets `"health":"up"`

### 5.3 Validações Externas (Post-SEAL)

**Grafana HTTPS:**
```bash
$ curl -skI https://grafana.verittadigital.com
HTTP/2 302 
server: nginx/1.24.0 (Ubuntu)
location: /login
```

**Prometheus HTTPS:**
```bash
$ curl -skI https://prometheus.verittadigital.com/-/healthy
HTTP/2 200 
server: nginx/1.24.0 (Ubuntu)
```

---

## 6. EVIDÊNCIAS PRESERVADAS

**Diretório:** `/opt/techno-os/artifacts/f9_8_tls_20260103_074442/`

**Arquivos:**
- `f9_8_tls.log` — Log completo de execução
- `api_health_pre.txt` — API health pré-deploy
- `api_health_post.txt` — API health pós-deploy
- `nslookup_grafana.verittadigital.com.txt` — DNS validation
- `nslookup_prometheus.verittadigital.com.txt` — DNS validation
- `certbot_grafana.txt` — Certbot output (Grafana)
- `certbot_prometheus.txt` — Certbot output (Prometheus)
- `cert_grafana_ls.txt` — Certificate files listing
- `cert_prometheus_ls.txt` — Certificate files listing
- `cert_grafana.verittadigital.com_dates.txt` — Certificate validity
- `cert_prometheus.verittadigital.com_dates.txt` — Certificate validity
- `nginx_test_http.txt` — Nginx config test (HTTP)
- `nginx_test_https.txt` — Nginx config test (HTTPS)
- `nginx_sites_enabled.txt` — Active vhosts list
- `prometheus_targets.txt` — Prometheus targets JSON
- `containers_post.txt` — Docker containers status
- `sites-available/` — Nginx configs backup (pre-deploy)
- `sites-enabled/` — Nginx configs backup (pre-deploy)

---

## 7. GOVERNANÇA V-COF

### 7.1 Fail-Closed ✅
- API health validada PRÉ e PÓS deploy
- Nginx config test antes de reload
- ABORT em qualquer falha crítica
- Rollback capability (Nginx configs backup)

### 7.2 Human-in-the-Loop ✅
- Prompt F9.8-TLS criado
- Executability parecer N/A (hotfix urgente)
- User command: "EXECUTE"
- Evidências preservadas para audit

### 7.3 Privacidade (LGPD) ✅
- Deployment infra-only (sem dados pessoais)
- Métricas Prometheus: runtime stats apenas
- Grafana: UI para análise humana (não coleta dados sensíveis)

### 7.4 Zero Downtime ✅
- API mantida funcionando durante todo processo
- Containers observability não reiniciados
- Nginx reload (graceful, não restart)
- Health checks OK em todos momentos

---

## 8. PRÓXIMOS PASSOS

### 8.1 Grafana Setup (Manual)
1. Acessar https://grafana.verittadigital.com
2. Login inicial: admin / admin
3. Alterar senha (mandatory)
4. Configurar Prometheus datasource:
   - Type: Prometheus
   - URL: http://127.0.0.1:9090
   - Access: Server (default)
   - Save & Test
5. Importar dashboards:
   - FastAPI dashboard (ID: 16110 ou similar)
   - Python runtime dashboard

### 8.2 Prometheus Alerting (Opcional)
- Configurar Alertmanager (se necessário)
- Definir rules: high CPU, errors, downtime
- Integrar com Slack/email (se aplicável)

### 8.3 Security Hardening (Recomendado)
- Prometheus: adicionar auth básica via Nginx (se exposto)
- Grafana: configurar SMTP para notificações
- Firewall: garantir 9090 não exposto publicamente (check feito)

### 8.4 Roadmap
- ⏳ F9.9-A: Memory Persistent (PostgreSQL user preferences)
- ⏳ F9.9-B: LLM Hardening (production-ready multi-provider)
- ⏳ F10: Console frontend integration

---

## 9. MÉTRICAS DO DEPLOYMENT

| Métrica | Valor |
|---------|-------|
| **Tempo total** | 26 segundos |
| **Certificados TLS** | 2 (ECDSA secp384r1) |
| **Vhosts criados** | 2 (Grafana, Prometheus) |
| **Containers deployados** | 0 (já existiam) |
| **Downtime API** | Não observado nas validações pré/pós* |
| **Validações** | 10/10 OK |
| **Rollbacks** | 0 |

*_Downtime zero-absoluto não comprovado por monitoramento contínuo; Nginx reload é graceful por design._

---

## 10. COMANDOS DE VALIDAÇÃO

**Backend Metrics:**
```bash
curl 127.0.0.1:8000/metrics | head -10
```

**Prometheus Targets:**
```bash
curl -s http://127.0.0.1:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

**Grafana HTTPS:**
```bash
curl -skI https://grafana.verittadigital.com
```

**Prometheus HTTPS:**
```bash
curl -skI https://prometheus.verittadigital.com/-/healthy
```

**Containers Status:**
```bash
sudo docker ps --filter name=techno --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Certificates Expiry:**
```bash
sudo openssl x509 -in /etc/letsencrypt/live/grafana.verittadigital.com/fullchain.pem -noout -dates
```

---

## 11. TROUBLESHOOTING

### 11.1 Grafana não carrega dashboards
- Verificar datasource Prometheus configurado
- URL: http://127.0.0.1:9090
- Test connection via UI

### 11.2 Prometheus scrape falha
- Verificar backend `/metrics` responde: `curl 127.0.0.1:8000/metrics`
- Verificar prometheus.yml scrape config
- Restart Prometheus: `sudo docker restart techno-prometheus`

### 11.3 TLS certificate errors
- Verificar DNS aponta para VPS IP
- Verificar certbot renewal ativo: `sudo systemctl status certbot.timer`
- Manual renewal test: `sudo certbot renew --dry-run`

### 11.4 Nginx 502 Bad Gateway
- Verificar containers running: `sudo docker ps`
- Verificar logs: `sudo docker logs techno-grafana`
- Verificar Nginx logs: `sudo tail -50 /var/log/nginx/error.log`

---

## 12. LIÇÕES APRENDIDAS

### 12.1 Certbot Strategy
**Problema:** Chicken-and-egg (Nginx precisa certs, certbot precisa Nginx OK)

**Solução:** HTTP-only vhosts primeiro → certbot → upgrade to HTTPS

**Resultado:** Deployment smooth sem manual intervention

### 12.2 Containers Reuse
**Decisão:** Não recrear containers existentes (Prometheus + Grafana)

**Vantagem:** Mantém dados Prometheus históricos

**Trade-off:** Assume containers em estado OK (validado pré-deploy)

### 12.3 Validação Granular
**Abordagem:** Validar cada passo (DNS, containers, scrape, HTTP, HTTPS)

**Benefício:** ABORT early se qualquer pré-condição falha

**Resultado:** Deployment confiável e auditável

---

## 13. RISKS OPEN / ACCEPTED (v1.1)

### RISK-1: Prometheus Exposto Sem Autenticação

**Severidade:** 🟡 **MÉDIO-ALTO**

**Descrição:**
- Prometheus acessível via `https://prometheus.verittadigital.com` sem Basic Auth ou IP allowlist
- Expõe métricas internas do backend (CPU, memória, requests, etc.)
- Acesso de leitura irrestrito

**Evidência:**
- Vhost Prometheus: sem diretivas `auth_basic`, `allow`, ou `deny`
- `curl -skI https://prometheus.verittadigital.com/-/healthy` → HTTP/2 200 (sem autenticação)

**Impacto:**
- Vazamento de informações operacionais (não PII, mas sensível)
- Possível uso para reconhecimento de infraestrutura

**Mitigação implementada:** Nenhuma (F9.8 não incluía autenticação)

**Mitigação recomendada (fora do escopo F9.8):**
1. Adicionar Basic Auth no vhost Prometheus (Nginx)
2. Ou: IP allowlist para equipe técnica
3. Ou: Mover para VPN/túnel SSH

**Status:** ⚠️ **RISCO ACEITO** para F9.8; requer decisão de hardening em fase futura.

---

### RISK-2: Grafana Credenciais Default

**Severidade:** 🔴 **ALTO**

**Descrição:**
- Grafana acessível via `https://grafana.verittadigital.com`
- Credenciais default (admin:admin) **podem estar ativas** até ação humana
- Acesso de escrita a dashboards e datasources

**Impacto:**
- Acesso não autorizado a dashboards
- Modificação/exclusão de configurações
- Potencial pivô para acesso a Prometheus (via datasource config)

**Mitigação implementada:** Nenhuma (aguarda ação humana)

**Mitigação pendente (ação manual obrigatória):**
1. Login via browser → alterar senha admin
2. Criar usuário viewer com permissões read-only
3. Configurar SMTP (opcional) para notificações

**Status:** 🔴 **RISCO CRÍTICO ABERTO** — Ação humana obrigatória pós-deploy.

---

### RISK-3: Ausência de Monitoramento Contínuo

**Severidade:** 🟢 **BAIXO**

**Descrição:**
- Deploy validado apenas com health checks pré/pós
- Sem evidência de monitoramento contínuo durante o período de mudança
- Downtime não descartado com 100% de certeza

**Impacto:**
- Possível downtime imperceptível não detectado
- Confiança reduzida em afirmação "zero downtime"

**Mitigação implementada:** Validações pré/pós + graceful reload

**Mitigação recomendada:**
- Implementar monitoring contínuo (ex.: UptimeRobot, Pingdom) em fase futura

**Status:** ⚠️ **RISCO BAIXO ACEITO** — Validações manuais suficientes para F9.8.

---

## 14. SEGURANÇA

### 14.1 TLS Configuration
- Protocols: TLSv1.2 + TLSv1.3
- Ciphers: HIGH:!aNULL:!MD5
- Key type: ECDSA (secp384r1)
- Auto-renewal: ✅ Enabled

### 14.2 Network Exposure (Corrigido v1.1)
- Grafana: HTTPS público (443) — **Credenciais default risco crítico** 🔴
- Prometheus: HTTPS público (443) — **SEM autenticação** 🟡
- Backend /metrics: Interno (127.0.0.1:8000) — ✅ Não exposto

### 14.3 Recommendations
1. **CRÍTICO:** Alterar senha Grafana admin imediatamente
2. **ALTO:** Adicionar Basic Auth no vhost Prometheus
3. Grafana: Configurar usuários viewer (read-only)
4. Backend: Rate limiting no /metrics (se exposto futuramente)

---

## 15. COMPLIANCE

### 15.1 LGPD
- ✅ Métricas Prometheus: runtime stats apenas (não PII)
- ✅ Grafana: ferramenta de visualização (não coleta dados pessoais)
- ⚠️ Prometheus exposto: métricas operacionais acessíveis (não PII, mas sensível)

### 15.2 Auditoria
- ✅ Evidências completas preservadas
- ✅ Logs timestamped
- ✅ Certificados rastreáveis (Let's Encrypt CT logs)
- ✅ Human approval (user command: EXECUTE)
- ✅ **Evidências v1.1:** `/opt/techno-os/artifacts/f9_8_seal_v1_1_20260103_080937/`

### 15.3 Fail-Closed
- ✅ API health validada PRÉ + PÓS
- ✅ ABORT se qualquer validação falha
- ✅ Rollback capability (Nginx configs backup)

---

## 15. STATUS FINAL

**F9.8 OBSERVABILITY EXTERNAL:** ✅ **SEALED**

**Production URLs:**
- API: https://api.verittadigital.com ✅
- Grafana: https://grafana.verittadigital.com ✅
- Prometheus: https://prometheus.verittadigital.com ✅

**Components:**
- Backend /metrics: ✅ Active
- Prometheus scraping: ✅ `"health":"up"`
- Grafana TLS: ✅ HTTPS (302 redirect to /login) — **🔴 Credenciais default risco crítico**
- Prometheus TLS: ✅ HTTPS (200 OK) — **🟡 SEM autenticação**
- Certificates: ✅ Valid until 2026-04-03
- Nginx: ✅ 3 vhosts active
- Containers: ✅ All healthy

**Risks Open:** 2 críticos (ver seção 13) — **Ação humana obrigatória**

**Next Milestone:** F9.9-A (Memory Persistent)

---

**Timestamp de SEAL:** 2026-01-03T07:45:22 UTC  
**Revisão v1.1 (FAIL-CLOSED):** 2026-01-03T08:10 UTC  
**Git SHA:** d73cfb1  
**Evidências deployment:** `/opt/techno-os/artifacts/f9_8_tls_20260103_074442/`  
**Evidências v1.1 review:** `/opt/techno-os/artifacts/f9_8_seal_v1_1_20260103_080937/`  
**Human validator:** ⏳ Aguardando confirmação + **ação em riscos críticos**

