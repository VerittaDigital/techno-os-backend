# RUNBOOK OPERACIONAL — Observabilidade Techno OS

**Fase:** F9.9-C  
**Data:** 2026-01-04  
**Stack:** Backend (FastAPI) + PostgreSQL + Prometheus (standalone)

---

## 📊 VISÃO GERAL

Este runbook documenta procedimentos operacionais para:
- Verificação de health
- Interpretação de métricas LLM
- Diagnóstico de circuit breaker
- Backup e restore

---

## 🔍 VERIFICAÇÃO DE HEALTH

### Backend API

**URL:** http://localhost:8000/health  
**Produção:** https://api.verittadigital.com/health

```bash
curl -s http://localhost:8000/health | jq
# Esperado: {"status": "ok"}
```

**Se falhar:**
1. Verificar container: `docker ps | grep techno-os-api`
2. Verificar logs: `docker logs techno-os-api --tail 50`
3. Verificar PostgreSQL: `docker ps | grep techno-os-db`

---

### PostgreSQL

```bash
docker exec techno-os-db pg_isready -U techno_user -d techno_os
# Esperado: techno_os - accepting connections
```

**Se falhar:**
1. Verificar container: `docker ps -a | grep techno-os-db`
2. Verificar logs: `docker logs techno-os-db --tail 50`
3. Validar env vars: `DB_USER`, `DB_PASSWORD`

---

### Prometheus (Standalone)

**URL:** http://localhost:9090/-/healthy  
**Produção:** https://prometheus.verittadigital.com/-/healthy

```bash
curl -s http://localhost:9090/-/healthy
# Esperado: Prometheus Server is Healthy.
```

**Se falhar:**
1. Verificar se Prometheus está rodando (processo ou container externo)
2. Verificar prometheus.yml syntax: `promtool check config prometheus.yml`
3. Verificar scrape targets: http://localhost:9090/targets

---

## 📈 MÉTRICAS LLM (F9.9-B)

### Latência (p50, p95, p99)

```promql
# p95 latency por provider
histogram_quantile(0.95, llm_request_latency_seconds{provider="openai"})

# p99 latency geral
histogram_quantile(0.99, rate(llm_request_latency_seconds_bucket[5m]))
```

**Thresholds:**
- p50 < 2s: OK
- p95 < 10s: OK
- p99 > 20s: Investigar timeout/retry

---

### Tokens Consumidos

```promql
# Total tokens por tipo (prompt vs completion)
sum(llm_tokens_total) by (provider, type)

# Rate de tokens/segundo
rate(llm_tokens_total{type="completion"}[5m])
```

**Uso:**
- Monitorar custos de API
- Detectar spikes anormais

---

### Erros LLM

```promql
# Total erros por tipo
sum(llm_errors_total) by (provider, error_type)

# Rate de erros (erros/segundo)
rate(llm_errors_total{error_type="provider_error"}[5m])
```

**Error types:**
- `timeout`: Timeout de rede (30s)
- `provider_error`: Erro do provider (5xx, rate limit)
- `circuit_open`: Circuit breaker aberto (3 falhas)

---

## 🚨 DIAGNÓSTICO CIRCUIT BREAKER

### Verificar Estado Atual

**Métrica:** `llm_errors_total{error_type="circuit_open"}`

```promql
# Verificar se circuit está aberto agora
llm_errors_total{error_type="circuit_open"} > 0
```

**Se circuit_open > 0:**
1. Circuit breaker está **ABERTO** (bloqueando chamadas)
2. Cooldown: **60 segundos** (configurado em F9.9-C)
3. Após cooldown: entra em **HALF_OPEN** (1 tentativa)

---

### Causas Comuns

1. **3 falhas consecutivas:**
   - Provider instável (OpenAI 5xx)
   - Network timeout (> 30s)
   - Rate limit esgotado (429)

2. **Como identificar:**
   ```promql
   # Rate de timeouts recentes
   rate(llm_errors_total{error_type="timeout"}[1m])
   
   # Rate de provider errors
   rate(llm_errors_total{error_type="provider_error"}[1m])
   ```

---

### Procedimento de Recovery

1. **Aguardar cooldown** (60s):
   - Circuit entra em HALF_OPEN automaticamente
   - Próxima chamada LLM é testada

2. **Se HALF_OPEN falhar:**
   - Circuit volta para OPEN (mais 60s)
   - Investigar causa raiz (logs, provider status)

3. **Se HALF_OPEN suceder:**
   - Circuit volta para CLOSED
   - Operação normal restaurada

4. **Ação manual (se necessário):**
   - Restart do serviço API (zera circuit breaker)
   ```bash
   docker restart techno-os-api
   ```

---

## 💾 BACKUP E RESTORE

### Executar Backup Manual

```bash
# Usar script versionado
/opt/techno-os/scripts/backup_observability.sh

# Ou com diretório customizado
BACKUP_DIR=/mnt/backups /opt/techno-os/scripts/backup_observability.sh
```

**Output esperado:**
```
✅ Iniciando backup: 20260104_020000
📦 Backup PostgreSQL...
✅ PostgreSQL backup: postgres_20260104_020000.tar.gz
🗑️ Aplicando retenção (7 dias)...
✅ Backup concluído: 20260104_020000
```

---

### Configurar Cron (Automático)

```bash
# Editar crontab
crontab -e

# Adicionar linha (backup diário às 2h)
0 2 * * * /opt/techno-os/scripts/backup_observability.sh >> /var/log/backup_obs.log 2>&1
```

**Validar cron:**
```bash
# Listar jobs agendados
crontab -l | grep backup_observability

# Verificar log (após primeira execução)
tail -f /var/log/backup_obs.log
```

---

### Restore PostgreSQL

**Passo 1: Parar serviços**
```bash
cd /opt/techno-os/app/backend
docker-compose down
```

**Passo 2: Remover volume antigo**
```bash
docker volume rm techno-os-backend_postgres_data
```

**Passo 3: Recriar volume vazio**
```bash
docker volume create techno-os-backend_postgres_data
```

**Passo 4: Restaurar backup**
```bash
# Usar backup específico
BACKUP_FILE="/opt/techno-os/backups/observability/postgres_20260104_020000.tar.gz"

# Ou usar latest
BACKUP_FILE="/opt/techno-os/backups/observability/postgres_latest.tar.gz"

# Restaurar
docker run --rm \
  -v techno-os-backend_postgres_data:/data \
  -v /opt/techno-os/backups/observability:/backup:ro \
  alpine:latest \
  sh -c "cd /data && tar xzf /backup/$(basename $BACKUP_FILE)"
```

**Passo 5: Subir serviços**
```bash
docker-compose up -d
```

**Passo 6: Validar restore**
```bash
# Health check
curl http://localhost:8000/health

# Verificar dados (exemplo: preferences)
docker exec -it techno-os-db psql -U techno_user -d techno_os \
  -c "SELECT COUNT(*) FROM user_preferences;"
```

**Tempo estimado:** 5-10 minutos

---

## ⚠️ ALERTAS (FUTURO: F9.10+)

**Status F9.9-C:** EIXO 2 BLOQUEADO (Prometheus fora docker-compose)

Quando Prometheus for integrado ao docker-compose:
- Criar `prometheus/alerts.yml` com 4 regras
- Configurar Alertmanager (opcional)
- Documentar interpretação de alertas

---

## 🔐 VARIÁVEIS ENV OBRIGATÓRIAS

### LLM Hardening (F9.9-B)

```bash
# Allowlist de providers (fail-closed)
VERITTA_LLM_ALLOWED_PROVIDERS="fake,openai"

# API keys por provider
OPENAI_API_KEY="sk-..."
# ANTHROPIC_API_KEY="sk-ant-..."
# GOOGLE_API_KEY="..."
# XAI_API_KEY="..."
# DEEPSEEK_API_KEY="..."

# Provider padrão (se não especificado explicitamente)
LLM_PROVIDER="fake"  # Desenvolvimento: usar fake
# LLM_PROVIDER="openai"  # Produção: usar real
```

---

## 📚 REFERÊNCIAS

- [SEAL F9.9-B](../sessions/f9.9-b/SEAL-F9.9-B.md) — LLM Hardening
- [SEAL F9.9-C](../sessions/f9.9-c/SEAL-F9.9-C.md) — Integração + Observabilidade
- [LLM Integration Guide](LLM_INTEGRATION_GUIDE.md) — Guia técnico
- [Prometheus Docs](https://prometheus.io/docs/) — Documentação oficial

---

**Última atualização:** 2026-01-04  
**Revisão:** F9.9-C
