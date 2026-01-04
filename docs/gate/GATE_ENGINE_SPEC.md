# Gate Engine Specification — FASE 11

## Visão geral
O Gate Engine consolidado (F11) implementa detecção canônica de ações e parsing determinístico de body, eliminando recorrência de erros G8_UNKNOWN_ACTION e falhas de parse.

## Arquitetura

```
HTTP Request
    ↓
┌─────────────────────────────────────────────────┐
│  gate_request() [main.py]                      │
├─────────────────────────────────────────────────┤
│  1. Autenticação (X-API-Key / X-Bearer-Token)  │
│  2. detect_action(request) → action            │
│  3. Validar action in action_matrix            │
│  4. Validar get_profile(action) != None        │
│  5. parse_body_by_method(request) → body       │
│  6. evaluate_gate(GateInput) → GateResult      │
│  7. Se DENY → log DecisionRecord → raise       │
│  8. Se ALLOW → route_action(action) → execute  │
└─────────────────────────────────────────────────┘
```

## Módulos

### 1. `app/gate_canonical/action_detector.py`

**Propósito:** Detecção canônica de action a partir de HTTP request.

**Componentes:**
- `ACTION_MAP: Dict[(path, method), action]`
  - Template-based: `/preferences/{user_id}` (não literal `/preferences/abc123`)
  - Cobertura: `/process`, `/preferences/{user_id}` (GET/PUT/DELETE)

- `normalize_path(raw_path: str) -> str`
  - Remove prefixo `/api/v1` (compatibilidade VPS)
  - Colapsa paths dinâmicos:
    - `/preferences/abc123` → `/preferences/{user_id}`
    - `/preferences/xyz789` → `/preferences/{user_id}`

- `detect_action(request: Request) -> str`
  - `path = normalize_path(request.url.path)`
  - `key = (path, request.method)`
  - `action = ACTION_MAP.get(key)`
  - Se `None`: `raise GateError(G8_UNKNOWN_ACTION, 500)`
  - Se found: `return action`

**Correções aplicadas:**
- **C1:** Templates `{user_id}` ao invés de paths literais
- **C2:** Formaliza auto-detect existente (não adiciona nova lógica)
- **C3:** Paths prontos para smoke tests com `/api/v1/preferences/{user_id}`

**Exemplo de uso:**
```python
from app.gate_canonical import detect_action

action = detect_action(request)  # "process" | "preferences.get" | ...
# Raises GateError(G8) se rota desconhecida
```

---

### 2. `app/gate_canonical/body_parser.py`

**Propósito:** Parse determinístico de body por método HTTP (não mais ad-hoc).

**Regras:**
| Método HTTP  | Body obrigatório? | Retorno | Exceção |
|--------------|-------------------|---------|---------|
| GET          | Não (opcional)    | `{}`    | Warning se Content-Length > 0 |
| DELETE       | Não (opcional)    | `{}`    | Warning se Content-Length > 0 |
| POST         | Sim               | `dict`  | GateError(G10, 422) se parse falhar |
| PUT          | Sim               | `dict`  | GateError(G10, 422) se parse falhar |
| PATCH        | Sim               | `dict`  | GateError(G10, 422) se parse falhar |
| OPTIONS/HEAD | Não               | `{}`    | — |

**Componentes:**
- `parse_body_by_method(request: Request) -> dict`
  - Async function (await request.body())
  - GET/DELETE: tolerante, retorna `{}` (warning se body presente)
  - POST/PUT/PATCH: exige JSON válido, raise GateError(G10) em falha

**Correções aplicadas:**
- **C4:** GateError(G10_BODY_PARSE_ERROR, 422) ao invés de HTTPException(400)
- **Q2:** GET/DELETE tolerante com warning (não erro)

**Exemplo de uso:**
```python
from app.gate_canonical import parse_body_by_method

body = await parse_body_by_method(request)  # dict | GateError(G10)
```

---

### 3. `app/gate_errors.py`

**Propósito:** Exceções estruturadas com reason codes estáveis para audit.

**Componentes:**

#### `ReasonCode(Enum)`
Códigos canônicos de falha gate (não podem mudar):
- `G0_AUTH_NOT_CONFIGURED`: Auth environment inválido
- `G8_UNKNOWN_ACTION`: Rota desconhecida (no ACTION_MAP)
- `G9_MISSING_PROFILE`: Profile não existe para action
- `G10_BODY_PARSE_ERROR`: JSON inválido ou ausente
- `G11_INVALID_PAYLOAD`: Payload não passa validação Pydantic

#### `GateError(HTTPException)`
```python
class GateError(HTTPException):
    def __init__(self, reason_code: ReasonCode, message: str, http_status: int = 403):
        self.reason_code = reason_code
        super().__init__(status_code=http_status, detail={
            "reason_code": reason_code.value,  # Fonte canônica para audit
            "message": message,
            "type": "gate_error"
        })
```

**Correções aplicadas:**
- **C5:** `reason_code` em `detail["reason_code"]` (não `detail.reason_code`)
- **R3:** G8 retorna 500 (internal error, não 404)

**Exemplo de uso:**
```python
from app.gate_errors import GateError, ReasonCode

raise GateError(
    reason_code=ReasonCode.G8_UNKNOWN_ACTION,
    message=f"No mapping for {method} {path}",
    http_status=500
)
```

---

## Fluxo de requisição

### Cenário 1: Requisição válida (POST /process)

```
1. POST /process {"text": "hello"}
   ↓
2. detect_action(request)
   - normalize_path("/process") → "/process"
   - ACTION_MAP[("/process", "POST")] → "process" ✅
   ↓
3. Validar "process" in action_matrix.allowed_actions ✅
   ↓
4. get_profile("process") → PolicyProfile(...) ✅
   ↓
5. parse_body_by_method(request)
   - Método POST → exige JSON
   - parse {"text": "hello"} → {"text": "hello"} ✅
   ↓
6. evaluate_gate(GateInput) → GateResult(ALLOW)
   ↓
7. route_action("process") → executor → LLM pipeline
   ↓
8. HTTP 200 + response JSON
```

### Cenário 2: Rota desconhecida (POST /unknown)

```
1. POST /unknown {"data": "test"}
   ↓
2. detect_action(request)
   - normalize_path("/unknown") → "/unknown"
   - ACTION_MAP[("/unknown", "POST")] → None ❌
   → raise GateError(G8_UNKNOWN_ACTION, 500)
   ↓
3. main.py gate_request() captura GateError:
   - log DecisionRecord(DENY, reason_codes=["G8_UNKNOWN_ACTION"])
   - re-raise GateError
   ↓
4. error_handler.py http_exception_handler():
   - Converte GateError.detail em error envelope
   - HTTP 500 + {"error": {...}, "trace_id": "..."}
```

### Cenário 3: JSON inválido (POST /process com body malformado)

```
1. POST /process {broken json}
   ↓
2. detect_action(request) → "process" ✅
   ↓
3. Validar "process" in action_matrix ✅
   ↓
4. get_profile("process") → PolicyProfile ✅
   ↓
5. parse_body_by_method(request)
   - Método POST → exige JSON
   - parse "{broken json}" → JSONDecodeError ❌
   → raise GateError(G10_BODY_PARSE_ERROR, 422)
   ↓
6. main.py gate_request() captura GateError:
   - log DecisionRecord(DENY, reason_codes=["G10_BODY_PARSE_ERROR"])
   - re-raise GateError
   ↓
7. HTTP 422 + error envelope
```

---

## Integração com action_matrix e gate_profiles

### Invariante 1:1
**Toda action em `action_matrix.allowed_actions` DEVE ter um PolicyProfile correspondente.**

Validação:
```python
# tests/test_gate_integrity.py
def test_action_matrix_and_profiles_are_1_to_1():
    matrix = get_action_matrix()
    for action in matrix.allowed_actions:
        profile = get_profile(action)
        assert profile is not None, f"Missing profile for action={action}"
```

**Se falhar:** drift de governança detectado.

### Exemplo: Adicionar nova action

1. **Adicionar route em `app/action_router.py`:**
```python
@action_router.post("/my-action")
async def my_action_handler(...):
    ...
```

2. **Adicionar mapeamento em `gate_canonical/action_detector.py`:**
```python
ACTION_MAP = {
    ("/my-action", "POST"): "my_action",
    ...
}
```

3. **Adicionar action ao `action_matrix.py`:**
```python
allowed_actions = ["process", "preferences.delete", "preferences.get", "preferences.put", "my_action"]
```

4. **Adicionar PolicyProfile em `gate_profiles.py`:**
```python
ACTION_MY_ACTION = "my_action"
DEFAULT_PROFILES[ACTION_MY_ACTION] = PolicyProfile(
    id="my_action",
    allowlist={"field1", "field2"},
    allow_external=False,
    deny_unknown_fields=True
)
```

5. **Validar:** `pytest tests/test_gate_integrity.py` ✅

---

## Auditoria

Todos os erros gate geram `DecisionRecord` antes de raise:

```python
decision_record = DecisionRecord(
    decision="DENY",
    profile_id="G8",  # ou "G9", "G10"
    profile_hash=profiles_fingerprint_sha256(),
    matched_rules=["Action 'xyz' not in action matrix"],
    reason_codes=["G8_UNKNOWN_ACTION"],
    input_digest=None,
    trace_id=trace_id,
)
log_decision(decision_record)  # → audit.log
```

**Nome do logger:** `gate_audit` (não `action_audit`, pois gate bloqueia antes de pipeline).

---

## Testes

### Unit tests (test_gate_canonical.py)
- `test_detect_action_*`: 6 testes (4 rotas válidas + 1 unknown + 1 normalize)
- `test_parse_body_*`: 6 testes (GET/DELETE empty, POST valid/invalid/missing)

### Integration test (test_gate_integrity.py)
- `test_action_matrix_and_profiles_are_1_to_1`: Valida 1:1 mapping

**Total:** 12 unit + 1 integration = 13 testes novos (387 passing total).

---

## Métricas de sucesso

### Antes de F11
- G8_UNKNOWN_ACTION: ocorrências esporádicas (rotas novas sem mapping)
- Body parse errors: ad-hoc, status code inconsistente (400 vs 422)
- Audit trail: reason_code em locais variados

### Depois de F11
- G8: eliminado para rotas conhecidas (centralizado em ACTION_MAP)
- Body parse: determinístico, sempre GateError(G10, 422)
- Audit trail: reason_code sempre em `detail["reason_code"]`

**Objetivo:** 0 G8 em produção para rotas mapeadas.

---

## Próximos passos (pós-F11)

1. **ENTREGA 10:** Documentação operational (este arquivo + ACTION_MATRIX.md + TROUBLESHOOTING.md)
2. **CP-11.1:** Human review action_matrix vs gate_profiles
3. **CP-11.2:** Audit logs review (5 sample requests)
4. **CP-11.3:** Smoke tests VPS (6 cenários)
5. **CP-11.4:** SEAL document + tag F11-SEALED

**Refs:**
- [F11-GATE-CONSOLIDATION-PLAN.md](../implementation/F11-GATE-CONSOLIDATION-PLAN.md)
- [ACTION_MATRIX.md](./ACTION_MATRIX.md)
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

