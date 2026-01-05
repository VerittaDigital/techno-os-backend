# ROADMAP TÉCNICA — TECHNO OS BACKEND

**Projeto:** Techno OS Backend  
**Governança:** V-COF · Fail-Closed · Human-in-the-Loop  
**Última atualização:** 2026-01-05 (F9.11 SEALED, F9.9-B revalidado)

---

## 🎯 VISÃO GERAL

Roadmap evolutiva do backend Techno OS, com foco em:
- Governança V-COF rigorosa
- Fail-closed em todas as camadas
- Observabilidade completa
- Privacy by design (LGPD)
- Human-in-the-loop obrigatório

---

## 📊 STATUS ATUAL (2026-01-05)

| Fase | Status | Data Conclusão | Tag |
|------|--------|----------------|-----|
| **F9.6.1** | ✅ SELADA | 2026-01-02 | F9.6.1-SEALED |
| **F9.7** | ✅ SELADA | 2026-01-03 | - |
| **F9.9-A** | ✅ SELADA | 2026-01-04 | F9.9-A-SEALED |
| **F9.9-B** | ✅ SELADA | 2026-01-04 | F9.9-B-SEALED |
| **F9.9-C** | ✅ SELADA | 2026-01-04 | F9.9-C-SEALED |
| **F9.10** | ✅ SELADA | 2026-01-04 | F9.10-SEALED |
| **F9.11** | ✅ SELADA | 2026-01-05 | F9.11-SEALED |
| **F10** | 📅 PRÓXIMA | - | - |

---

## ✅ FASES CONCLUÍDAS

### F9.6.1 — CI/CD Minimal
**Selada:** 2026-01-02  
**Escopo:**
- Estrutura de testes (pytest)
- Linting básico (flake8/black)
- GitHub Actions workflow mínimo
- Tag canônico: `F9.6.1-SEALED`

**Entregas:**
- ✅ Pipeline CI funcional
- ✅ Testes automatizados
- ✅ Code quality gates

---

### F9.7 — Produção Controlada (Nginx + TLS)
**Selada:** 2026-01-03  
**Escopo:**
- Deployment em VPS (Ubuntu 24.04)
- Nginx reverse proxy
- TLS via Let's Encrypt (produção real)
- Health checks automatizados

**Entregas:**
- ✅ API pública: https://api.verittadigital.com
- ✅ Certificado ECDSA válido (expira 2026-04-03)
- ✅ Renovação automática configurada
- ✅ Fail-closed em todos os scripts
- ✅ Artifacts de deployment persistidos

**Commit canônico:** `cd7fcc8`

---

## ✅ FASES RECÉM CONCLUÍDAS

### F9.9-A — Memória Persistente (User Preferences)
**Selada:** 2026-01-04  
**Tag:** `F9.9-A-SEALED`  
**Status:** ✅ CONCLUÍDA E OPERACIONAL

**Escopo:**
- Tabela `user_preferences` no PostgreSQL
- Preferências explícitas (tom, formato, idioma)
- API CRUD para preferências
- Sem inferência psicológica (conforme V-COF Princípio 5)

**Entregas esperadas:**
- Modelo SQLAlchemy para preferences
- Endpoints `/preferences` (GET/PUT)
- Testes de persistência
- Migração de schema
- Documentação de uso

**Dependências:**
- F9.8 concluída (observabilidade estável)

**Estimativa:** 2-3 dias

---

### F9.9-B — LLM Hardening (Produção-Ready)
**Selada:** 2026-01-04  
**Tag:** `F9.9-B-SEALED`  
**Status:** ✅ CONCLUÍDA (17/17 testes PASS)

**Implementado:**
- Factory Pattern Fail-Closed com allowlist obrigatória
- LLMResponse Pydantic normalizado (text, usage, model, latency_ms)
- Retry automático (max 2, exponential backoff, apenas 429/5xx)
- Circuit breaker thread-safe (CLOSED/OPEN/HALF_OPEN)
- 3 métricas Prometheus (latency, tokens, errors)
- Zero logs de PII (privacy by design)

### F9.9-C — Integration + Observability
**Selada:** 2026-01-04  
**Tag:** `F9.9-C-SEALED`  
**Status:** ✅ CONCLUÍDA

**Implementado:**
- Circuit breaker singleton integrado ao LLM executor
- Retry policy aplicado a todas as chamadas LLM
- Observabilidade de circuit breaker (estado, contadores)
- Tests suite (8 cenários, 100% pass)

---

### F9.10 — Observability Containerization
**Selada:** 2026-01-04  
**Tag:** `F9.10-SEALED`  
**Status:** ✅ DEPLOYADA EM PRODUÇÃO

**Implementado:**
- Prometheus containerizado (docker-compose)
- Alertmanager containerizado (console mode)
- 5 alert rules governadas (LLM + API health)
- Backup automation (3 volumes: postgres, prometheus, grafana)
- Circuit breaker ENV configurável (VERITTA_CB_THRESHOLD, VERITTA_CB_TIMEOUT)
- Dashboard Grafana (4 painéis LLM metrics)

**Containers rodando no VPS:**
- techno-os-prometheus:9090
- techno-os-alertmanager:9093
- techno-os-grafana:3000

---

### F9.11 — Alerting Governance
**Selada:** 2026-01-05  
**Tag:** `F9.11-SEALED`  
**Status:** ✅ OPERACIONAL EM PRODUÇÃO

**Implementado:**
- Runbook operacional (docs/RUNBOOK_ALERTING.md)
- Steady-state validation (5min, 0 FIRING alerts)
- Test alert + silence (F9_11_TEST_ALERT)
- Evidence pack completo (19 arquivos)
- Remote validation via SSH (fail-closed)

---

## 📅 PRÓXIMAS FASES

### F10 — Console / UI (Frontend Integration)
**Status:** 📅 PRÓXIMA FASE  
**Prioridade:** ALTA (UX completa)

**Dependências satisfeitas:**
- ✅ F9.9-A (User Preferences) — API /preferences operacional
- ✅ F9.9-B (LLM Hardening) — Factory fail-closed + retry + circuit breaker
- ✅ F9.10 (Observability) — Métricas + alerts + dashboard
- ✅ F9.11 (Alerting) — Runbook + steady-state

**Escopo:**
- Integrar Console (Next.js) com API
- Chat interface básica
- Consumo de endpoints `/process`, `/preferences`
- Exibição de respostas LLM

**Dependências:**
- F9.9-A concluída (preferências disponíveis)
- F9.9-B concluída (LLM estável)
- Console (techno-os-console) atualizado

**Estimativa:** 5-7 dias

---

## 🚨 RISCOS E PENDÊNCIAS

### Risco 1: LLM em Produção (ALTO)
**Descrição:** Arquitetura LLM existe mas não está hardened.  
**Impacto:** Falhas silenciosas, custos imprevisíveis, indisponibilidade.  
**Mitigação:** Executar F9.9-B antes de F10.  
**Status:** 📅 Planejada (F9.9-B)

### Risco 2: Memória Efêmera (MÉDIO)
**Descrição:** Sessões não persistem preferências entre logins.  
**Impacto:** UX degradada, perda de contexto.  
**Mitigação:** Executar F9.9-A.  
**Status:** 📅 Planejada (F9.9-A)

### Risco 3: Observabilidade Incompleta (BAIXO)
**Descrição:** Métricas de negócio ainda ausentes.  
**Impacto:** Diagnóstico lento de incidentes.  
**Mitigação:** F9.8 em andamento.  
**Status:** 🔄 Em andamento

---

## 🔐 GOVERNANÇA E DECISÕES

### Princípios Invariantes
1. **Fail-closed:** Erro → bloqueio explícito (não fallback silencioso)
2. **Human-in-the-loop:** Decisões críticas exigem confirmação humana
3. **Privacy by design:** Sem log de dados sensíveis (LGPD)
4. **Separação de responsabilidades:** Backend ≠ Frontend ≠ LLM
5. **Memória dignificada:** Apenas preferências explícitas

### Decisões de Roadmap
- **F9.9-A antes de F10:** Console precisa de preferências persistentes
- **F9.9-B obrigatória:** Não ir para produção com LLM mock
- **Um provider por vez:** OpenAI como padrão inicial
- **Observabilidade primeiro:** Métricas antes de features

---

## 📚 REFERÊNCIAS

- Copilot Instructions: `.github/copilot-instructions.md`
- LLM Integration Guide: `docs/LLM_INTEGRATION_GUIDE.md`
- SEAL F9.7: `docs/SEAL-F9.7.md`
- V-COF Principles: Documentação interna Verittà

---

**Última revisão:** 2026-01-03  
**Revisores:** Vinícius Soares de Souza (Tech Lead)  
**Próxima revisão:** Após conclusão de F9.8
