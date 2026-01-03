# 🏛️ Techno OS Backend — Architecture

**Visão Arquitetural High-Level**

---

## 📋 Visão Geral

Techno OS Backend é uma API inteligente que integra Large Language Models (LLMs) com governança V-COF (Veritta Code of Conduct Framework), fornecendo assistência contextualizada com foco em privacidade e auditabilidade.

**Stack Tecnológico:**
- **API Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15+
- **LLM Providers:** OpenAI, Anthropic, Google (multi-provider)
- **Observability:** Prometheus + Grafana
- **Deployment:** Docker Compose + Nginx (reverse proxy)
- **Infrastructure:** VPS Ubuntu 24.04 LTS

---

## 🏗️ Componentes Principais

```
┌─────────────┐
│   Cliente   │
│ (Frontend)  │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────┐
│        Nginx Reverse Proxy          │
│  (TLS termination, rate limiting)   │
└──────┬──────────────────┬───────────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│  FastAPI     │   │ Prometheus   │
│  Backend     │   │ (Metrics)    │
└──────┬───────┘   └──────────────┘
       │                  ▲
       ├──────────────────┘
       │ /metrics
       │
       ├──► PostgreSQL (User data, sessions)
       │
       ├──► LLM Gateway (Multi-provider)
       │    ├─► OpenAI API
       │    ├─► Anthropic API
       │    └─► Google Gemini API
       │
       └──► Audit Log (Evidence collection)
```

---

## 🔄 Fluxo de Requisição

### 1. Entrada de Requisição
```
Cliente → Nginx → FastAPI → Privacy Guard
```

**Privacy Guard:**
- Valida que não há PII sensível no input
- Anonimiza dados se necessário (LGPD by design)
- Bloqueia requisição se detectar violação

### 2. Pipeline V-COF
```
Privacy Guard → Intent Classification → Context Builder → LLM Gateway
```

**Intent Classification:**
- Classifica intenção do usuário (query, code, audit, etc.)
- Determina qual contexto adicionar

**Context Builder:**
- Busca contexto relevante (docs, sessions, artifacts)
- Empacota prompt com governança V-COF
- Adiciona instruções de comportamento

### 3. Chamada LLM
```
LLM Gateway → Provider Selection → API Call → Response Validation
```

**LLM Gateway:**
- Seleciona provider (fallback automático)
- Timeout: 30s
- Retry: 2x com exponential backoff
- Circuit breaker: 3 falhas → open 60s

**Response Validation:**
- Valida formato de resposta
- Remove PII se presente (fail-closed)
- Registra em audit log

### 4. Sugestão de Memória
```
Response → Memory Suggester → User Approval → Storage (opcional)
```

**Memória Dignificada:**
- NUNCA armazena automaticamente
- Sempre pergunta ao usuário
- Armazena apenas preferências explícitas (tom, formato)
- NUNCA armazena dados sensíveis

---

## 📂 Estrutura de Diretórios

```
techno-os-backend/
├── app/                    # 🐍 Código fonte FastAPI
│   ├── __init__.py
│   ├── main.py             # Entry point
│   ├── api/                # Routers FastAPI
│   ├── core/               # Config, security, dependencies
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   │   ├── llm_client.py   # LLM Gateway
│   │   ├── privacy_guard.py # Privacy validation
│   │   └── audit_log.py    # Audit trail
│   └── utils/              # Helpers
│
├── tests/                  # 🧪 Testes automatizados
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                   # 📚 Documentação técnica
│   ├── architecture/       # ADRs (Architecture Decision Records)
│   ├── implementation/     # Guias de implementação
│   ├── operations/         # Runbooks, disaster recovery
│   ├── audits/             # Pareceres comerciais, valuation
│   └── governance/         # Políticas V-COF, LGPD
│
├── sessions/               # 🔐 SEAL documents (histórico)
│   ├── f9.7/, f9.8/, ...   # SEALs por fase
│   └── consolidation/      # Snapshots canônicos
│
├── artifacts/              # 💾 Evidências de implementação
│   ├── f9_5/, f9_6/, ...   # Artifacts por fase
│   └── archive/            # Artifacts >90 dias
│
├── planning/               # 📝 Roadmap e planejamento
│   ├── ROADMAP.md
│   ├── HARDENING-PENDENCIES-F9.9-B.md
│   └── backlog/
│
├── observability/          # 📊 Configs Prometheus + Grafana
├── nginx/                  # 🌐 Configs Nginx reverse proxy
├── alembic/                # 🔄 Database migrations
├── scripts/                # 🛠️ Automações operacionais
└── backups/                # 💾 Backups e disaster recovery
```

---

## 🔐 Segurança e Governança

### Princípios V-COF

1. **IA como instrumento**
   - LLM auxilia, humano decide
   - Não cria automações irreversíveis sem aprovação

2. **Human-in-the-loop**
   - Checkpoints de revisão em operações críticas
   - Deploy manual ou com aprovação explícita

3. **Evidence-based execution**
   - Toda implementação crítica gera evidências em `artifacts/`
   - Auditabilidade total via SEAL documents

4. **Fail-closed enforcement**
   - Se validação falha → abortar requisição
   - Não tentar "fazer de qualquer jeito"

5. **LGPD by design**
   - Privacy Guard valida entrada
   - Não inferir traços psicológicos
   - Não armazenar PII sem consentimento

### Hardening Implementado

- ✅ **F9.8:** Observability (Prometheus + Grafana)
- ✅ **F9.8.1:** Prometheus Basic Auth
- ✅ **F9.8A:** SSH hardening (passwordauth disabled)
- ✅ **STEP 10.2:** SSH reload automation
- ⏳ **F9.9-B:** LLM Hardening (em desenvolvimento)

---

## 📊 Observability e Monitoramento

### Métricas Coletadas (Prometheus)

**API Metrics:**
- `http_requests_total` — Total de requisições
- `http_request_duration_seconds` — Latência de requisições
- `http_requests_in_progress` — Requisições em andamento

**LLM Metrics:**
- `llm_requests_total` — Total de chamadas LLM
- `llm_request_duration_seconds` — Latência de LLM
- `llm_provider_failures` — Falhas por provider
- `llm_circuit_breaker_state` — Estado do circuit breaker

**System Metrics:**
- `process_cpu_seconds_total` — CPU usage
- `process_resident_memory_bytes` — Memory usage
- `process_open_fds` — File descriptors

### Dashboards (Grafana)

- **API Overview:** Requests, latency, errors
- **LLM Performance:** Provider comparison, timeouts
- **System Health:** CPU, memory, disk

### Alertas (planejado F9.9-B)

- API down por >1min
- Taxa de erro >5% por 2min
- LLM timeout >50% por 5min

---

## 🔄 Disaster Recovery

### Backup Strategy

**Pre-deploy backups:**
- Antes de cada fase crítica
- Configs: `/etc/nginx/`, `/etc/ssh/`, docker-compose
- Data: PostgreSQL dump, Grafana dashboards
- Retenção: 30 dias

**Restore procedures:**
- Ver: `docs/operations/DISASTER_RECOVERY.md`
- Tempo estimado: 15-20min

---

## 🚀 Deploy e Ambientes

### Produção (VPS)
- **Host:** 72.61.219.157
- **OS:** Ubuntu 24.04 LTS
- **User:** deploy (SSH key only)
- **Stack:** Docker Compose

### Staging (planejado)
- Ambiente isolado para testes pré-produção
- Mesmo stack de produção

### Local Development
- Docker Compose simplificado
- PostgreSQL em container
- LLM mock (sem custos)

---

## 📈 Roadmap Arquitetural

**Fase Atual:** F9.9-B (LLM Hardening)

**Próximas Fases:**
- **F10:** Multi-tenancy e RBAC
- **F11:** Caching layer (Redis)
- **F12:** Async processing (Celery)
- **F13:** Kubernetes migration

Ver: `planning/ROADMAP.md` para detalhes.

---

## 🤝 Decisões Arquiteturais (ADRs)

Decisões importantes documentadas em `docs/architecture/`:

- **ADR-001:** Escolha de FastAPI (performance + type safety)
- **ADR-002:** Multi-provider LLM (vendor lock-in mitigation)
- **ADR-003:** Circuit breaker pattern (resilience)
- **ADR-004:** LGPD by design (privacy guard obrigatório)

---

## 📚 Referências

- **Governança V-COF:** `.github/copilot-instructions.md`
- **Contribuir:** `CONTRIBUTING.md`
- **Estado Atual:** `sessions/consolidation/SEAL-SESSION-*.md`
- **Planejamento:** `planning/ROADMAP.md`

---

**Documento criado:** 2026-01-03  
**Versão:** 1.0  
**Próxima revisão:** Após F9.9-B
