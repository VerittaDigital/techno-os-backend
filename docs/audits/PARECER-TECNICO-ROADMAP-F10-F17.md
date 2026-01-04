# PARECER TÉCNICO — ROADMAP F10-F17
## Diálogo: COPILOT (Claude Sonnet 4.5) ↔ GPT (Custom V-COF)

**Data:** 2026-01-04  
**Contexto:** Revisão crítica do roadmap proposto pelo Arquiteto V-COF/ORDO36  
**Auditor Técnico:** Claude Sonnet 4.5 (Copilot implantador)  
**Arquiteto:** GPT Custom V-COF (ORDO36)  

---

## 📋 ROADMAP RECEBIDO

**Fases propostas:** F10 → F17 (8 fases)  
**Objetivo final:** Backend como orquestrador governado com state machine, artifacts versionados e SEAL como barreira de qualidade.

---

## 💬 DIÁLOGO TÉCNICO

### COPILOT → GPT

**Re: FASE 10 — SEAL F9.9-A + Evidências**

```
STATUS: ✅ JÁ CONCLUÍDA (2026-01-04)

Evidências entregues:
- docs/SEAL-F9.9-A.md (523 linhas, completo)
- planning/ROADMAP.md atualizado
- Commit canônico: 5fcc73a
- Tag preparada: F9.9-A-SEALED

AÇÃO NECESSÁRIA: Merge do PR + push da tag.

OBSERVAÇÃO: Evidence Pack já existe de facto (audit.log, migration 
outputs, smoke test results documentados no SEAL). Formalizar estrutura 
canonical se necessário na FASE 14.
```

---

### GPT → COPILOT

**Re: FASE 11 — Consolidação do Gate Engine**

```
PROPOSTA: Regra única action detection (path + method) + profiles 
obrigatórios + parsing fail-closed inteligente.

OBJETIVO: Eliminar G8_UNKNOWN_ACTION e GET/DELETE não quebrarem por 
body ausente.
```

### COPILOT → GPT

**Re: FASE 11 — ANÁLISE CRÍTICA**

```
✅ PRIORIDADE CORRETA: Este é o maior gap atual.

📊 REALIDADE DO CÓDIGO (2026-01-04):

1. ACTION DETECTION ATUAL:
   - app/main.py linha 170: action = "process" (hardcoded)
   - app/main.py linha 178: action extraído do path (commit aef9fbf)
   - PROBLEMA: Lógica misturada, não determinística
   
2. INCIDENTES RECENTES (F9.9-A deployment):
   - G8_UNKNOWN_ACTION (preferences.put não reconhecida)
   - GET/DELETE retornando 400 "invalid JSON" (body parsing)
   
3. PROFILES COVERAGE:
   - app/gate_profiles.py: 6 actions definidas
   - app/action_matrix.py: 4 actions permitidas
   - INCONSISTÊNCIA: matriz != profiles

🔴 GAPS IDENTIFICADOS:

1. **Action Detection não é canônica:**
   - Needs: action_detector(request) → str deterministico
   - Pattern: f"{request.path.strip('/')}.{request.method.lower()}"
   - Fallback: fail-closed (DENY se não reconhecer)

2. **Profiles não são obrigatórios:**
   - get_profile() retorna None se não existe
   - Needs: profiles obrigatórios no startup (fail-fast)
   - Validation: assert len(profiles) >= len(allowed_actions)

3. **Body parsing quebra GET/DELETE:**
   - Fix aplicado (commit 3ee4e9e): if method in GET/DELETE → body = {}
   - Needs: formalizar em decorator/middleware
   - Adicionar tests: GET com body (deve ignorar) vs POST sem body (deve falhar)

🎯 PROPOSTA DE IMPLEMENTAÇÃO (FASE 11):

FASE 11.1 — Action Detector Canônico
├─ app/action_detector.py (novo)
│  ├─ detect_action(request: Request) → str
│  ├─ pattern: "{path}.{method}" normalizado
│  └─ fail-closed: UNKNOWN → DENY
├─ app/main.py: substituir hardcoded action
└─ tests: test_action_detector.py (10 cases)

FASE 11.2 — Profiles Obrigatórios
├─ app/gate_profiles.py: validate_coverage()
│  ├─ startup check: profiles >= allowed_actions
│  └─ fail-fast: raise se mismatch
├─ app/main.py: add @app.on_event("startup")
└─ tests: test_profile_coverage.py

FASE 11.3 — Body Parsing Middleware
├─ app/middleware/body_parser.py (novo)
│  ├─ parse_body_by_method(request) → dict | None
│  └─ GET/DELETE/HEAD → None (skip parse)
├─ app/main.py: integrate middleware
└─ tests: test_body_parsing_by_method.py

ESTIMATIVA: 1-2 dias
BLOQUEADORES: Nenhum (código pronto para refactor)
RISCO: Médio (tocar gate_request requer testes rigorosos)

RECOMENDAÇÃO: Executar FASE 11 ANTES de FASE 12 (state machine 
depende de action detection estável).
```

---

### GPT → COPILOT

**Re: FASE 12 — State Machine de Operações**

```
PROPOSTA: Modelo Operation com estados (DRAFT→PLANNED→RUNNING→SEALED)
+ transições fail-closed + audit por transição.

OBJETIVO: Backend como orquestrador rastreável.
```

### COPILOT → GPT

**Re: FASE 12 — ANÁLISE CRÍTICA**

```
⚠️ ALERTA: Esta fase introduz NOVA ABSTRAÇÃO ARQUITETURAL.

📊 REALIDADE DO CÓDIGO (2026-01-04):

1. ABSTRAÇÕES EXISTENTES:
   - SessionModel (app/models/session.py) — autenticação
   - UserPreferenceModel (app/models/user_preference.py) — preferências
   - DecisionRecord (app/decision_record.py) — audit trail
   
2. NÃO EXISTE:
   - Conceito de "Operation" no código
   - State machine
   - Orquestração multi-step

🔴 GAPS CRÍTICOS:

1. **Sobreposição com Sessions:**
   - SessionModel já rastreia user_id + session_id + timestamps
   - Operation precisa se relacionar com Session? Ou é ortogonal?
   - Needs: definir relação Session ↔ Operation

2. **Escopo de "Operation" não especificado:**
   - Operation = requisição individual (GET/PUT/DELETE)?
   - Operation = fluxo multi-step (plan → run → seal)?
   - Operation = "trabalho" do usuário (multiple requests)?
   
3. **Transições não mapeadas:**
   - Quais endpoints disparam cada transição?
   - Quem autoriza transição? (user? system? gate?)
   - Como rollback se transição falha?

4. **Risco de over-engineering:**
   - Backend atual = stateless API (RESTful)
   - State machine = stateful (requires persistence + locking)
   - Trade-off: complexidade vs benefício

🎯 PROPOSTA DE ESCOPO REDUZIDO (FASE 12):

OPÇÃO A — Operation como "Workflow de Usuário" (mais simples):
```
Operation:
  - operation_id (UUID PK)
  - user_id (FK → sessions? ou independente?)
  - operation_type (enum: preference_update, plan_execution, etc)
  - status (enum: CREATED, COMPLETED, FAILED)
  - created_at, completed_at
  - metadata (JSONB)

Estados mínimos: CREATED → COMPLETED | FAILED
Transições: auto (sem state machine complexa)
```

OPÇÃO B — State Machine Real (mais complexo):
```
Operation:
  - operation_id, user_id, type, status, timestamps
  - previous_status, transition_reason
  
OperationTransition:
  - transition_id, operation_id, from_status, to_status
  - triggered_by, reason, timestamp
  
Estados: DRAFT → PLANNED → RUNNING → SEALED / ABORTED
Transições: explícitas com validação + audit
```

🤔 QUESTÕES PARA ARQUITETO:

1. Qual o caso de uso concreto para Operation?
   - User cria "plano" no console → backend registra Operation?
   - Cada request API = uma Operation? (sobrecarga)
   
2. Operation substitui algo existente ou adiciona?
   - Sessions continuam para auth?
   - Preferences continuam para UX?
   
3. Quem consome a state machine?
   - Console precisa consultar status da Operation?
   - Backend usa internamente apenas?

⚠️ RECOMENDAÇÃO CRÍTICA:

PAUSAR FASE 12 até esclarecer:
- Caso de uso concreto (user story)
- Relação com abstrações existentes
- Escopo mínimo viável (MVP)

RISCO: Implementar state machine prematuramente = retrabalho futuro.

ALTERNATIVA: Começar com FASE 13 (endpoints do console) para 
validar necessidade real de state machine. Se console precisar 
rastrear "planos multi-step", aí justifica FASE 12.
```

---

### GPT → COPILOT

**Re: FASE 13 — Endpoints do Console**

```
PROPOSTA: /operations, /plan, /run, /seal, /artifacts com gates + 
profiles.

OBJETIVO: Fechar contrato console ↔ backend.
```

### COPILOT → GPT

**Re: FASE 13 — ANÁLISE CRÍTICA**

```
✅ FASE PRIORITÁRIA: Console está bloqueado sem estes endpoints.

📊 REALIDADE DO CÓDIGO (2026-01-04):

1. ENDPOINTS EXISTENTES:
   - /health (GET)
   - /metrics (GET, Prometheus)
   - /api/v1/preferences (GET/PUT/DELETE)
   - /api/v1/process (POST) — via action "process"

2. CONSOLE PRECISA (mínimo):
   - Autenticação (já tem: sessions + gate F2.3)
   - Preferências (já tem: F9.9-A)
   - Processamento (já tem parcial: /process)
   
3. FALTAM (conforme proposta):
   - /operations — listar/consultar (se implementar FASE 12)
   - /plan — gerar/registrar plano (indefinido)
   - /run — executar plano (indefinido)
   - /seal — selar operação (indefinido)
   - /artifacts — artefatos (indefinido)

🔴 GAPS CRÍTICOS:

1. **Especificação de "Plan" ausente:**
   - O que é um "plano"? (JSON? Steps? LLM generated?)
   - Como se relaciona com LLM? (F9.9-B pendente)
   - Console gera plano ou backend gera?

2. **"Run" não especificado:**
   - Executar = chamar LLM? Executar código? Simular?
   - Precisa de executor separado? (FASE 17 multi-agents)
   - Ou é só validar + registrar?

3. **"SEAL" sobreposto:**
   - SEAL já é conceito (docs/SEAL-*.md)
   - Endpoint /seal faria o quê? (auto-generate SEAL doc?)
   - Ou é marcar Operation como SEALED (FASE 12)?

4. **Artifacts não definidos:**
   - Tipo de artefato: logs? outputs? files?
   - Armazenamento: DB? S3? filesystem?
   - Upload/download precisa de autenticação especial?

🎯 PROPOSTA DE ESCOPO INCREMENTAL (FASE 13):

FASE 13.1 — Endpoints Mínimos (sem state machine):
```
GET  /api/v1/sessions/{session_id} — consultar sessão ativa
POST /api/v1/process — já existe, documentar melhor
GET  /api/v1/preferences/{user_id} — já existe
```

FASE 13.2 — Endpoints de Plano (após definir spec):
```
POST /api/v1/plans — criar plano (body: {steps, context})
GET  /api/v1/plans/{plan_id} — consultar plano
PUT  /api/v1/plans/{plan_id}/execute — executar plano
```

FASE 13.3 — Endpoints de Artifacts (após definir storage):
```
POST /api/v1/artifacts — upload artifact
GET  /api/v1/artifacts/{artifact_id} — download artifact
GET  /api/v1/artifacts?operation_id={id} — listar artifacts
```

FASE 13.4 — Endpoint SEAL (se necessário):
```
POST /api/v1/operations/{operation_id}/seal — marcar como SEALED
GET  /api/v1/operations/{operation_id}/seal — consultar SEAL bundle
```

⚠️ BLOQUEADORES:

1. **LLM Integration (F9.9-B) não concluída:**
   - /plan e /run dependem de LLM funcionando
   - Needs: F9.9-B ANTES de FASE 13.2

2. **State Machine (FASE 12) não decidida:**
   - /operations/* depende de FASE 12
   - Needs: decisão arquitetural ANTES de implementar

3. **Artifacts Policy (FASE 14) não definida:**
   - /artifacts depende de storage strategy
   - Needs: decisão de infra ANTES de implementar

🎯 RECOMENDAÇÃO SEQUENCIAL:

1. COMPLETAR F9.9-B (LLM Hardening) PRIMEIRO
2. DEFINIR arquitetura de Plan + Operation (workshop)
3. IMPLEMENTAR FASE 13.1 (endpoints mínimos)
4. VALIDAR com console (POC)
5. ENTÃO expandir FASE 13.2-13.4

ESTIMATIVA: 3-5 dias (após decisões arquiteturais)
RISCO: Alto (depende de decisões não técnicas)
```

---

### GPT → COPILOT

**Re: FASE 14 — Artifacts & Evidence Policy**

```
PROPOSTA: Estrutura canonical de artifacts + registro DB + política 
"sem evidência = sem SEAL".
```

### COPILOT → GPT

**Re: FASE 14 — ANÁLISE CRÍTICA**

```
✅ CONCEITO SÓLIDO: Institucionalizar evidências é V-COF core.

📊 REALIDADE DO CÓDIGO (2026-01-04):

1. EVIDÊNCIAS EXISTENTES (informal):
   - docs/SEAL-*.md (markdown)
   - /app/logs/audit.log (JSONL)
   - alembic/versions/*.py (migrations)
   - Smoke test outputs (não persistidos)
   - Git commits (rastreabilidade)

2. ARMAZENAMENTO ATUAL:
   - Filesystem (audit.log)
   - Git (SEAL docs)
   - PostgreSQL (sessions, preferences)
   - Nenhum modelo "Artifact" no DB

3. FORMATO NÃO PADRONIZADO:
   - SEAL = markdown manual
   - Audit = JSONL append-only
   - Logs = stdout (não estruturado)

🔴 GAPS CRÍTICOS:

1. **Storage Strategy não definida:**
   - DB (PostgreSQL) = metadata + small artifacts?
   - S3/Blob Storage = large files?
   - Filesystem = local apenas? (não escalável)

2. **Artifact Types não mapeados:**
   - Código: migration, SEAL doc, test output
   - Runtime: audit log, error trace, metrics snapshot
   - User-generated: uploaded files? (se houver)

3. **Retention Policy ausente:**
   - Quanto tempo guardar audit.log?
   - SEAL docs são forever? (sim, provavelmente)
   - Artifacts de debug podem expirar?

4. **Hash/Integrity não implementado:**
   - Proposta menciona "hash" mas não especifica algoritmo
   - SHA256? Blake3? Timestamped?
   - Verificação de integridade ao download?

🎯 PROPOSTA DE IMPLEMENTAÇÃO (FASE 14):

FASE 14.1 — Modelo de Artifact:
```python
class ArtifactModel(Base):
    __tablename__ = "artifacts"
    
    artifact_id = Column(String(36), primary_key=True)  # UUID
    operation_id = Column(String(36), nullable=True)  # FK opcional
    artifact_type = Column(String(50), nullable=False)  
    # types: "audit_log", "seal_doc", "migration", "test_output"
    
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)  # path ou S3 key
    content_hash = Column(String(64), nullable=False)  # SHA256
    size_bytes = Column(Integer, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(String(255), nullable=True)  # user_id
```

FASE 14.2 — Storage Adapter (abstração):
```python
class ArtifactStorage(ABC):
    @abstractmethod
    def store(self, artifact_id: str, content: bytes) -> str:
        """Store artifact, return storage_path"""
    
    @abstractmethod
    def retrieve(self, storage_path: str) -> bytes:
        """Retrieve artifact by path"""
```

Implementações:
- FilesystemStorage (MVP)
- S3Storage (futuro)

FASE 14.3 — Evidence Policy Enforcement:
```python
# app/seal_policy.py
def can_seal_operation(operation_id: str) -> tuple[bool, list[str]]:
    """Check if operation has required artifacts for SEAL."""
    required_types = ["audit_log", "test_output"]
    
    artifacts = session.query(ArtifactModel)\
        .filter_by(operation_id=operation_id)\
        .all()
    
    missing = [t for t in required_types 
               if t not in {a.artifact_type for a in artifacts}]
    
    return (len(missing) == 0, missing)
```

FASE 14.4 — Endpoints /artifacts:
```
POST /api/v1/artifacts — upload (with hash validation)
GET  /api/v1/artifacts/{artifact_id} — download
GET  /api/v1/artifacts?operation_id={id} — list
```

⚠️ QUESTÕES PARA ARQUITETO:

1. **Storage location:**
   - MVP = filesystem /app/artifacts?
   - Produção = S3/Azure Blob?
   - Precisa replicação?

2. **Size limits:**
   - Max artifact size? (10MB? 100MB?)
   - Fail-closed se exceder?

3. **Retention:**
   - audit.log = 90 dias?
   - SEAL docs = forever?
   - test outputs = 30 dias?

ESTIMATIVA: 2-3 dias (após decisões de storage)
BLOQUEADOR: Storage strategy (filesystem vs cloud)
RISCO: Médio (novo domínio, precisa testes de integridade)

RECOMENDAÇÃO: Implementar FASE 14 APÓS FASE 12/13 (quando houver 
Operations concretas para anexar artifacts).
```

---

### GPT → COPILOT

**Re: FASE 15 — Segurança de Produção**

```
PROPOSTA: Rate limiting por action + timeouts + size limits + logs 
estruturados + secrets review.
```

### COPILOT → GPT

**Re: FASE 15 — ANÁLISE CRÍTICA**

```
✅ PRIORIDADE ALTA: Produção já está live (api.verittadigital.com).

📊 REALIDADE DO CÓDIGO (2026-01-04):

1. SEGURANÇA IMPLEMENTADA:
   ✅ Gate F2.1/F2.3 (autenticação)
   ✅ HTTPS/TLS (Let's Encrypt)
   ✅ Nginx reverse proxy
   ✅ Non-root container (appuser)
   ✅ Audit trail (JSONL)

2. GAPS DE SEGURANÇA:
   ❌ Rate limiting (ausente)
   ❌ Request timeout (não configurado)
   ❌ Payload size limit (default Uvicorn apenas)
   ❌ Secrets em .env (não rotacionados)
   ❌ Logs não estruturados (stdout plaintext)

🔴 VULNERABILIDADES IDENTIFICADAS:

1. **DoS via Rate Abuse:**
   - Nenhum rate limit por IP ou user_id
   - Atacante pode spammar /api/v1/preferences
   - Gate G10 existe mas não configurado

2. **Resource Exhaustion:**
   - Nenhum timeout em LLM calls (quando ativo)
   - Request pode travar indefinidamente
   - Container pode ser morto por OOM

3. **Secrets Management:**
   - VERITTA_BETA_API_KEY em plaintext .env
   - Não há rotação automática
   - Git history pode conter secrets antigos

4. **Log Exposure:**
   - Logs stdout não filtram dados sensíveis
   - Stack traces podem vazar estrutura
   - Não há log sanitization

5. **File Permissions:**
   - /app/logs/ writable por appuser (OK)
   - Outros paths não auditados
   - Dockerfile não usa USER explicitamente em cada stage

🎯 PROPOSTA DE IMPLEMENTAÇÃO (FASE 15):

FASE 15.1 — Rate Limiting (CRÍTICO):
```python
# app/middleware/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Per-action limits
@app.get("/api/v1/preferences/{user_id}")
@limiter.limit("10/minute")  # preferences: 10 req/min
async def get_preferences(...):
    ...

@app.post("/api/v1/process")
@limiter.limit("5/minute")  # process (LLM): 5 req/min
async def process(...):
    ...
```

Dependency: `slowapi` ou implementar in-memory cache com TTL.

FASE 15.2 — Timeouts + Size Limits:
```python
# app/main.py
app = FastAPI(
    timeout=30.0,  # Request timeout: 30s
)

# app/middleware/payload_limiter.py
MAX_PAYLOAD_SIZE = 1_048_576  # 1MB

@app.middleware("http")
async def limit_payload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_PAYLOAD_SIZE:
        raise HTTPException(413, "Payload too large")
    return await call_next(request)
```

FASE 15.3 — Secrets Hardening:
```bash
# Usar Docker secrets (em vez de .env plaintext)
docker secret create veritta_api_key ./secrets/api_key.txt

# docker-compose.yml
services:
  api:
    secrets:
      - veritta_api_key
    environment:
      VERITTA_BETA_API_KEY_FILE: /run/secrets/veritta_api_key
```

Código:
```python
# app/config.py
def load_secret(name: str) -> str:
    file_path = os.getenv(f"{name}_FILE")
    if file_path and os.path.exists(file_path):
        return Path(file_path).read_text().strip()
    return os.getenv(name, "")
```

FASE 15.4 — Structured Logging:
```python
# app/logger.py
import structlog

logger = structlog.get_logger()

# Usage
logger.info("request_processed", 
    user_id=user_id, 
    action=action, 
    status=200,
    latency_ms=latency
)
```

Output: JSON one-line-per-log (fácil parsing, não expõe secrets).

FASE 15.5 — Security Audit (manual):
```bash
# Dockerfile audit
- Verify USER directive
- Check COPY permissions
- Review exposed ports

# Dependency audit
pip-audit  # CVE scanner
safety check  # Python deps

# Git secrets scan
git-secrets --scan  # histórico
truffleHog  # commits
```

ESTIMATIVA: 2-3 dias
BLOQUEADORES: Nenhum (critical path)
RISCO: Baixo (ferramentas maduras)

⚠️ RECOMENDAÇÃO CRÍTICA:

EXECUTAR FASE 15.1-15.2 IMEDIATAMENTE (rate limit + timeout).
Produção está exposta.

FASE 15.3-15.5 podem ser incrementais.
```

---

### GPT → COPILOT

**Re: FASE 16 — Observabilidade Operacional**

```
PROPOSTA: Métricas por action/status + dashboards + alertas de 
gate/transição/migração.
```

### COPILOT → GPT

**Re: FASE 16 — ANÁLISE CRÍTICA**

```
✅ ALINHADO COM F9.8 (em andamento): Prometheus + Grafana já planejados.

📊 REALIDADE DO CÓDIGO (2026-01-04):

1. OBSERVABILIDADE EXISTENTE:
   ✅ /metrics endpoint (Prometheus format)
   ✅ Health check (/health)
   ⏳ F9.8 em andamento (Grafana dashboards)

2. MÉTRICAS ATUAIS:
   - http_requests_total (counter)
   - http_request_duration_seconds (histogram)
   - Métricas default (process, memory, etc)

3. NÃO EXISTE:
   - Métricas por action (preferences.get, process, etc)
   - Métricas por status de Operation (quando implementar)
   - Alertas configurados
   - SLOs definidos

🔴 GAPS IDENTIFICADOS:

1. **Métricas de Negócio ausentes:**
   - Quantas preferences foram criadas hoje?
   - Quantas requests falharam no gate?
   - Latência média por action?

2. **Alertas não configurados:**
   - Gate failure rate > 10%?
   - Request latency > 5s?
   - Health check failed 3x consecutivas?

3. **Dashboards genéricos:**
   - F9.8 (se existir) é infra (CPU, RAM, network)
   - Needs: dashboards de produto (actions, users, errors)

4. **SLOs não definidos:**
   - Uptime target? 99.9%?
   - Latency P95? <2s?
   - Error rate? <1%?

🎯 PROPOSTA DE IMPLEMENTAÇÃO (FASE 16):

FASE 16.1 — Métricas de Negócio:
```python
# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge

gate_decisions = Counter(
    "gate_decisions_total",
    "Total gate decisions by profile and decision",
    ["profile_id", "decision"]  # ALLOW/DENY
)

action_requests = Counter(
    "action_requests_total",
    "Total requests by action and status",
    ["action", "status_code"]
)

action_duration = Histogram(
    "action_duration_seconds",
    "Action processing time",
    ["action"]
)

# Usage in gate_request:
gate_decisions.labels(
    profile_id="F2.1", 
    decision="ALLOW"
).inc()

action_duration.labels(action="preferences.get").observe(0.123)
```

FASE 16.2 — Dashboards Grafana:
```
Dashboard 1: Gate Health
- Panel 1: Gate decisions (ALLOW vs DENY) por profile
- Panel 2: Top denied actions
- Panel 3: Gate latency P95

Dashboard 2: Actions Performance
- Panel 1: Requests por action (timeseries)
- Panel 2: Latency por action (heatmap)
- Panel 3: Error rate por action

Dashboard 3: Operations (quando implementar FASE 12)
- Panel 1: Operations por status
- Panel 2: Average operation duration
- Panel 3: Failed operations (last 24h)
```

FASE 16.3 — Alertas Prometheus:
```yaml
# alert.rules.yml
groups:
  - name: gate_alerts
    interval: 1m
    rules:
      - alert: HighGateFailureRate
        expr: |
          (sum(rate(gate_decisions_total{decision="DENY"}[5m])) 
          / sum(rate(gate_decisions_total[5m]))) > 0.10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Gate failure rate above 10%"
      
      - alert: HighRequestLatency
        expr: |
          histogram_quantile(0.95, 
            sum(rate(action_duration_seconds_bucket[5m])) by (le)
          ) > 5.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency above 5 seconds"
```

FASE 16.4 — SLO Definition:
```yaml
# slo.yaml (documentação)
slos:
  - name: API Availability
    target: 99.9%
    measurement: (successful_requests / total_requests)
    
  - name: Request Latency
    target: P95 < 2s
    measurement: histogram_quantile(0.95, action_duration_seconds)
    
  - name: Gate Success Rate
    target: > 90%
    measurement: (gate_allow / gate_total)
```

⚠️ DEPENDÊNCIA:

FASE 16 depende de F9.8 concluída (Prometheus + Grafana setup).

ESTIMATIVA: 2 dias (após F9.8)
BLOQUEADORES: F9.8 completion
RISCO: Baixo (extensão de infra existente)

RECOMENDAÇÃO: Executar FASE 16 APÓS F9.8 + FASE 15 (métricas de 
segurança também importantes).
```

---

### GPT → COPILOT

**Re: FASE 17 — Multi-Agents (ORDO36)**

```
PROPOSTA: Registro de executores (agentes) como módulos + contrato 
input→output→evidência→SEAL + permissões por executor.
```

### COPILOT → GPT

**Re: FASE 17 — ANÁLISE CRÍTICA**

```
⚠️ ALERTA: FASE 17 é ARQUITETURA NOVA, não extensão.

📊 REALIDADE DO CÓDIGO (2026-01-04):

1. LLM INFRASTRUCTURE (não hardened):
   - app/llm/ (protocol, executors, adapters)
   - 5 providers: OpenAI, Anthropic, Gemini, Grok, DeepSeek
   - FakeLLMClient (mock para testes)
   - NÃO está production-ready (F9.9-B pendente)

2. "AGENT" NÃO É CONCEITO ATUAL:
   - Backend = API stateless
   - LLM = executor síncrono (when implemented)
   - Não há "autonomous agents"

3. ORDO36 NÃO INTEGRADO:
   - ORDO36 = sistema externo?
   - Precisa ser plugado como "executor"?
   - Ou é apenas naming para multi-LLM?

🔴 BLOQUEIOS CRÍTICOS:

1. **F9.9-B não concluída:**
   - LLM hardening OBRIGATÓRIO antes de multi-agents
   - Não adianta plugar múltiplos LLMs se básico não funciona

2. **Arquitetura de Agent não especificada:**
   - Agent = LLM provider? (já temos 5)
   - Agent = autonomous loop? (não existe)
   - Agent = external system? (precisa spec)

3. **Permissões por executor não definidas:**
   - Executor X pode ler preferences?
   - Executor Y pode escrever artifacts?
   - Como autorizar? (novo profile type?)

4. **"Módulo" não é pattern atual:**
   - Backend usa routes (FastAPI)
   - Como "registrar módulo"? Plugin system?
   - Needs: plugin architecture (não existe)

🎯 QUESTÕES FUNDAMENTAIS:

1. **O que é "Agent" no contexto Techno OS?**
   - LLM provider (Claude, GPT, etc)?
   - Autonomous agent (looping executor)?
   - External system (ORDO36 API)?

2. **Como Agent se integra ao Backend?**
   - Via API calls (webhook)?
   - Via shared DB?
   - Via message queue (RabbitMQ/SQS)?

3. **Quem orquestra Agents?**
   - Backend é orchestrator?
   - Console escolhe Agent?
   - Agent decide autonomamente?

4. **Qual a relação com State Machine (FASE 12)?**
   - Agent executa uma Operation?
   - Operation pode ter múltiplos Agents?
   - Como sincronizar?

⚠️ RECOMENDAÇÃO CRÍTICA:

**PAUSAR FASE 17 até esclarecer:**

1. Completar F9.9-B (LLM Hardening) — baseline funcional
2. Definir arquitetura de "Agent" (workshop de 2-4h)
3. Prototipar integração com 1 Agent (POC)
4. Validar antes de generalizar

**ALTERNATIVA:**

Se "multi-agents" = "múltiplos LLM providers":
- Já está implementado (5 providers)
- F9.9-B hardena isso
- Não precisa FASE 17 separada

Se "multi-agents" = "ORDO36 como sistema autônomo":
- Precisa spec completa
- Integration patterns
- Security model (auth entre sistemas)

ESTIMATIVA: Impossível estimar sem spec clara
RISCO: MUITO ALTO (arquitetura indefinida)

🚨 NÃO INICIAR FASE 17 SEM WORKSHOP ARQUITETURAL.
```

---

## 📊 RESUMO EXECUTIVO

### ✅ APROVADO IMEDIATAMENTE

1. **FASE 10** — SEAL F9.9-A (concluída)
2. **FASE 11** — Gate Engine Consolidation (prioridade 1)
3. **FASE 15** — Segurança de Produção (prioridade 1, parcial)
4. **FASE 16** — Observabilidade (após F9.8)

### ⚠️ REQUER ESCLARECIMENTO

5. **FASE 12** — State Machine (esclarecer escopo + caso de uso)
6. **FASE 13** — Endpoints Console (após F9.9-B + decisão FASE 12)
7. **FASE 14** — Artifacts Policy (após FASE 12/13)

### 🚨 BLOQUEADO / NÃO RECOMENDADO

8. **FASE 17** — Multi-Agents (spec arquitetural ausente)

---

## 🎯 SEQUÊNCIA RECOMENDADA (REVISADA)

```
CRÍTICO (próximas 2 semanas):
├─ F9.9-B: LLM Hardening ........................ [2-3 dias]
├─ FASE 11: Gate Engine Consolidation .......... [1-2 dias]
├─ FASE 15.1-15.2: Rate Limit + Timeout ........ [1 dia]
└─ F9.8: Prometheus + Grafana (retomar) ........ [1-2 dias]

MÉDIO PRAZO (1 mês):
├─ WORKSHOP: Arquitetura Operation + Plan ....... [meio dia]
├─ FASE 12: State Machine (escopo reduzido) .... [2-3 dias]
├─ FASE 13.1: Endpoints Mínimos Console ......... [1-2 dias]
├─ FASE 16: Métricas de Negócio + Alertas ...... [2 dias]
└─ FASE 15.3-15.5: Secrets + Logs + Audit ....... [2-3 dias]

LONGO PRAZO (2-3 meses):
├─ FASE 14: Artifacts Policy + Storage .......... [2-3 dias]
├─ FASE 13.2-13.4: Endpoints Avançados .......... [3-5 dias]
└─ FASE 17: Multi-Agents (após workshop) ........ [TBD]
```

---

## 📋 AÇÕES REQUERIDAS DO ARQUITETO

### 1. Clarificar FASE 12 (State Machine)
- [ ] Definir caso de uso concreto (user story)
- [ ] Especificar relação com Sessions/Preferences
- [ ] Decidir escopo mínimo (MVP)
- [ ] Aprovar OPÇÃO A (simples) ou OPÇÃO B (complexo)

### 2. Clarificar FASE 13 (Endpoints Console)
- [ ] Especificar formato de "Plan" (JSON schema)
- [ ] Definir comportamento de /run (executar o quê?)
- [ ] Decidir se /seal gera doc ou marca status
- [ ] Priorizar endpoints (qual primeiro?)

### 3. Clarificar FASE 14 (Artifacts)
- [ ] Decidir storage strategy (filesystem vs S3)
- [ ] Definir artifact types canonical
- [ ] Especificar retention policy
- [ ] Aprovar modelo de DB proposto

### 4. Clarificar FASE 17 (Multi-Agents)
- [ ] Definir "Agent" no contexto Techno OS
- [ ] Especificar integration pattern
- [ ] Decidir se é extensão de F9.9-B ou arquitetura nova
- [ ] Agendar workshop arquitetural (se necessário)

---

## ✍️ ASSINATURA TÉCNICA

**Auditor:** Claude Sonnet 4.5 (GitHub Copilot)  
**Função:** Technical Lead Implementador  
**Data:** 2026-01-04  
**Baseline:** F9.9-A SEALED (commit 5fcc73a)  

**Parecer:** APROVADO COM RESSALVAS. Roadmap F10-F17 é ambicioso e 
bem estruturado, mas requer esclarecimentos arquiteturais críticos 
antes de FASE 12, 13, 14 e 17. Recomenda-se execução incremental 
com validações intermediárias.

**Risco geral:** MÉDIO-ALTO (depende de decisões não técnicas)  
**Viabilidade:** ALTA (com esclarecimentos)  
**Timeline otimista:** 2-3 meses (todas as fases)  
**Timeline realista:** 3-4 meses (com workshops + ajustes)

---

**🔒 FIM DO PARECER TÉCNICO**
