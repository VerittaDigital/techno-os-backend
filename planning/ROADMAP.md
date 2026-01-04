# ROADMAP TÉCNICA — TECHNO OS BACKEND

**Projeto:** Techno OS Backend  
**Governança:** V-COF · Fail-Closed · Human-in-the-Loop  
**Última atualização:** 2026-01-04 (F9.9-A concluída)

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
| **F9.9-A** | ✅ SELADA | 2026-01-04 |
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

### F9.9-A — Memória Persistente (User Preferences)
**Selada:** 2026-01-04  
**Escopo:**
- Tabela `user_preferences` no PostgreSQL
- Preferências explícitas (tom, formato, idioma)
- API CRUD para preferências (/api/v1/preferences)
- Gate F2.1 com profiles específicos
- Anti-enumeration (user_id validation)
- 12 unit tests + smoke tests VPS

**Entregas:**
- ✅ Model SQLAlchemy (UUID PK, UNIQUE user_id)
- ✅ Schemas Pydantic v2 (regex validation)
- ✅ Migration Alembic (52e2b2a85aec)
- ✅ Endpoints GET/PUT/DELETE com anti-enumeration
- ✅ Gate profiles para preferences.{get|put|delete}
- ✅ 404 tests passing (392 baseline + 12 new)
- ✅ Deployed to VPS com smoke tests validados
- ✅ SEAL documentation (docs/SEAL-F9.9-A.md)

**Commit canônico:** `3ee4e9e`  
**Branch:** `feature/f9.9-a-user-preferences`  
**SEAL:** docs/SEAL-F9.9-A.md

---

## 🔄 FASE ATIVA

### FASE 11 — Gate Engine Consolidation
**Status:** 📅 PRONTA PARA EXECUÇÃO  
**Branch:** `stage/f11-gate-consolidation` (a criar)  
**Prioridade:** 🔴 CRÍTICA (bloqueador de recorrência de falhas)

**Contexto:**
- Incidente real: G8_UNKNOWN_ACTION durante F9.9-A deployment
- Causa raiz: detecção de action não canônica, profiles incompletos, body parsing ambíguo
- Impacto: falhas silenciosas, auditoria inconsistente, experiência degradada

**Objetivo:** Tornar o Gate Engine 100% determinístico e fail-closed.

#### Checklist Executável (10 entregas mínimas)

**1. Canonicalizar Action Detection**
- [ ] Criar `app/gate_engine/action_detector.py` com função única `detect_action(request)`
- [ ] Lógica: `path + method → action` (ex: `/preferences` + PUT → `preferences.put`)
- [ ] Documentar matriz completa (todas rotas ativas → actions válidas)
- [ ] Migrar todas as rotas para usar `action_detector.detect_action()`

**2. Formalizar Body Parsing Rules**
- [ ] Regra GET/DELETE: `body = {}` (não tenta parse JSON)
- [ ] Regra POST/PUT/PATCH: body obrigatório, validação Pydantic
- [ ] Documentar em `docs/gate/BODY_PARSING_RULES.md`
- [ ] Atualizar `gate_request` dependency com lógica canônica

**3. Completar Gate Profiles (1:1 com Action Matrix)**
- [ ] Auditar `action_matrix.py` vs `gate_profiles.py`
- [ ] Criar profiles faltantes (garantir 1:1 mapping)
- [ ] Adicionar testes: `assert get_profile(action) is not None for all actions`

**4. Testes do Gate Engine**
- [ ] Teste: action detection por path/method (matriz de 10+ casos)
- [ ] Teste: GET sem body → não falha
- [ ] Teste: DELETE sem body → não falha
- [ ] Teste: POST sem body → 422 Unprocessable Entity
- [ ] Teste: action inexistente → G8_UNKNOWN_ACTION (fail-closed)
- [ ] Teste: profile ausente → DENY com reason_code estável

**5. Erro Padronizado (Fail-Closed)**
- [ ] Criar `GateError` exception com `reason_code`, `message`, `http_status`
- [ ] Padronizar reason_codes: `G8_UNKNOWN_ACTION`, `G9_MISSING_PROFILE`, `G10_BODY_PARSE_ERROR`
- [ ] Handler centralizado em `main.py` para `GateError`

**6. Auditoria de Gate Decisions**
- [ ] Log estruturado: `{"action", "profile", "decision", "reason_code", "user_id"}`
- [ ] Garantir que todo DENY gera entrada em `audit.log`
- [ ] Teste: DENY → verifica log emitido

**7. Documentação Operacional**
- [ ] `docs/gate/GATE_ENGINE_SPEC.md` (arquitetura + fluxo)
- [ ] `docs/gate/TROUBLESHOOTING.md` (runbook de erros comuns)
- [ ] `docs/gate/ACTION_MATRIX.md` (mapa completo path/method → action)

**8. Smoke Tests (VPS Production)**
- [ ] Smoke test: GET/DELETE preferences sem body → 200/204
- [ ] Smoke test: POST sem body → 422
- [ ] Smoke test: rota não mapeada → 404 + audit log
- [ ] Smoke test: profile ausente → DENY + audit log

**9. Non-Regression**
- [ ] Executar suite completa de testes (deve manter 404+ testes)
- [ ] Validar que nenhuma rota existente quebrou
- [ ] Cobertura de código: gate/ deve ter >90%

**10. SEAL Evidence**
- [ ] Commit final com mensagem: `feat(gate): FASE 11 consolidation - canonical action detection + fail-closed`
- [ ] SEAL document: `docs/SEAL-F11.md` (arquitetura, testes, deployment)
- [ ] Tag: `F11-SEALED`

#### Critérios de SEAL (Fail-Closed)
- ✅ Zero ocorrência de `G8_UNKNOWN_ACTION` em smoke tests
- ✅ Zero ocorrência de body parse error em GET/DELETE
- ✅ Action matrix = gate_profiles = 1:1 (sem lacunas)
- ✅ Teste automatizado detecta lacunas futuras
- ✅ Documentação operacional completa

#### Checkpoints Humanos (4 obrigatórios)
1. **CP-11.1** (após item 3): Revisar matriz de actions vs profiles (aprovação humana)
2. **CP-11.2** (após item 6): Revisar logs de auditoria (sample de 5 decisões)
3. **CP-11.3** (após item 8): Executar smoke tests no VPS (validação humana)
4. **CP-11.4** (final): Revisar SEAL document + aprovar tag

#### Estimativa & Riscos
- **Estimativa:** 1-2 dias (8-16h, inclui testes + deployment)
- **Risco baixo:** trabalho cirúrgico, escopo fechado, sem dependências externas
- **Bloqueadores:** nenhum (trabalho interno ao Gate)

---

### F9.9-B — LLM Hardening (Produção-Ready)
**Status:** 📅 PLANEJADA  
**Branch:** `stage/f9.9-b-llm-hardening` (já existe)  
**Prioridade:** 🔴 CRÍTICA (bloqueador de /plan e /run)

**Contexto:**
- Arquitetura LLM **já existe** (Protocol + executors + adapters)
- Atualmente usa `FakeLLMClient` (mock para testes)
- 5 providers prototipados: OpenAI, Anthropic, Gemini, Grok, DeepSeek
- **NÃO ESTÁ HARDENED** para produção real
- **BLOQUEADOR:** Sem isso, não existe /plan e /run governado

**Objetivo:** LLM fail-closed, determinístico no controle, auditável.

#### Checklist Executável (12 entregas mínimas)

**1. Factory Pattern Fail-Closed**
- [ ] `app/llm/factory.py`: provider inválido → ABORT (não fallback)
- [ ] API key ausente → `LLMConfigError` com reason_code
- [ ] Validação de configuração na inicialização (fail-fast)
- [ ] Teste: provider="invalid" → exception clara

**2. Normalização de Contratos**
- [ ] Schema Pydantic obrigatório: `LLMResponse(text, usage, model, latency_ms)`
- [ ] Validação de resposta: response.text não vazio
- [ ] Erros normalizados: `PROVIDER_ERROR`, `TIMEOUT`, `AUTH_ERROR`, `RATE_LIMIT`
- [ ] Teste: response inválida → exception com reason_code

**3. Timeout Obrigatório**
- [ ] Configurar timeout padrão: 30s (ajustável por provider)
- [ ] Aplicar timeout em TODAS as chamadas HTTP
- [ ] Teste: mock com sleep(60s) → timeout exception
- [ ] Documentar timeout policy em `docs/llm/TIMEOUT_POLICY.md`

**4. Retry Policy (Transitório Only)**
- [ ] Retry apenas para: 429 (rate limit), 500, 502, 503, 504
- [ ] Backoff exponencial: 1s, 2s, 4s (max 3 tentativas)
- [ ] Nenhum retry para: 401, 403, 400, 422 (auth/client errors)
- [ ] Teste: 429 → 3 retries + sucesso
- [ ] Teste: 401 → 0 retries + fail imediato

**5. Circuit Breaker**
- [ ] Implementar circuit breaker: 5 falhas consecutivas → OPEN (30s)
- [ ] Estado OPEN → fail-fast (não tenta chamada)
- [ ] Estado HALF_OPEN → 1 tentativa de teste
- [ ] Teste: 5 falhas → circuit OPEN → fail-fast
- [ ] Métricas: `llm_circuit_breaker_state{provider}`

**6. Secrets Management**
- [ ] Secrets exclusivamente via `.env` (nunca hardcoded)
- [ ] Validar presença de API keys na inicialização
- [ ] Documentar `.env.example` com todas as keys necessárias
- [ ] Teste: API key ausente → erro explícito na startup

**7. Allowlists (Segurança)**
- [ ] Allowlist de providers: `ALLOWED_PROVIDERS=openai,anthropic`
- [ ] Allowlist de modelos: `ALLOWED_MODELS=gpt-4o,claude-sonnet-4`
- [ ] Rejeitar requests fora da allowlist (fail-closed)
- [ ] Teste: provider não permitido → exception

**8. Privacy by Design**
- [ ] Sem log de prompts (apenas metadata)
- [ ] Sem log de respostas completas (apenas length + hash)
- [ ] Log estruturado: `{"provider", "model", "latency_ms", "tokens", "status"}`
- [ ] Auditoria: decisão de chamar LLM + outcome

**9. Rate Limiting por Provider**
- [ ] Configurar rate limit: ex: OpenAI 10 req/min, Anthropic 20 req/min
- [ ] Implementar token bucket ou sliding window
- [ ] Excesso → 429 com `Retry-After` header
- [ ] Teste: 11 requests/min → 429 no 11º

**10. Testes de Produção**
- [ ] Unit tests: factory, retry logic, circuit breaker
- [ ] Integration tests: cada adapter com mock HTTP
- [ ] Teste de timeout real (mock delay)
- [ ] Teste de auth error (mock 401)
- [ ] Smoke test com provider real (staging only, não em CI)

**11. Observabilidade LLM**
- [ ] Métricas Prometheus:
   - `llm_request_latency_seconds{provider, model}`
   - `llm_tokens_total{provider, model, type=input|output}`
   - `llm_errors_total{provider, error_type}`
   - `llm_circuit_breaker_state{provider}`
- [ ] Dashboard Grafana: `LLM Health Dashboard`
- [ ] Alertas: latência >10s, error rate >5%, circuit OPEN

**12. SEAL Evidence**
- [ ] Documentação: `docs/llm/LLM_HARDENING_SPEC.md`
- [ ] Runbook: `docs/llm/TROUBLESHOOTING.md`
- [ ] SEAL document: `docs/SEAL-F9.9-B.md`
- [ ] Tag: `F9.9-B-SEALED`

#### Critérios de SEAL (Fail-Closed)
- ✅ Provider indisponível → ABORT com reason_code claro
- ✅ Rate limit → 429 + Retry-After
- ✅ Timeout → exception + audit log
- ✅ Secrets ausentes → erro na startup (não em runtime)
- ✅ Smoke test com provider real → 100% sucesso
- ✅ Cobertura de testes: llm/ >85%

#### Checkpoints Humanos (5 obrigatórios)
1. **CP-9B.1** (após item 4): Revisar retry policy (aprovar backoff + limites)
2. **CP-9B.2** (após item 7): Revisar allowlists (segurança)
3. **CP-9B.3** (após item 10): Executar smoke test no staging (validação com API real)
4. **CP-9B.4** (após item 11): Revisar dashboard + alertas (observabilidade)
5. **CP-9B.5** (final): Aprovar SEAL + tag

#### Dependências
- F9.8 concluída (Prometheus disponível para métricas) — **RECOMENDADA**
- F11 concluída (Gate estável) — **DESEJÁVEL**

#### Estimativa & Riscos
- **Estimativa:** 2-3 dias (16-24h, inclui testes extensivos)
- **Risco médio:** depende de APIs externas (staging tests)
- **Bloqueadores:** Sem F9.9-B, não existe /plan e /run governado

---

### FASE 15 — Security Hardening (Runtime Protection)
**Status:** 📅 PLANEJADA  
**Branch:** `stage/f15-security-hardening` (a criar)  
**Prioridade:** 🟠 URGENTE (produção exposta)

**Contexto:**
- **Produção atual:** sem rate limiting, sem timeouts configurados, secrets em .env
- **Risco real:** DoS, resource exhaustion, credential leaks
- **Impacto:** downtime, degradação, violação de SLA

**Objetivo:** Garantir que produção aguenta carga e ataque básico.

#### FASE 15.1 — Rate Limiting (por Action)

**Checklist Executável (6 entregas)**

1. **Implementar Rate Limiter**
- [ ] Biblioteca: `slowapi` (compatível com FastAPI)
- [ ] Estratégia: sliding window (1 min)
- [ ] Storage: Redis ou in-memory (configurável)
- [ ] Teste: 100 requests/min → primeiros 50 ok, resto 429

2. **Configurar Limites por Action**
- [ ] `preferences.*`: 100 req/min/user
- [ ] `process.*`: 20 req/min/user (LLM-bound)
- [ ] `plan.*`: 10 req/min/user (intensivo)
- [ ] `run.*`: 5 req/min/user (crítico)
- [ ] Documentar em `docs/security/RATE_LIMITS.md`

3. **Fail-Closed com Reason Code**
- [ ] Excesso → 429 Too Many Requests
- [ ] Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
- [ ] Audit log: decisão de rate limit + user_id
- [ ] Teste: 429 → headers corretos + audit log

4. **Métricas & Observabilidade**
- [ ] Métrica: `http_requests_rate_limited_total{action, user_id}`
- [ ] Dashboard: gráfico de rate limit hits
- [ ] Alerta: rate limit >10 hits/min (possível ataque)

5. **Testes de Carga**
- [ ] Teste: 200 requests em 30s → primeiros 50 ok, resto 429
- [ ] Teste: reset após 1 min → requests voltam a passar
- [ ] Teste: users diferentes → limits isolados

6. **SEAL Evidence**
- [ ] Documentação: `docs/security/RATE_LIMITING_SPEC.md`
- [ ] Commit: `feat(security): FASE 15.1 rate limiting by action`
- [ ] Smoke test no VPS: validar rate limit ativo

**Critérios de SEAL:**
- ✅ Rate limit funcional em produção
- ✅ 429 com headers corretos
- ✅ Teste de carga reproduzível
- ✅ Audit log de rate limit decisions

**Estimativa:** 4-6h

---

#### FASE 15.2 — Timeouts & Payload Limits

**Checklist Executável (7 entregas)**

1. **Request Timeout Global**
- [ ] Configurar: `TIMEOUT_REQUEST=60s` (ajustável por action)
- [ ] Aplicar em todas as rotas via middleware
- [ ] Teste: request com sleep(70s) → 504 Gateway Timeout
- [ ] Documentar em `docs/security/TIMEOUT_POLICY.md`

2. **LLM Timeout (Específico)**
- [ ] Configurar: `TIMEOUT_LLM=30s` (override do global)
- [ ] Aplicar em todas as chamadas LLM
- [ ] Teste: LLM mock com delay(40s) → timeout exception
- [ ] Métrica: `llm_timeout_total{provider}`

3. **Database Timeout**
- [ ] Configurar: `TIMEOUT_DB=10s` (queries longas)
- [ ] Aplicar em SQLAlchemy engine
- [ ] Teste: query com pg_sleep(15) → timeout
- [ ] Alerta: db timeout >5 em 5 min

4. **Payload Size Limit**
- [ ] Limite de body: 1 MB (ajustável)
- [ ] Rejeitar requests >1MB → 413 Payload Too Large
- [ ] Teste: body de 2MB → 413
- [ ] Documentar em `docs/security/PAYLOAD_LIMITS.md`

5. **Content-Type Validation**
- [ ] POST/PUT/PATCH → requer `Content-Type: application/json`
- [ ] Rejeitar outros content-types → 415 Unsupported Media Type
- [ ] Teste: Content-Type: text/plain → 415
- [ ] Documentar content-types permitidos

6. **Header Normalization (Obrigatórios)**
- [ ] `X-API-KEY`: obrigatório (validado pelo Gate)
- [ ] `X-VERITTA-USER-ID`: obrigatório para actions que usam user_id
- [ ] Rejeitar requests sem headers → 400 Bad Request
- [ ] Teste: request sem X-API-KEY → 400 + reason_code

7. **SEAL Evidence**
- [ ] Documentação: `docs/security/RUNTIME_PROTECTION_SPEC.md`
- [ ] Commit: `feat(security): FASE 15.2 timeouts + payload limits`
- [ ] Smoke test no VPS: validar timeouts ativos

**Critérios de SEAL:**
- ✅ Timeout funcional em produção
- ✅ Payload limit bloqueando requests grandes
- ✅ Content-Type validation ativa
- ✅ Headers obrigatórios validados

**Estimativa:** 4-6h

---

**Estimativa Total FASE 15:** 1 dia (8-12h)

**Checkpoints Humanos (3 obrigatórios):**
1. **CP-15.1** (após 15.1 item 2): Revisar limites de rate (aprovação)
2. **CP-15.2** (após 15.2 item 6): Revisar headers obrigatórios (segurança)
3. **CP-15.3** (final): Executar teste de carga no VPS (validação)

---

### F9.8 — Observabilidade Externa (Prometheus + Grafana)
**Status:** 🔄 EM ANDAMENTO  
**Branch:** `stage/f9.8-observability`  
**Prioridade:** 🟡 ALTA (visibilidade de produção)

**Escopo:**
- Prometheus para métricas
- Grafana para visualização
- Alertas básicos (uptime, latência, erros)
- Dashboard governado

**Entregas mínimas (pós F11 + F9.9-B):**

**Métricas por Action:**
- [ ] `http_requests_total{action, status, method}`
- [ ] `http_request_duration_seconds{action}`
- [ ] `gate_decisions_total{action, decision, reason_code}`
- [ ] `llm_requests_total{provider, model}` (F9.9-B)
- [ ] `llm_tokens_total{provider, model, type}` (F9.9-B)

**Dashboards Essenciais:**
- [ ] **Health Dashboard:** uptime, request rate, latency P50/P95/P99
- [ ] **Gate Dashboard:** decisions (ALLOW/DENY), reason_codes, top denied actions
- [ ] **LLM Dashboard:** provider latency, token usage, error rate (F9.9-B)
- [ ] **Errors Dashboard:** 4xx/5xx by action, top errors, spike detection

**Alertas Críticos:**
- [ ] Uptime <99% em 5 min
- [ ] Latência P95 >2s em 5 min
- [ ] Error rate >5% em 5 min
- [ ] G8_UNKNOWN_ACTION detected (gate failure)
- [ ] LLM circuit breaker OPEN (F9.9-B)
- [ ] Rate limit >10 hits/min (FASE 15)

**Critérios de conclusão:**
- [ ] Prometheus scrapeando `/metrics`
- [ ] Grafana 4 dashboards funcionais
- [ ] Alertas configurados + testados
- [ ] Documentação: `docs/observability/DASHBOARDS.md`
- [ ] SEAL formal: `docs/SEAL-F9.8.md`

**Estimativa:** 1-2 dias (ajustado pós F11/F9.9-B)

---

## 🚧 FASES BLOQUEADAS (Requerem Workshop)

### Workshop: Escopo de Operações (pré FASE 12/13/14/17)
**Status:** 📅 PLANEJADA  
**Duração:** 60-90 minutos  
**Objetivo:** Definir sem ambiguidade "Operation", "Plan", "Run", "Artifact"

**Saídas obrigatórias (documento curto):**

1. **Entidades Mínimas**
   - `Operation`: `{id, user_id, status, type, created_at, sealed_at}`
   - `Plan`: `{operation_id, steps[], constraints, created_at}`
   - `Artifact`: `{operation_id, type, path, hash, size, created_at}`

2. **Estados Mínimos (Escopo Reduzido)**
   - FASE 12 inicial: `DRAFT → PLANNED → SEALED` (sem RUNNING)
   - RUNNING só entra depois de F9.9-B selado + validado

3. **Regras de Transição (Fail-Closed)**
   - `DRAFT → PLANNED`: requer plano válido (validação Pydantic)
   - `PLANNED → SEALED`: requer aprovação humana
   - `SEALED → RUNNING`: requer F9.9-B hardened + LLM disponível (FASE 13+)

4. **Storage Strategy (FASE 14)**
   - Decidir: filesystem local? Docker volume? S3? outro?
   - Definir política de retenção (30 dias? 90 dias?)
   - Definir versionamento e hash (SHA-256)

**Decisões bloqueantes:**
- Sem isso, FASE 12 vira "conceito aberto" e explode escopo
- FASE 13 não pode começar sem definição clara de "Run"
- FASE 14 não pode começar sem storage strategy

**Participantes sugeridos:** Tech Lead, Architect, Product Owner

---

### FASE 12 — State Machine Mínima (BLOQUEADA)
**Status:** 🚫 BLOQUEADA (aguarda Workshop)  
**Prioridade:** 🟡 MÉDIA (após F11 + F9.9-B + FASE 15 + Workshop)

**Escopo reduzido (pós Workshop):**
- Persistir `Operation` com transições mínimas: `DRAFT → PLANNED → SEALED`
- Auditoria por transição (quem, quando, de onde, por quê)
- Endpoints somente para criar/consultar/selar estado (sem LLM, sem execução)
- Testes de transição: estados válidos, transições inválidas bloqueadas

**Entregas esperadas:**
- [ ] Model: `app/models/operation.py`
- [ ] Schema: `app/schemas/operation.py`
- [ ] Migration: `alembic revision` para tabela `operations`
- [ ] Endpoints: `/operations` (create, get, list, seal)
- [ ] Testes: transições válidas/inválidas
- [ ] SEAL: `docs/SEAL-F12.md`

**Dependências:**
- Workshop concluído (entidades + estados definidos)
- F11 concluída (Gate estável)
- F9.9-B concluída (se transição SEALED→RUNNING depender de LLM)

**Estimativa:** 1-2 dias (escopo reduzido, sem execução)

---

### FASE 13 — Console Endpoints Mínimos (BLOQUEADA)
**Status:** 🚫 BLOQUEADA (aguarda F9.9-B + Workshop)  
**Prioridade:** 🟡 MÉDIA (após F9.9-B + FASE 12)

**Escopo MVP (pós F9.9-B selado):**
- `/operations` (create, get, list) — **FASE 12 entrega isso**
- `/plan` (create, get) — **requer F9.9-B** para gerar plano com LLM
- `/seal` (seal operação + evidências) — **FASE 12 entrega isso**
- `/artifacts` (index, metadata only) — **aguarda FASE 14**

**Entregas esperadas:**
- [ ] Endpoint: `POST /plan` (gera plano via LLM)
- [ ] Endpoint: `GET /plan/{operation_id}` (retorna plano)
- [ ] Validação: plano válido segundo Pydantic schema
- [ ] Gate profiles para `plan.*` actions
- [ ] Testes: criar plano, get plano, plano inválido → 422
- [ ] SEAL: `docs/SEAL-F13.md`

**Dependências:**
- F9.9-B concluída + selada (LLM hardened)
- FASE 12 concluída (Operation model existe)
- Workshop concluído (definição clara de "Plan")
- F11 concluída (Gate estável)

**Estimativa:** 2-3 dias (MVP mínimo)

---

### FASE 14 — Artifacts Storage (BLOQUEADA)
**Status:** 🚫 BLOQUEADA (aguarda Workshop: storage strategy)  
**Prioridade:** 🟢 BAIXA (após FASE 13)

**Decisões requeridas (Workshop):**
- Onde armazenar? (filesystem VPS? Docker volume? S3?)
- Como versionar? (SHA-256 hash? timestamps?)
- Política de retenção? (30 dias? 90 dias? manual cleanup?)
- Limites de tamanho? (100MB/artifact? 1GB/operation?)

**Escopo esperado (pós decisões):**
- [ ] Model: `app/models/artifact.py`
- [ ] Schema: `app/schemas/artifact.py`
- [ ] Storage abstraction: `app/storage/artifact_store.py`
- [ ] Endpoints: `/artifacts` (upload, get metadata, list, delete)
- [ ] Versionamento: hash SHA-256 + created_at
- [ ] Testes: upload, download, hash verification, cleanup
- [ ] SEAL: `docs/SEAL-F14.md`

**Dependências:**
- Workshop concluído (storage strategy definida)
- FASE 12 concluída (Operation model)
- FASE 13 concluída (se artifacts são gerados por /run)

**Estimativa:** 2-3 dias (inclui storage abstraction + testes)

---

### FASE 17 — Multi-Agents (BLOQUEADA)
**Status:** 🚫 BLOQUEADA (spec arquitetural ausente)  
**Prioridade:** 🟢 BAIXA (longo prazo)

**Pré-requisitos para desbloquear estimativa:**
- Especificação arquitetural: como agentes se comunicam?
- Modelo de isolamento: agentes por user_id? por operation_id?
- Limites e permissões: o que cada agente pode fazer?
- Rastreabilidade: como auditar decisões multi-agent?
- Contrato de execução: síncrono? assíncrono? event-driven?

**Decisões críticas:**
- Arquitetura: monolítica? microserviços? event-driven?
- Orquestração: Celery? RabbitMQ? Kafka? outro?
- State sharing: Redis? PostgreSQL? shared nothing?
- Failure modes: como lidar com agente que falha?

**Sem spec arquitetural, FASE 17 permanece indefinida.**

**Recomendação:** Executar Workshop dedicado após FASE 13 concluída.

---

## 📅 FASES PLANEJADAS (Baixa Prioridade)

### F10 — Console / UI (Frontend Integration)
**Status:** 📅 PLANEJADA  
**Prioridade:** 🟢 BAIXA (após backend estável)

**Escopo:**
- Integrar Console (Next.js) com API
- Chat interface básica
- Consumo de endpoints `/process`, `/preferences`
- Exibição de respostas LLM

**Dependências:**
- F9.9-A concluída (preferências disponíveis) — ✅ DONE
- F9.9-B concluída (LLM estável) — ⏳ PENDENTE
- FASE 13 concluída (endpoints disponíveis) — ⏳ PENDENTE
- Console (techno-os-console) atualizado

**Estimativa:** 3-5 dias

---

## 🚨 RISCOS E DECISÕES ESTRATÉGICAS

### Sequência Recomendada (Curto Prazo Realista)

**CRÍTICO (1-3 dias):**
1. ✅ **FASE 11** (Gate consolidation) — 1-2 dias
2. ✅ **F9.9-B** (LLM Hardening) — 2-3 dias
3. ✅ **FASE 15.1-15.2** (rate limit + timeout) — 1 dia

**IMPORTANTE (3-5 dias):**
4. ⏳ **F9.8** (Observabilidade) — 1-2 dias
5. ⏳ **Workshop** (Escopo Operations) — 90 minutos

**MÉDIO PRAZO (5-10 dias):**
6. ⏳ **FASE 12** (State Machine reduzida) — 1-2 dias
7. ⏳ **FASE 13.1** (Endpoints mínimos) — 2-3 dias

**LONGO PRAZO (>10 dias):**
8. ⏳ **FASE 14** (Artifacts) — 2-3 dias
9. ⏳ **F10** (Console UI) — 3-5 dias
10. ⏳ **FASE 17** (Multi-Agents) — indefinido (spec ausente)

---

### Riscos Críticos Identificados

#### Risco 1: Gate Failures (ALTO → MITIGADO)
**Descrição:** Incidentes recorrentes de G8_UNKNOWN_ACTION, body parsing errors.  
**Impacto:** Falhas silenciosas, auditoria inconsistente, experiência degradada.  
**Mitigação:** FASE 11 (Gate consolidation) — prioridade crítica.  
**Status:** 📅 PRONTA PARA EXECUÇÃO

#### Risco 2: LLM em Produção (CRÍTICO)
**Descrição:** Arquitetura LLM existe mas não está hardened.  
**Impacto:** Falhas silenciosas, custos imprevisíveis, indisponibilidade, dados expostos.  
**Mitigação:** F9.9-B (LLM Hardening) antes de qualquer /plan ou /run.  
**Status:** 🚫 BLOQUEADOR de FASE 13

#### Risco 3: Runtime Vulnerabilities (URGENTE)
**Descrição:** Produção sem rate limiting, sem timeouts, secrets em plaintext.  
**Impacto:** DoS, resource exhaustion, credential leaks, downtime.  
**Mitigação:** FASE 15.1-15.2 (rate limit + timeout + payload limits).  
**Status:** 🟠 URGENTE (produção exposta)

#### Risco 4: Observabilidade Limitada (MÉDIO)
**Descrição:** Métricas de negócio ausentes, alertas incompletos.  
**Impacto:** Diagnóstico lento de incidentes, blind spots em produção.  
**Mitigação:** F9.8 (Prometheus + Grafana) com métricas de Gate + LLM.  
**Status:** 🔄 EM ANDAMENTO

#### Risco 5: Escopo Indefinido (ALTO)
**Descrição:** "Operation", "Plan", "Run" não têm definição clara.  
**Impacto:** FASE 12/13/14/17 explodem em escopo, retrabalho massivo.  
**Mitigação:** Workshop obrigatório (60-90 min) antes de iniciar FASE 12.  
**Status:** 🚫 BLOQUEADOR de FASE 12/13/14/17

#### Risco 6: Storage Strategy Ausente (MÉDIO)
**Descrição:** FASE 14 sem definição de onde/como armazenar artifacts.  
**Impacto:** Decisões ad-hoc, refactoring futuro, risco operacional.  
**Mitigação:** Decidir em Workshop (filesystem? S3? volume?).  
**Status:** 🚫 BLOQUEADOR de FASE 14

#### Risco 7: Multi-Agents sem Spec (BAIXO)
**Descrição:** FASE 17 proposta sem arquitetura definida.  
**Impacto:** Estimativa impossível, escopo aberto, risco de overengineering.  
**Mitigação:** Workshop dedicado após FASE 13 (não urgente).  
**Status:** 🟢 LONGO PRAZO (não crítico)

---

## 🔐 GOVERNANÇA E DECISÕES

### Princípios Invariantes
1. **Fail-closed:** Erro → bloqueio explícito (não fallback silencioso)
2. **Human-in-the-loop:** Decisões críticas exigem confirmação humana
3. **Privacy by design:** Sem log de dados sensíveis (LGPD)
4. **Separação de responsabilidades:** Backend ≠ Frontend ≠ LLM ≠ Storage
5. **Memória dignificada:** Apenas preferências explícitas (F9.9-A implementado)
6. **Evidence-based:** Toda fase exige SEAL com evidências completas
7. **Checkpoints obrigatórios:** Revisão humana em pontos críticos

### Decisões de Roadmap
- **FASE 11 antes de tudo:** Gate estável = fundação de governança
- **F9.9-B obrigatória:** Não /plan ou /run sem LLM hardened
- **FASE 15 urgente:** Produção não pode ficar exposta (DoS risk)
- **Workshop obrigatório:** Sem definir "Operation", FASE 12/13 não começam
- **Um provider por vez:** OpenAI como padrão inicial (F9.9-B)
- **Observabilidade primeiro:** Métricas antes de features complexas
- **Escopo reduzido:** MVP mínimo sempre (fail-closed > feature-rich)

### Bloqueadores Críticos
- 🚫 **FASE 12/13/14/17:** Bloqueadas até Workshop (escopo indefinido)
- 🚫 **FASE 13:** Bloqueada até F9.9-B selada (LLM hardened)
- 🚫 **FASE 14:** Bloqueada até storage strategy definida
- 🚫 **FASE 17:** Bloqueada até spec arquitetural (longo prazo)

---

## 📚 REFERÊNCIAS

- Copilot Instructions: `.github/copilot-instructions.md`
- LLM Integration Guide: `docs/LLM_INTEGRATION_GUIDE.md`
- SEAL F9.7: `docs/SEAL-F9.7.md`
- SEAL F9.9-A: `docs/SEAL-F9.9-A.md`
- Parecer Técnico F10-F17: `docs/audits/PARECER-TECNICO-ROADMAP-F10-F17.md`
- V-COF Principles: Documentação interna Verittà

---

**Última revisão:** 2026-01-04  
**Revisores:** Vinícius Soares de Souza (Tech Lead) + Claude Sonnet 4.5 (Technical Auditor)  
**Próxima revisão:** Após FASE 11 concluída  
**Próxima revisão:** Após conclusão de F9.8
