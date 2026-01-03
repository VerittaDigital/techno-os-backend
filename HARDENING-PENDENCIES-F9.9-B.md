# 🔒 HARDENING PENDENCIES — F9.9-B
**Registro Formal de Pendências para Próxima Fase**

---

## 📋 METADATA

- **Fase**: F9.9-B (Hardening)
- **Dependência**: F9.8 (COMPLETA — commit de3c8e2)
- **Status**: BLOCKED by RISK-2
- **Data Registro**: 2026-01-03T08:20:00Z
- **Autoria**: Evidence-based review F9.8
- **SEAL Origem**: [SEAL-F9.8-CONSOLIDATED.md](SEAL-F9.8-CONSOLIDATED.md)

---

## 🚨 BLOQUEIOS CRÍTICOS (MUST-FIX ANTES DE INICIAR F9.9-B)

### RISK-2: Grafana Credenciais Default 🔴 **CRÍTICO — BLOCKING**

**Descrição:**  
Grafana inicializado com credenciais default `admin:admin` (ambiente production).

**Evidência Primária:**  
- Container: `docker logs techno-os-grafana` não mostra `GF_SECURITY_ADMIN_PASSWORD` customizado
- URL: https://grafana.verittadigital.com (acessível externamente via TLS)
- Estado: Não testado login (mas comportamento padrão Grafana é manter admin:admin)

**Impacto:**  
- Acesso não autorizado ao painel de monitoramento
- Modificação de dashboards e alertas
- Possível pivô para reconnaissance de infraestrutura
- **VIOLAÇÃO LGPD**: Métricas podem conter informações sobre uso da API

**Acceptance Criteria (para desbloquear F9.9-B):**  
```bash
# Teste de aceitação:
curl -u admin:admin https://grafana.verittadigital.com/api/auth/keys
# Deve retornar: 401 Unauthorized (senha alterada)
```

**Ação Obrigatória:**  
```bash
# 1. Login manual em https://grafana.verittadigital.com
# 2. Alterar senha admin em Profile > Change Password
# 3. Criar usuário viewer (read-only) para análise diária
# 4. Documentar alteração:
ssh deploy@72.61.219.157
echo "$(date -u): Grafana admin password changed" >> /opt/techno-os/artifacts/hardening_f9_9_b.log
```

**Prazo:** IMEDIATO (antes de qualquer deploy F9.9-B)

---

## ⚠️ RISCOS RECOMENDADOS (SHOULD-FIX em F9.9-B)

### RISK-1: Prometheus Exposto Sem Autenticação 🟡 **MÉDIO-ALTO**

**Descrição:**  
Prometheus acessível publicamente via HTTPS sem Basic Auth ou IP allowlist.

**Evidência Primária:**  
- Teste externo: `curl -skI https://prometheus.verittadigital.com/-/healthy` → HTTP/2 200
- Vhost: `/etc/nginx/sites-available/prometheus.verittadigital.com` sem diretiva `auth_basic`
- Port bind: `ss -tlnp | grep :9090` → `LISTEN *:9090` (wildcard, não 127.0.0.1)

**Impacto:**  
- Information disclosure (métricas de performance, não PII)
- Reconhecimento de arquitetura (endpoints, services, latências)
- Possível denial of service via queries pesadas

**Acceptance Criteria:**  
```bash
# Teste de aceitação:
curl -skI https://prometheus.verittadigital.com/-/healthy
# Deve retornar: HTTP/2 401 (se Basic Auth implementado)
# OU: HTTP/2 403 (se IP allowlist implementado)
```

**Opções de Mitigação (escolher 1):**

#### Opção A: Basic Auth (Recomendado — Baixo Risco Operacional)
```nginx
# /etc/nginx/sites-available/prometheus.verittadigital.com
location / {
    auth_basic "Prometheus";
    auth_basic_user_file /etc/nginx/.htpasswd_prometheus;
    proxy_pass http://127.0.0.1:9090;
}
```
```bash
# Gerar htpasswd:
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd_prometheus prometheus_user
sudo nginx -t && sudo systemctl reload nginx
```

**Prós:** Simples, padrão industry, compatível com Grafana datasource  
**Contras:** Credencial adicional para gerenciar

#### Opção B: IP Allowlist (Segurança Máxima — Risco Operacional Médio)
```nginx
# /etc/nginx/sites-available/prometheus.verittadigital.com
location / {
    allow 72.61.219.157; # VPS próprio
    allow <IP_ESCRITORIO>;
    deny all;
    proxy_pass http://127.0.0.1:9090;
}
```

**Prós:** Sem credenciais, mais seguro  
**Contras:** Equipe remota precisa VPN/IP fixo

**Decisão Necessária:** Tech Lead deve escolher Opção A ou B  
**Prazo:** Recomendado em F9.9-B

---

### RISK-6: Alert Rules Ausentes 🟡 **MÉDIO**

**Descrição:**  
Prometheus funcional mas sem regras de alerta configuradas.

**Evidência Primária:**  
- Arquivo `/opt/techno-os/app/backend/prometheus/alerts.yml` não existe
- Docker compose: `command: --config.file=/etc/prometheus/prometheus.yml` sem `--rules` flag
- Dashboard: "Alerts" tab vazio em Grafana

**Impacto:**  
- Falhas de API não detectadas automaticamente
- Degradação de performance silenciosa
- Violação de SLA sem notificação

**Acceptance Criteria:**  
```bash
# 1. Alert rules configuradas:
curl -s http://127.0.0.1:9090/api/v1/rules | jq '.data.groups[].name'
# Deve retornar ao menos: ["api_health", "api_performance"]

# 2. Alertmanager funcional:
curl -s http://127.0.0.1:9093/api/v2/status | jq '.cluster.status'
# Deve retornar: "ready"
```

**Ação Recomendada:**  
```yaml
# prometheus/alerts.yml (criar):
groups:
  - name: api_health
    interval: 30s
    rules:
      - alert: APIDown
        expr: up{job="techno-os-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API indisponível por 1min+"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Taxa de erro > 5% por 2min"
```

**Dependências:**  
- Alertmanager container (adicionar ao docker-compose)
- Webhook Slack/Email (configurar destino)

**Prazo:** F9.9-B recomendado

---

### RISK-4: Backup Ausente 🟡 **MÉDIO**

**Descrição:**  
Dados Prometheus e Grafana sem backup automatizado.

**Evidência Primária:**  
- `docker volume inspect techno-os-backend_prometheus_data` → `/var/lib/docker/volumes/...`
- `docker volume inspect techno-os-backend_grafana_data` → `/var/lib/docker/volumes/...`
- Script backup: Não existe em `/opt/techno-os/scripts/`
- Cron: `crontab -l` não lista backup job

**Impacto:**  
- Perda de histórico de métricas (data loss)
- Perda de dashboards customizados
- Dificuldade de rollback em caso de corrupção

**Acceptance Criteria:**  
```bash
# 1. Script backup criado:
ls -lh /opt/techno-os/scripts/backup_observability.sh
# Deve retornar: -rwxr-xr-x ... backup_observability.sh

# 2. Cron configurado:
crontab -l | grep backup_observability
# Deve retornar: 0 2 * * * /opt/techno-os/scripts/backup_observability.sh

# 3. Backup funcional:
ls -lh /opt/techno-os/backups/observability/latest.tar.gz
# Deve retornar: arquivo recente (<24h)
```

**Ação Recomendada:**  
```bash
#!/bin/bash
# /opt/techno-os/scripts/backup_observability.sh
BACKUP_DIR="/opt/techno-os/backups/observability"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup Prometheus data
docker run --rm \
  -v techno-os-backend_prometheus_data:/data \
  -v ${BACKUP_DIR}:/backup \
  alpine tar czf /backup/prometheus_${TIMESTAMP}.tar.gz /data

# Backup Grafana data
docker run --rm \
  -v techno-os-backend_grafana_data:/data \
  -v ${BACKUP_DIR}:/backup \
  alpine tar czf /backup/grafana_${TIMESTAMP}.tar.gz /data

# Retenção: 7 dias
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +7 -delete

# Link latest
ln -sf prometheus_${TIMESTAMP}.tar.gz ${BACKUP_DIR}/prometheus_latest.tar.gz
ln -sf grafana_${TIMESTAMP}.tar.gz ${BACKUP_DIR}/grafana_latest.tar.gz
```

**Dependências:** Espaço em disco (estimar ~500MB/semana)  
**Prazo:** F9.9-B recomendado

---

### RISK-7: Rollback Procedure Não Formalizado 🟡 **MÉDIO**

**Descrição:**  
Sem procedimento documentado para rollback de observability stack.

**Evidência Primária:**  
- Arquivo `docs/rollback_observability.md` não existe
- SEAL F9.8: Menciona "zero downtime deployment" mas não rollback
- Backup existe (F9.7) mas sem procedimento de restore

**Impacto:**  
- Tempo de resposta lento em incidentes
- Risco de danos colaterais durante rollback manual
- Violação de governança (procedure não auditável)

**Acceptance Criteria:**  
```bash
# 1. Documento criado:
ls -lh docs/rollback_observability.md
# Deve retornar: arquivo existente

# 2. Conteúdo mínimo:
grep -q "docker-compose down" docs/rollback_observability.md
grep -q "docker volume rm" docs/rollback_observability.md
grep -q "nginx sites-enabled" docs/rollback_observability.md
# Todos devem retornar: 0 (success)
```

**Ação Recomendada:**  
Criar `docs/rollback_observability.md` com:
1. Passos de rollback container-by-container
2. Ordem de desativação Nginx vhosts
3. Procedimento de restore de backup
4. Validação pós-rollback (API ainda funcional?)
5. Tempo estimado: 5-10min

**Prazo:** F9.9-B recomendado

---

## 🟢 RISCOS BAIXOS (MAY-FIX — Backlog)

### RISK-3: Monitoramento Contínuo Ausente

**Descrição:** Zero downtime não comprovado (sem monitoring loop durante deploy).  
**Mitigação Sugerida:** UptimeRobot ou similar (5min checks).  
**Prioridade:** Baixa (não bloqueia produção).

### RISK-5: Rate Limiting Ausente

**Descrição:** Endpoints Prometheus/Grafana sem rate limit.  
**Mitigação Sugerida:** Nginx `limit_req_zone` em `/etc/nginx/nginx.conf`.  
**Prioridade:** Baixa (risco teórico de DoS).

### RISK-8: Policy Retenção Artifacts Ausente

**Descrição:** `/opt/techno-os/artifacts/` crescendo indefinidamente.  
**Mitigação Sugerida:** Cron cleanup (30 dias retenção).  
**Prioridade:** Baixa (espaço em disco não crítico ainda).

---

## 📅 ROADMAP F9.9-B

### Pre-Flight (ANTES DE INICIAR F9.9-B)
- [ ] ✅ F9.8 commitado (de3c8e2)
- [ ] 🔴 **BLOCKER**: Trocar senha Grafana (RISK-2)
- [ ] 🟡 Decidir: Basic Auth ou IP allowlist para Prometheus (RISK-1)

### F9.9-B Scope (LLM Hardening + Observability Hardening)
- [ ] LLM provider hardening (timeout 30s, retry 2x, exponential backoff)
- [ ] Fail-closed enforcement (LLM falha → reject request, não "try anyway")
- [ ] Circuit breaker pattern (3 falhas consecutivas → open 60s)
- [ ] Rate limiting LLM endpoints (10 req/min por usuário)
- [ ] 🟡 Implementar RISK-1 mitigation (se aprovado)
- [ ] 🟡 Implementar RISK-6 (alert rules)
- [ ] 🟡 Implementar RISK-4 (backup automatizado)
- [ ] 🟡 Implementar RISK-7 (rollback procedure doc)
- [ ] Structured logging LLM calls (audit trail)
- [ ] SEAL F9.9-B com evidence collection

### Post-Go (APÓS F9.9-B)
- [ ] Validar alertas (triggar falha intencional, verificar notificação)
- [ ] Validar backup (restore em ambiente staging)
- [ ] Validar circuit breaker (simular 3 timeouts LLM)
- [ ] Documentar runbook operacional (on-call playbook)

---

## 🎯 CRITÉRIOS DE SUCESSO F9.9-B

**F9.9-B considerado COMPLETO quando:**

1. ✅ RISK-2 mitigado (Grafana password != admin:admin)
2. ✅ LLM hardening implementado (timeout + retry + circuit breaker)
3. ✅ Fail-closed enforcement em LLM executor
4. ✅ Rate limiting LLM endpoints funcional
5. ✅ RISK-6 mitigado (2+ alert rules configuradas e testadas)
6. ✅ Evidence collection + SEAL F9.9-B criado
7. 🟡 OPCIONAL: RISK-1, RISK-4, RISK-7 mitigados (conforme priorização)

**Governança:** Evidence-based, fail-closed, human-in-the-loop.

---

## 📚 REFERÊNCIAS

- [SEAL-F9.8-CONSOLIDATED.md](SEAL-F9.8-CONSOLIDATED.md) — Documento principal F9.8
- [F9.8-SEAL-v1.1-EVIDENCE-BASED-REVIEW.md](F9.8-SEAL-v1.1-EVIDENCE-BASED-REVIEW.md) — 8 riscos detalhados
- [F9.8-SEAL-v1.1-CHANGELOG.md](F9.8-SEAL-v1.1-CHANGELOG.md) — Correções v1.0 → v1.1
- VPS Evidence: `/opt/techno-os/artifacts/f9_8_seal_v1_1_20260103_080937/` (14 files)

---

**ASSINATURA:**  
Documento gerado por evidence-based review F9.8.  
Tech Lead deve aprovar mitigations antes de F9.9-B start.

**TIMESTAMP:** 2026-01-03T08:20:00Z  
**COMMIT:** de3c8e2 (F9.8 deployment)
