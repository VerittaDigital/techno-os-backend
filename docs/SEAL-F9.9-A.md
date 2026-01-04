# SEAL F9.9-A — User Preferences Persistence

**Status:** ✅ CONCLUÍDO  
**Data:** 2026-01-04  
**Branch:** `feature/f9.9-a-user-preferences`  
**Commit final:** `3ee4e9e`  

---

## 1. Objetivo

Implementar persistência de preferências de usuário (tom, formato de output, idioma) seguindo governance V-COF FAIL-CLOSED + HUMAN-IN-THE-LOOP.

**Escopo:**
- Model SQLAlchemy `UserPreferenceModel` (7 colunas, UUID PK, UNIQUE user_id)
- Schemas Pydantic v2 (`UserPreferenceUpdate`, `UserPreferenceResponse`)
- Migration Alembic `52e2b2a85aec_add_user_preferences_table.py`
- Endpoints CRUD (`GET`, `PUT`, `DELETE` em `/api/v1/preferences/{user_id}`)
- Gate F2.1 (X-API-Key) com profiles específicos
- Anti-enumeration (user_id == X-VERITTA-USER-ID header)
- 12 unit tests (404 total, 0 failures)
- Deployment VPS com smoke tests

---

## 2. Commits (Rastreabilidade Git)

### Baseline
- **271cf64** - `chore(tooling): add alembic, pytest-cov, coverage, flake8 to requirements` (2026-01-03)
  - Requirements.txt: alembic==1.17.2, pytest-cov==6.0.0, coverage==7.6.9, flake8==7.1.1
  - Branch: stage/f9.9-a-prep-tooling
  - Tests baseline: 392 passing

### Feature Branch (feature/f9.9-a-user-preferences)

**db0adfa** - `feat(preferences): add user preferences persistence (F9.9-A)`
- app/models/user_preference.py (73 lines) - UserPreferenceModel
- app/schemas/user_preference.py (44 lines) - Pydantic schemas
- app/routes/preferences.py (177 lines) - CRUD endpoints
- app/main.py - router registration
- alembic/env.py - import UserPreferenceModel for autogenerate
- alembic/versions/52e2b2a85aec_add_user_preferences_table.py - migration
- tests/test_preferences.py (328 lines, 12 tests) - unit tests
- tests/conftest.py - test DB setup
- **Tests:** 404 passing (392 baseline + 12 new), 0 failures

**c20c098** - `fix(build): include alembic files in Docker image`
- Dockerfile - COPY alembic.ini and alembic/ directory

**6130bb6** - `fix(alembic): remove localhost replacement in DATABASE_URL`
- alembic/env.py - remove hardcoded postgres→localhost replacement

**0623282** - `fix(audit): set writable audit.log path for appuser`
- Dockerfile - chown -R appuser:appuser /app, mkdir -p /app/logs
- app/audit_sink.py - default path /app/logs/audit.log

**94c1729** - `feat(config): add VERITTA env vars to docker-compose`
- docker-compose.yml - add VERITTA_BETA_API_KEY, VERITTA_PROFILES_FINGERPRINT, etc.

**aef9fbf** - `feat(preferences): register actions in matrix and auto-detect from path`
- app/action_matrix.py - add preferences.{get|put|delete} to allowed_actions
- app/main.py - extract action from request path

**7f06387** - `feat(preferences): add profiles for preferences.{get,put,delete}`
- app/gate_profiles.py - PolicyProfile for each preferences action

**3ee4e9e** - `fix(gate): allow empty body for GET/DELETE methods`
- app/main.py - skip body parsing for GET/DELETE

---

## 3. Arquitetura Técnica

### 3.1 Model (app/models/user_preference.py)
```python
class UserPreferenceModel(Base):
    __tablename__ = "user_preferences"
    
    preference_id = Column(String(36), primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    tone_preference = Column(String(50), nullable=True)
    output_format = Column(String(50), nullable=True)
    language = Column(String(10), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=datetime.now(timezone.utc))
```

**Decisões de design:**
- UUID preference_id (PK) para atomicidade
- UNIQUE index em user_id (1:1 user→preferences)
- Campos opcionais (nullable=True) para flexibilidade
- Timezone-aware timestamps (UTC)
- to_dict() method para serialização JSON

### 3.2 Schemas (app/schemas/user_preference.py)

**UserPreferenceUpdate (PUT):**
```python
class UserPreferenceUpdate(BaseModel):
    tone_preference: Optional[str] = Field(None, pattern="^(institutional|technical|conversational)$")
    output_format: Optional[str] = Field(None, pattern="^(text|bullet_points|checklist|table|structured)$")
    language: Optional[str] = Field(None, pattern="^(pt-BR|en-US)$")
```

**UserPreferenceResponse (GET):**
```python
class UserPreferenceResponse(BaseModel):
    preference_id: str
    user_id: str
    tone_preference: Optional[str]
    output_format: Optional[str]
    language: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
```

**Validação Pydantic v2:**
- Regex patterns para valores permitidos
- ConfigDict(from_attributes=True) para ORM compatibility
- Partial updates suportados (campos Optional)

### 3.3 Migration (alembic/versions/52e2b2a85aec)

**SQL executado:**
```sql
CREATE TABLE user_preferences (
    preference_id VARCHAR(36) NOT NULL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    tone_preference VARCHAR(50),
    output_format VARCHAR(50),
    language VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX ix_user_preferences_user_id ON user_preferences (user_id);
```

**Downgrade:**
```sql
DROP INDEX ix_user_preferences_user_id;
DROP TABLE user_preferences;
```

### 3.4 Endpoints (app/routes/preferences.py)

**GET /api/v1/preferences/{user_id}**
- Response: 200 + UserPreferenceResponse | 404 if not found
- Anti-enumeration: validates user_id == X-VERITTA-USER-ID header (403 if mismatch)
- Gate: F2.1 X-API-Key via gate_dependency

**PUT /api/v1/preferences/{user_id}**
- Body: UserPreferenceUpdate (partial allowed)
- Response: 200 + UserPreferenceResponse
- Logic: upsert (INSERT if not exists, UPDATE if exists)
- Validation: Pydantic regex patterns + anti-enumeration

**DELETE /api/v1/preferences/{user_id}**
- Response: 204 No Content | 404 if not found
- LGPD compliance: explicit user control over data deletion

### 3.5 Governance V-COF

**Gate F2.1 Chain:**
1. G0: Check VERITTA_BETA_API_KEY configured
2. G2: API key validation (fail-closed)
3. G7: Payload limits + forbidden fields
4. G8: Action/profile matrix check
5. G10: Rate limiting
6. G12: Async audit (post-response)

**Action Matrix:**
```python
allowed_actions = [
    "process",
    "preferences.get",
    "preferences.put",
    "preferences.delete",
]
```

**Gate Profiles:**
```python
ACTION_PREFERENCES_GET: PolicyProfile(
    name="preferences.get.v1",
    allowlist=frozenset(),  # GET sem payload
    deny_unknown_fields=False,
)

ACTION_PREFERENCES_PUT: PolicyProfile(
    name="preferences.put.v1",
    allowlist=frozenset({"tone_preference", "output_format", "language"}),
    deny_unknown_fields=True,
)

ACTION_PREFERENCES_DELETE: PolicyProfile(
    name="preferences.delete.v1",
    allowlist=frozenset(),  # DELETE sem payload
    deny_unknown_fields=False,
)
```

---

## 4. Testes

### 4.1 Unit Tests (tests/test_preferences.py)

**TestGetPreferences (4 tests):**
- `test_get_preferences_success` → 200 OK
- `test_get_preferences_not_found` → 404
- `test_get_preferences_user_id_mismatch` → 403 (anti-enumeration)
- `test_get_preferences_no_auth` → 401 (gate_dependency mock bypass check)

**TestPutPreferences (5 tests):**
- `test_put_preferences_create` → 200 OK (INSERT)
- `test_put_preferences_update` → 200 OK (UPDATE)
- `test_put_preferences_partial_update` → 200 OK (apenas tone_preference)
- `test_put_preferences_user_id_mismatch` → 403 (anti-enumeration)
- `test_put_preferences_invalid_tone` → 400/422 (Pydantic validation)

**TestDeletePreferences (3 tests):**
- `test_delete_preferences_success` → 204 No Content
- `test_delete_preferences_not_found` → 404
- `test_delete_preferences_user_id_mismatch` → 403 (anti-enumeration)

**Fixtures:**
- `test_client_with_auth`: TestClient com gate_dependency mockado
- `test_db_engine`: SQLite in-memory com check_same_thread=False
- `db_session`: Session transactional (rollback após cada teste)

**Coverage:**
- **404 tests passing** (392 baseline + 12 new)
- **0 failures**
- Non-regression validado

---

## 5. Deployment VPS

### 5.1 Infraestrutura
- **Host:** srv1241381.hstgr.cloud (72.61.219.157)
- **SSH alias:** techno-os (deploy user)
- **Path:** /opt/techno-os/app/backend
- **Docker:** Compose v2, services 'postgres' and 'api'
- **Database:** PostgreSQL 15, user techno_user, database techno_os

### 5.2 Processo de Deploy

**1. Pull código:**
```bash
git fetch origin
git checkout feature/f9.9-a-user-preferences
git pull origin feature/f9.9-a-user-preferences
```

**2. Configuração .env:**
```env
DATABASE_URL=postgresql://techno_user:change_me_in_production@postgres:5432/techno_os
VERITTA_BETA_API_KEY=f99a-test-deployment-key-2026-01-04
VERITTA_PROFILES_FINGERPRINT=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
VERITTA_HOST=0.0.0.0
VERITTA_PORT=8000
LOG_LEVEL=INFO
```

**3. Rebuild containers:**
```bash
docker compose down
docker compose up -d --build
```

**4. Executar migração:**
```bash
docker compose exec api alembic upgrade head
```

**Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> da44f6d378a1, baseline_initial_schema
INFO  [alembic.runtime.migration] Running upgrade da44f6d378a1 -> 52e2b2a85aec, add_user_preferences_table
```

**5. Validação tabela:**
```bash
docker compose exec postgres psql -U techno_user -d techno_os -c '\d user_preferences'
```

**Output:**
```
                              Table "public.user_preferences"
     Column      |           Type           | Collation | Nullable |      Default      
-----------------+--------------------------+-----------+----------+-------------------
 preference_id   | character varying(36)    |           | not null | 
 user_id         | character varying(255)   |           | not null | 
 tone_preference | character varying(50)    |           |          | 
 output_format   | character varying(50)    |           |          | 
 language        | character varying(10)    |           |          | 
 created_at      | timestamp with time zone |           | not null | CURRENT_TIMESTAMP
 updated_at      | timestamp with time zone |           |          | 
Indexes:
    "user_preferences_pkey" PRIMARY KEY, btree (preference_id)
    "ix_user_preferences_user_id" UNIQUE, btree (user_id)
```

### 5.3 Smoke Tests (VPS Production)

**Health check:**
```bash
curl -sf http://localhost:8000/health
# Response: {"status":"ok"}
```

**PUT (create):**
```bash
curl -X PUT \
  -H "X-API-KEY: f99a-test-deployment-key-2026-01-04" \
  -H "X-VERITTA-USER-ID: test-user-f99a" \
  -H "Content-Type: application/json" \
  -d '{"tone_preference":"institutional","output_format":"text","language":"pt-BR"}' \
  http://localhost:8000/api/v1/preferences/test-user-f99a

# Response: HTTP/1.1 200 OK
# {
#   "preference_id":"4b1e1ca9-bbf1-4f08-8916-1404e55fe3e9",
#   "user_id":"test-user-f99a",
#   "tone_preference":"institutional",
#   "output_format":"text",
#   "language":"pt-BR",
#   "created_at":"2026-01-04T15:37:09.123456Z",
#   "updated_at":null
# }
```

**GET (retrieve):**
```bash
curl -H "X-API-KEY: f99a-test-deployment-key-2026-01-04" \
     -H "X-VERITTA-USER-ID: test-user-f99a" \
     http://localhost:8000/api/v1/preferences/test-user-f99a

# Response: HTTP/1.1 200 OK
# (same JSON as PUT response)
```

**DELETE (remove):**
```bash
curl -X DELETE \
  -H "X-API-KEY: f99a-test-deployment-key-2026-01-04" \
  -H "X-VERITTA-USER-ID: test-user-f99a" \
  http://localhost:8000/api/v1/preferences/test-user-f99a

# Response: HTTP/1.1 204 No Content
```

**GET after DELETE (validate):**
```bash
curl -i -H "X-API-KEY: f99a-test-deployment-key-2026-01-04" \
        -H "X-VERITTA-USER-ID: test-user-f99a" \
        http://localhost:8000/api/v1/preferences/test-user-f99a

# Response: HTTP/1.1 404 Not Found
# {"error":"Preferences not found","message":"Preferences not found","trace_id":"..."}
```

✅ **Todos os smoke tests passaram com sucesso.**

---

## 6. Audit Trail (Governance)

**Audit log path:** `/app/logs/audit.log` (JSONL append-only)

**Sample decision record (G8 ALLOW):**
```json
{
  "decision": "ALLOW",
  "profile_id": "G8",
  "profile_hash": "f92d5263e1dbe67375a7ade4210877d4f38a2bcf5b3f312039b60904e25e2299",
  "matched_rules": [],
  "reason_codes": [],
  "input_digest": "3b3adb32b753dcbc6b4efd821adb28445ef2808b35a2dcfe5ae30505eb964e6d",
  "trace_id": "d187e31d-922e-4096-b730-2fb03d3d9257",
  "ts_utc": "2026-01-04T15:35:31.576141Z",
  "event_type": "decision_audit"
}
```

**Gate enforcement active:**
- X-API-Key validation (G2)
- Action/profile matrix (G8)
- Payload validation (G7)
- Rate limiting (G10)
- Audit trail persistence (G12)

---

## 7. Blockers Resolvidos

### B1: Circular Import (app/routes/preferences.py → app.main)
**Problema:** `from app.main import gate_request` causa circular import.  
**Solução:** Criado `gate_dependency()` wrapper que importa lazily.

### B2: SQLite Threading (tests/conftest.py)
**Problema:** TestClient usa threads, SQLite default é single-threaded.  
**Solução:** `connect_args={"check_same_thread": False}` no test_db_engine.

### B3: Docker Image Missing alembic.ini
**Problema:** Dockerfile não copiava alembic.ini nem alembic/.  
**Solução:** Adicionado `COPY alembic.ini .` e `COPY alembic/ ./alembic/`.

### B4: alembic/env.py localhost replacement
**Problema:** Hardcoded `database_url.replace("postgres:5432", "localhost:5432")` quebrava VPS.  
**Solução:** Removida substituição, usar DATABASE_URL diretamente.

### B5: audit.log Permission Denied
**Problema:** Container roda como `appuser` (non-root) mas audit.log estava em /app sem permissões.  
**Solução:** `mkdir -p /app/logs && chown -R appuser:appuser /app` no Dockerfile, path `/app/logs/audit.log`.

### B6: VERITTA_BETA_API_KEY não configurado
**Problema:** VPS não tinha .env com VERITTA_BETA_API_KEY, gate bloqueava com G0_auth_not_configured.  
**Solução:** Criado .env no VPS + atualizado docker-compose.yml para injetar env vars.

### B7: Action "preferences.put" não reconhecida (G8_UNKNOWN_ACTION)
**Problema:** action_matrix não incluía preferences actions, get_profile() retornava None.  
**Solução:** Adicionadas actions ao action_matrix + criados PolicyProfile para cada action.

### B8: GET/DELETE methods retornavam 400 "Request body is not valid JSON"
**Problema:** gate_request tentava parsear body em todas requisições.  
**Solução:** `if request.method in ("GET", "DELETE"): body = {}` para permitir requisições sem body.

---

## 8. Lições Aprendidas

1. **FAIL-CLOSED execution order:** Migração deve rodar ANTES de rebuild, mas tooling (alembic) precisa estar no container. Solução pragmática: rebuild primeiro quando tooling falta.

2. **Docker permissions:** Non-root users precisam permissões explícitas de escrita. `chown -R` no Dockerfile resolve.

3. **Gate flexibility:** GET/DELETE precisam bypass de body parsing. Profiles com `allowlist=frozenset()` e `deny_unknown_fields=False`.

4. **Pydantic v2 migration:** `Config` class → `model_config = ConfigDict(from_attributes=True)`.

5. **VPS .env management:** Variáveis críticas (VERITTA_BETA_API_KEY) devem estar no .env + docker-compose.yml env injection.

---

## 9. Checklist de Conformidade

- [x] Model SQLAlchemy com UUID PK e UNIQUE user_id
- [x] Schemas Pydantic v2 com validation patterns
- [x] Migration Alembic com upgrade/downgrade
- [x] Endpoints CRUD com anti-enumeration
- [x] Gate F2.1 com profiles específicos
- [x] 12 unit tests (404 total passing)
- [x] Non-regression validado (0 failures)
- [x] Migration executada no VPS PostgreSQL
- [x] Smoke tests validados em produção
- [x] Audit trail persistido em JSONL
- [x] Dockerfile com permissões corretas
- [x] .env configurado no VPS
- [x] Action matrix atualizado
- [x] Gate profiles criados
- [x] GET/DELETE sem body funcionando
- [x] Documentation completa (SEAL)

---

## 10. Next Steps (Post-F9.9-A)

1. **Merge to main:** Criar PR de `feature/f9.9-a-user-preferences` → `main`
2. **F9.9-B (LLM Hardening):** Seguir governança V-COF para integração LLM
3. **Console Integration:** Frontend deve consumir `/api/v1/preferences` para personalização
4. **Rate Limiting Review:** Ajustar G10 rate limits se necessário
5. **Monitoring:** Adicionar métricas de uso dos endpoints preferences

---

## 11. Referências

- **ROADMAP.md** - F9.9 User Preferences Persistence
- **Copilot Instructions** - `.github/copilot-instructions.md`
- **V-COF Governance** - CONFORMIDADE_EXECUTION_SEMANTICS_V1.txt
- **Pydantic v2 docs** - https://docs.pydantic.dev/latest/
- **Alembic docs** - https://alembic.sqlalchemy.org/

---

**Assinatura digital (commit hash):** 3ee4e9e  
**Baseline ref:** 271cf64  
**Execution time:** ~90 minutes (planning + implementation + deployment)  
**Human checkpoints:** 6 (FAIL-CLOSED governance)  

✅ **F9.9-A User Preferences Persistence: CONCLUÍDO E VALIDADO EM PRODUÇÃO**
