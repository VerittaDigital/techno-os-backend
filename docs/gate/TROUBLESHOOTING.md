# Gate Engine Troubleshooting — Runbook

## Visão geral
Guia operacional para diagnosticar e resolver erros do Gate Engine (F11).

**Público-alvo:** DevOps, SRE, desenvolvedores em produção.

---

## Errors de referência

### G8_UNKNOWN_ACTION (HTTP 500)
**Descrição:** Rota HTTP não mapeada no `ACTION_MAP`.

**Causa raiz:**
- Nova rota criada sem adicionar ao `ACTION_MAP`
- Path com typo (ex: `/proccess` ao invés de `/process`)
- Método HTTP incorreto (ex: GET ao invés de POST)

**Sintomas:**
```json
{
  "error": {"reason_code": "G8_UNKNOWN_ACTION", "message": "No mapping for POST /unknown"},
  "message": {...},
  "trace_id": "uuid"
}
```

**Auditoria:**
```json
// audit.log
{
  "decision": "DENY",
  "profile_id": "G8",
  "reason_codes": ["G8_UNKNOWN_ACTION"],
  "trace_id": "uuid"
}
```

**Diagnóstico:**
1. Verificar path e método na requisição HTTP (curl/Postman)
2. Conferir `app/gate_canonical/action_detector.py` → `ACTION_MAP`
3. Se path dinâmico (ex: `/preferences/{user_id}`), verificar normalização

**Resolução:**

**Se rota DEVERIA existir:**
1. Adicionar ao `ACTION_MAP`:
```python
ACTION_MAP = {
    ("/my-route", "POST"): "my_action",
    ...
}
```

2. Adicionar ao `action_matrix.py`:
```python
allowed_actions = ["process", "preferences.delete", "preferences.get", "preferences.put", "my_action"]
```

3. Criar `PolicyProfile` em `gate_profiles.py`

4. Rodar testes: `pytest tests/test_gate_integrity.py`

**Se rota NÃO deveria existir:**
- Corrigir cliente (typo, método incorreto, URL errada)

**Hotfix em produção:**
- Não há hotfix (requer deploy de código)
- Alternativa: reverter deploy + corrigir código + redeploy

---

### G9_MISSING_PROFILE (HTTP 500)
**Descrição:** Action existe no `action_matrix` mas não tem `PolicyProfile` correspondente.

**Causa raiz:**
- Drift de governança: action adicionada ao matrix sem criar profile
- Profile foi removido mas action permanece no matrix

**Sintomas:**
```json
{
  "error": {"reason_code": "G9_MISSING_PROFILE", "message": "No profile for action=my_action"},
  "trace_id": "uuid"
}
```

**Auditoria:**
```json
// audit.log
{
  "decision": "DENY",
  "profile_id": "G9",
  "reason_codes": ["G9_MISSING_PROFILE"],
  "trace_id": "uuid"
}
```

**Diagnóstico:**
1. Verificar `app/action_matrix.py` → `allowed_actions`
2. Verificar `app/gate_profiles.py` → `DEFAULT_PROFILES`
3. Rodar: `pytest tests/test_gate_integrity.py` (deve falhar)

**Resolução:**

**Adicionar profile faltante:**
```python
# app/gate_profiles.py
ACTION_MY_ACTION = "my_action"
DEFAULT_PROFILES[ACTION_MY_ACTION] = PolicyProfile(
    id="my_action",
    allowlist={"field1", "field2"},
    allow_external=False,
    deny_unknown_fields=True
)
```

**Atualizar lock:**
```bash
python -c "from app.gate_artifacts import profiles_fingerprint_sha256; print(profiles_fingerprint_sha256())" > app/profiles_fingerprint.lock
```

**Validar:**
```bash
pytest tests/test_gate_integrity.py  # Deve passar
pytest tests/test_profiles_governance_lock.py  # Deve passar
```

**Prevenção:**
- Sempre rodar `pytest tests/test_gate_integrity.py` antes de commit
- CI/CD deve bloquear deploy se teste falhar

---

### G10_BODY_PARSE_ERROR (HTTP 422)
**Descrição:** JSON inválido ou ausente quando método HTTP requer body.

**Causa raiz:**
- Cliente enviou JSON malformado
- Cliente não enviou body em POST/PUT/PATCH
- Cliente enviou Content-Type incorreto (ex: `text/plain` ao invés de `application/json`)

**Sintomas:**
```json
{
  "error": {"reason_code": "G10_BODY_PARSE_ERROR", "message": "Invalid or missing JSON body: ..."},
  "trace_id": "uuid"
}
```

**Auditoria:**
```json
// audit.log
{
  "decision": "DENY",
  "profile_id": "G10",
  "reason_codes": ["G10_BODY_PARSE_ERROR"],
  "trace_id": "uuid"
}
```

**Diagnóstico:**
1. **Verificar request raw:**
```bash
curl -X POST https://api.exemplo.com/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_test_abc" \
  -d '{"text": "hello"}'  # Testar com JSON válido
```

2. **Verificar Content-Type:**
- DEVE ser `application/json` para POST/PUT/PATCH
- Se `text/plain` ou omitido → G10

3. **Validar JSON:**
```bash
# Testar parse local
echo '{"text": "hello"}' | jq .  # OK
echo '{broken json' | jq .        # Error
```

**Resolução:**

**Se cliente está incorreto:**
- Corrigir JSON no cliente
- Adicionar Content-Type header: `application/json`
- Usar ferramenta de validação JSON (jsonlint.com)

**Se erro está no servidor:**
- Verificar encoding (UTF-8 esperado)
- Verificar Content-Length (> 0 para POST/PUT/PATCH)

**Notas:**
- GET/DELETE SÃO TOLERANTES: retornam `{}` mesmo se body presente (warning no log)
- POST/PUT/PATCH SÃO STRICT: exigem JSON válido ou retornam G10

---

### G11_INVALID_PAYLOAD (HTTP 422)
**Descrição:** JSON válido mas payload não passa validação Pydantic ou allowlist.

**Causa raiz:**
- Campo obrigatório ausente (ex: `text` em `/process`)
- Campo não permitido enviado (violação de `allowlist`)
- Tipo de campo incorreto (ex: `text: 123` ao invés de string)

**Sintomas:**
```json
{
  "error": {"reason_code": "G11_INVALID_PAYLOAD", "message": "Field validation failed: ..."},
  "trace_id": "uuid"
}
```

**Diagnóstico:**
1. Verificar schema Pydantic da action:
   - `/process` → `ProcessRequest(text: str)`
   - `/preferences/{user_id}` PUT → `PreferencesUpdate(...)`

2. Verificar allowlist do PolicyProfile:
```python
# app/gate_profiles.py
DEFAULT_PROFILES[ACTION_PROCESS] = PolicyProfile(
    id="process",
    allowlist={"text", "user_id"},  # Somente esses campos
    ...
)
```

3. Comparar payload enviado vs allowlist:
```json
// Payload enviado
{"text": "hello", "extra_field": "invalid"}

// allowlist
{"text", "user_id"}

// Resultado: "extra_field" não permitido → G11
```

**Resolução:**

**Se cliente está incorreto:**
- Remover campos não permitidos
- Adicionar campos obrigatórios faltantes
- Corrigir tipos de campos

**Se allowlist está incorreta:**
1. Atualizar PolicyProfile:
```python
DEFAULT_PROFILES[ACTION_PROCESS] = PolicyProfile(
    id="process",
    allowlist={"text", "user_id", "extra_field"},  # NOVO campo
    ...
)
```

2. Atualizar lock:
```bash
python -c "from app.gate_artifacts import profiles_fingerprint_sha256; print(profiles_fingerprint_sha256())" > app/profiles_fingerprint.lock
```

3. Documentar mudança em GOVERNANCE_PROFILES.md

---

## Cenários comuns

### Cenário 1: Nova rota não funciona (G8)

**Sintoma:** Cliente recebe HTTP 500 com G8_UNKNOWN_ACTION.

**Checklist:**
- [ ] Rota adicionada ao `ACTION_MAP`?
- [ ] Path normalizado corretamente? (ex: `/api/v1/preferences/abc` → `/preferences/{user_id}`)
- [ ] Método HTTP correto? (POST, GET, PUT, DELETE)
- [ ] Action adicionada ao `action_matrix.py`?
- [ ] PolicyProfile criado em `gate_profiles.py`?
- [ ] `pytest tests/test_gate_integrity.py` passa?

**Solução rápida:** Seguir processo de adição de nova action (ver ACTION_MATRIX.md).

---

### Cenário 2: JSON malformado no cliente

**Sintoma:** Cliente recebe HTTP 422 com G10_BODY_PARSE_ERROR.

**Checklist:**
- [ ] JSON válido? (testar com `jq` ou jsonlint)
- [ ] Content-Type: application/json?
- [ ] Body não está vazio para POST/PUT/PATCH?
- [ ] Encoding UTF-8?

**Solução rápida:**
```bash
# Testar com curl válido
curl -X POST https://api.exemplo.com/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_test_abc" \
  -d '{"text": "hello world"}'
```

---

### Cenário 3: Campo extra enviado (G11)

**Sintoma:** Cliente recebe HTTP 403 ou 422 com G11_INVALID_PAYLOAD.

**Checklist:**
- [ ] Verificar allowlist do PolicyProfile para a action
- [ ] Campo extra é intencional? (adicionar ao allowlist)
- [ ] Campo extra é acidental? (remover do cliente)

**Solução:**
```python
# Opção A: Adicionar campo ao allowlist (se intencional)
DEFAULT_PROFILES[ACTION_PROCESS] = PolicyProfile(
    allowlist={"text", "user_id", "new_field"},  # NOVO
    ...
)

# Opção B: Remover campo do cliente (se acidental)
# Cliente: {"text": "hello"}  # Sem "extra_field"
```

---

## Debugging avançado

### Verificar audit.log
```bash
# Buscar por trace_id
grep "trace_id_uuid" audit.log | jq .

# Buscar por reason_code
grep "G8_UNKNOWN_ACTION" audit.log | jq .

# Últimas 10 decisões DENY
grep "DENY" audit.log | tail -10 | jq .
```

### Verificar normalization de path
```python
from app.gate_canonical import normalize_path

# Testar path
path = "/api/v1/preferences/user_abc123"
normalized = normalize_path(path)
print(normalized)  # "/preferences/{user_id}"
```

### Simular detect_action
```python
from app.gate_canonical import detect_action
from starlette.requests import Request

# Mock request
scope = {
    "type": "http",
    "method": "POST",
    "path": "/process",
    "query_string": b"",
    "headers": [],
}
request = Request(scope)

action = detect_action(request)
print(action)  # "process"
```

---

## Alertas recomendados (Prometheus/Grafana)

### G8_UNKNOWN_ACTION spike
```promql
rate(gate_decision_deny_total{reason_code="G8_UNKNOWN_ACTION"}[5m]) > 0.1
```
**Ação:** Verificar se nova rota foi adicionada sem mapping.

### G10_BODY_PARSE_ERROR spike
```promql
rate(gate_decision_deny_total{reason_code="G10_BODY_PARSE_ERROR"}[5m]) > 1
```
**Ação:** Verificar se cliente está enviando JSON malformado.

### G9_MISSING_PROFILE (crítico)
```promql
gate_decision_deny_total{reason_code="G9_MISSING_PROFILE"} > 0
```
**Ação:** DRIFT DE GOVERNANÇA DETECTADO. Corrigir imediatamente.

---

## Contato e escalação

**Nível 1 (DevOps):**
- G8, G10, G11 (erros de cliente ou config)

**Nível 2 (Dev Backend):**
- G9 (drift de governança, requer code change)

**Nível 3 (Arquiteto V-COF):**
- Mudanças em PolicyProfile ou action_matrix

**Documentação adicional:**
- [GATE_ENGINE_SPEC.md](./GATE_ENGINE_SPEC.md)
- [ACTION_MATRIX.md](./ACTION_MATRIX.md)
- [F11-GATE-CONSOLIDATION-PLAN.md](../implementation/F11-GATE-CONSOLIDATION-PLAN.md)

