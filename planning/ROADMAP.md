# ROADMAP TÉCNICA — TECHNO OS BACKEND

**Projeto:** Techno OS Backend  
**Governança:** V-COF · Fail-Closed · Human-in-the-Loop  
**Última atualização:** 2026-01-03 (F9.8 em andamento)

---

## 🎯 VISÃO GERAL

Roadmap evolutiva do backend Techno OS, com foco em:
- Governança V-COF rigorosa
- Fail-closed em todas as camadas
- Observabilidade completa
- Privacy by design (LGPD)
- Human-in-the-loop obrigatório

---

## 📊 STATUS ATUAL (2026-01-03)

| Fase | Status | Data Conclusão |
|------|--------|----------------|
| **F9.6.1** | ✅ SELADA | 2026-01-02 |
| **F9.7** | ✅ SELADA | 2026-01-03 |
| **F9.8** | 🔄 EM ANDAMENTO | - |
| **F9.9-A** | 📅 PLANEJADA | - |
| **F9.9-B** | 📅 PLANEJADA | - |
| **F10** | 📅 PLANEJADA | - |

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

## 🔄 FASE ATIVA

### F9.8 — Observabilidade Externa (Prometheus + Grafana)
**Status:** 🔄 EM ANDAMENTO  
**Branch:** `stage/f9.8-observability`

**Escopo:**
- Prometheus para métricas
- Grafana para visualização
- Alertas básicos (uptime, latência)
- Dashboard governado

**Critérios de conclusão:**
- [ ] Prometheus scrapeando `/metrics`
- [ ] Grafana dashboard funcional
- [ ] Alertas configurados
- [ ] Documentação de operação
- [ ] SEAL formal (commit + tag)

**Previsão:** 2-3 dias (dependente de configuração)

---

## 📅 FASES PLANEJADAS

### F9.9-A — Memória Persistente (User Preferences)
**Status:** 📅 PLANEJADA  
**Prioridade:** ALTA (bloqueante para F10)

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
**Status:** 📅 PLANEJADA  
**Prioridade:** CRÍTICA (segurança + governança)

**Contexto:**
- Arquitetura LLM **já existe** (Protocol + executors + adapters)
- Atualmente usa `FakeLLMClient` (mock para testes)
- 5 providers prototipados: OpenAI, Anthropic, Gemini, Grok, DeepSeek
- **NÃO ESTÁ HARDENED** para produção real

**Escopo:**
1. **Factory Pattern Fail-Closed**
   - Provider inválido → ABORT (não fallback silencioso)
   - API key ausente → erro explícito
   - Validação de configuração na inicialização

2. **Normalização de Contratos**
   - Retorno obrigatório: `{"text", "usage", "model", "latency_ms"}`
   - Validação Pydantic de respostas
   - Erros normalizados (`PROVIDER_ERROR`, `TIMEOUT`, `AUTH_ERROR`)

3. **Resiliência**
   - Timeout obrigatório em todas as chamadas
   - Retry apenas para erros transitórios (429, 5xx)
   - Circuit breaker para providers instáveis
   - Nenhum retry para 401/403 (auth)

4. **Testes de Produção**
   - Unit tests de factory com mock
   - Integration tests de cada adapter (mock HTTP)
   - Teste de timeout real
   - Teste de erro de autenticação
   - Smoke test com provider real (staging)

5. **Segurança + Governança**
   - Secrets exclusivamente via `.env`
   - Allowlist explícita de providers habilitados
   - Allowlist explícita de modelos permitidos
   - Sem log de prompts (privacy by design)
   - Rate limiting por provider

6. **Observabilidade LLM**
   - Métricas Prometheus:
     - `llm_request_latency_seconds{provider, model}`
     - `llm_tokens_total{provider, model, type=input|output}`
     - `llm_errors_total{provider, error_type}`
   - Dashboard Grafana dedicado
   - Alertas de falha/latência

**Entregas esperadas:**
- `app/llm/factory.py` hardened
- Testes completos (unit + integration)
- Configuração de um provider padrão (OpenAI recomendado)
- Documentação de deployment
- Runbook de troubleshooting
- SEAL formal

**Dependências:**
- F9.8 concluída (Prometheus disponível para métricas)
- F9.9-A desejável mas não bloqueante

**Riscos identificados:**
- ⚠️ Provider downtime (mitigar com circuit breaker)
- ⚠️ Rate limiting inesperado (mitigar com backoff exponencial)
- ⚠️ Custos de API (mitigar com quotas configuráveis)
- ⚠️ Latência variável (mitigar com timeout agressivo)

**Estimativa:** 3-5 dias (inclui testes extensivos)

---

### F10 — Console / UI (Frontend Integration)
**Status:** 📅 PLANEJADA  
**Prioridade:** MÉDIA (após backend estável)

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
