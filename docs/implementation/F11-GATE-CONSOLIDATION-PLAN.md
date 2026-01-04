# FASE 11 — Gate Engine Consolidation
## Plano de Implementação para Revisão Crítica (V-COF Adversarial)

**Data:** 2026-01-04  
**Branch:** `stage/f11-gate-consolidation`  
**Autor:** Claude Sonnet 4.5 (Technical Implementer)  
**Revisor esperado:** GPT-4 Custom V-COF (Arquiteto Samurai / Crítica Adversarial)

---

## 1. CONTEXTO E JUSTIFICATIVA

### 1.1 Problema Real Identificado
Durante deployment da F9.9-A (User Preferences), ocorreram **8 bloqueios consecutivos** relacionados ao Gate Engine, incluindo:

- **G8_UNKNOWN_ACTION**: Action `preferences.put` não reconhecida
- **Body Parsing Error**: GET/DELETE falhando ao tentar parse JSON de body vazio
- **Profile Missing**: `get_profile("preferences.put")` retornando `None`
- **Action Detection Ambígua**: Lógica inline em `main.py` sem canonicidade

### 1.2 Causa Raiz
O Gate Engine atual tem **3 pontos de falha arquitetural**:

1. **Detecção de Action não canônica**: 
   - Lógica espalhada em múltiplos locais (`main.py`, routers)
   - Regra de path→action não documentada
   - Ambiguidade entre `/preferences` (path) e `preferences.put` (action)

2. **Profiles vs Action Matrix desacoplados**:
   - `action_matrix.py` tem `["process"]`
   - `gate_profiles.py` tem `ACTION_PROCESS`, `ACTION_AGENT_RUN`, `ACTION_ARCONTE_SIGNAL`
   - **Gap**: não há validação 1:1 entre matriz e profiles
   - **Resultado**: actions permitidas mas sem profile → DENY silencioso

3. **Body Parsing não determinístico**:
   - GET/DELETE tentam parse JSON mesmo com body vazio
   - Falha em `request.json()` gera exception não tratada
   - Falta regra explícita: GET/DELETE = body opcional

### 1.3 Impacto Observado
- **Tempo de deployment**: 3h extras para resolver 8 bloqueios
- **Experiência de desenvolvimento**: 8 commits iterativos (c20c098 → 3ee4e9e)
- **Risco de recorrência**: **ALTO** (próxima rota nova vai repetir)
- **Auditoria comprometida**: UNKNOWN_ACTION não gera log estruturado claro

---

## 2. OBJETIVO DA FASE 11

### 2.1 Objetivo Primário
**Tornar o Gate Engine 100% determinístico, canônico e fail-closed.**

Isso significa:
- Toda rota ativa resolve para uma action válida (zero "unknown action")
- Toda action tem profile correspondente (1:1 mapping)
- Body parsing tem regra explícita por método HTTP
- Erros geram reason_code estável e auditável

### 2.2 Não-Objetivos (Out of Scope)
- ❌ Não vamos refatorar autenticação (F2.1/F2.3)
- ❌ Não vamos adicionar rate limiting (FASE 15)
- ❌ Não vamos adicionar timeout policies (FASE 15)
- ❌ Não vamos adicionar métricas Prometheus (F9.8)
- ❌ Não vamos mudar estrutura de profiles (mantém frozenset)

**Princípio**: cirurgia precisa, escopo fechado, sem side-effects.

---

## 3. ARQUITETURA PROPOSTA

### 3.1 Mapa Atual (Baseline)

```
REQUEST → gate_request() em main.py
          ├─ Detecta action: path.split("/") + method (inline)
          ├─ Busca profile: get_profile(action)
          ├─ Parse body: await request.json() (sempre)
          └─ Chama evaluate_gate()

action_matrix.py: ["process"]
gate_profiles.py: {ACTION_PROCESS, ACTION_AGENT_RUN, ACTION_ARCONTE_SIGNAL}

GAP: action matrix ≠ profiles (desacoplado)
GAP: body parsing não condicional (GET/DELETE falham)
GAP: action detection não canônica (lógica inline)
```

### 3.2 Arquitetura Alvo (FASE 11)

```
REQUEST → gate_request() em main.py
          ├─ Detecta action: action_detector.detect_action(request) [NOVO]
          │   └─ Lógica canônica: (path, method) → action
          │   └─ Documentado: ACTION_MATRIX.md
          │
          ├─ Valida action: assert action in action_matrix [NOVO]
          │   └─ Se ausente: raise GateError(G8_UNKNOWN_ACTION)
          │
          ├─ Busca profile: get_profile(action)
          │   └─ Se ausente: raise GateError(G9_MISSING_PROFILE) [NOVO]
          │
          ├─ Parse body: parse_body_by_method(request) [NOVO]
          │   └─ GET/DELETE: return {}
          │   └─ POST/PUT/PATCH: await request.json() + validação
          │
          └─ Chama evaluate_gate()

action_matrix.py: ["process", "preferences.get", "preferences.put", "preferences.delete"]
gate_profiles.py: {ACTION_PROCESS, PREFERENCES_GET, PREFERENCES_PUT, PREFERENCES_DELETE}

GARANTIA: action matrix = profiles (1:1, validado por teste)
GARANTIA: body parsing determinístico (regra por método)
GARANTIA: action detection canônica (função única)
```

### 3.3 Novos Componentes

#### 3.3.1 `app/gate_engine/action_detector.py`
```python
"""Canonical action detection from HTTP request."""
from fastapi import Request

ACTION_MAP = {
    ("/process", "POST"): "process",
    ("/preferences", "GET"): "preferences.get",
    ("/preferences", "PUT"): "preferences.put",
    ("/preferences", "DELETE"): "preferences.delete",
    # Futuro: ("/plan", "POST"): "plan.create", etc.
}

def detect_action(request: Request) -> str:
    """Detect action from request path and method.
    
    Returns:
        action_id (str): canonical action identifier
    
    Raises:
        GateError: if no mapping found (G8_UNKNOWN_ACTION)
    """
    key = (request.url.path, request.method)
    action = ACTION_MAP.get(key)
    
    if action is None:
        from app.gate_errors import GateError, ReasonCode
        raise GateError(
            reason_code=ReasonCode.G8_UNKNOWN_ACTION,
            message=f"No action mapping for {request.method} {request.url.path}",
            http_status=404
        )
    
    return action
```

**Justificativa:**
- Mapa explícito (path, method) → action
- Fail-closed: sem mapping → exception clara
- Documentável: ACTION_MAP é auto-explicativo
- Testável: mapa pequeno, casos finitos

#### 3.3.2 `app/gate_engine/body_parser.py`
```python
"""HTTP body parsing by method (fail-closed)."""
from fastapi import Request, HTTPException
from typing import Dict, Any

async def parse_body_by_method(request: Request) -> Dict[str, Any]:
    """Parse request body according to HTTP method.
    
    Rules:
    - GET/DELETE: body is optional, return {}
    - POST/PUT/PATCH: body is required, parse JSON
    
    Returns:
        dict: parsed body or empty dict
    
    Raises:
        HTTPException(422): if required body is missing/invalid
    """
    if request.method in ("GET", "DELETE"):
        # Body optional for GET/DELETE
        return {}
    
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.json()
            if not isinstance(body, dict):
                raise HTTPException(
                    status_code=422,
                    detail="Body must be a JSON object"
                )
            return body
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid JSON body: {str(e)}"
            )
    
    # Métodos não suportados (OPTIONS, HEAD, etc.)
    return {}
```

**Justificativa:**
- Regra explícita por método HTTP
- Fail-closed: POST sem body → 422 (não tenta adivinhar)
- Sem ambiguidade: GET/DELETE sempre retornam `{}`
- Testável: 5 casos (GET, DELETE, POST ok, POST fail, método raro)

#### 3.3.3 `app/gate_errors.py`
```python
"""Gate-specific exceptions with reason codes."""
from enum import Enum
from fastapi import HTTPException

class ReasonCode(str, Enum):
    """Canonical reason codes for gate failures."""
    G0_AUTH_NOT_CONFIGURED = "G0_AUTH_NOT_CONFIGURED"
    G8_UNKNOWN_ACTION = "G8_UNKNOWN_ACTION"
    G9_MISSING_PROFILE = "G9_MISSING_PROFILE"
    G10_BODY_PARSE_ERROR = "G10_BODY_PARSE_ERROR"
    G11_INVALID_PAYLOAD = "G11_INVALID_PAYLOAD"

class GateError(HTTPException):
    """Exception for gate failures (fail-closed).
    
    Attributes:
        reason_code: canonical reason code (for audit)
        message: human-readable message
        http_status: HTTP status code to return
    """
    def __init__(self, reason_code: ReasonCode, message: str, http_status: int = 403):
        self.reason_code = reason_code
        super().__init__(status_code=http_status, detail={
            "reason_code": reason_code.value,
            "message": message,
            "type": "gate_error"
        })
```

**Justificativa:**
- Reason codes estáveis (auditoria depende deles)
- Exception tipada (não é genérico HTTPException)
- Fail-closed: sempre retorna estrutura conhecida
- Extensível: novos codes sem quebrar existentes

#### 3.3.4 Mudanças em `app/action_matrix.py`
```python
# Adicionar actions de preferences ao default
return ActionMatrix(
    profile="default",
    allowed_actions=[
        "process",
        "preferences.get",
        "preferences.put",
        "preferences.delete",
    ],
)
```

#### 3.3.5 Mudanças em `app/gate_profiles.py`
```python
# Adicionar profiles para preferences
ACTION_PREFERENCES_GET = "preferences.get"
ACTION_PREFERENCES_PUT = "preferences.put"
ACTION_PREFERENCES_DELETE = "preferences.delete"

DEFAULT_PROFILES: Dict[str, PolicyProfile] = {
    # ... profiles existentes ...
    ACTION_PREFERENCES_GET: PolicyProfile(
        name="preferences_get.v1",
        allowlist=frozenset({"user_id"}),
        deny_unknown_fields=True,
        allow_external=False,
    ),
    ACTION_PREFERENCES_PUT: PolicyProfile(
        name="preferences_put.v1",
        allowlist=frozenset({"user_id", "tone_preference", "output_format", "language"}),
        deny_unknown_fields=True,
        allow_external=False,
    ),
    ACTION_PREFERENCES_DELETE: PolicyProfile(
        name="preferences_delete.v1",
        allowlist=frozenset({"user_id"}),
        deny_unknown_fields=True,
        allow_external=False,
    ),
}
```

#### 3.3.6 Mudanças em `app/main.py` (gate_request)
```python
async def gate_request(request: Request, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    # ... auth checks existentes ...
    
    # NOVO: Detectar action de forma canônica
    from app.gate_engine.action_detector import detect_action
    action = detect_action(request)  # Pode lançar GateError(G8)
    
    # NOVO: Validar que action está no action_matrix
    action_matrix = get_action_matrix()
    if action not in action_matrix.allowed_actions:
        raise GateError(
            reason_code=ReasonCode.G8_UNKNOWN_ACTION,
            message=f"Action '{action}' not in action matrix",
            http_status=403
        )
    
    # NOVO: Validar que profile existe
    profile = get_profile(action)
    if profile is None:
        raise GateError(
            reason_code=ReasonCode.G9_MISSING_PROFILE,
            message=f"No profile defined for action '{action}'",
            http_status=500  # Internal error, not user fault
        )
    
    # NOVO: Parse body de forma determinística
    from app.gate_engine.body_parser import parse_body_by_method
    body = await parse_body_by_method(request)
    
    # ... resto da lógica de gate ...
```

---

## 4. CHECKLIST DE IMPLEMENTAÇÃO (10 ENTREGAS)

### ✅ ENTREGA 1: Criar módulo `app/gate_engine/`
- [ ] Criar diretório `app/gate_engine/`
- [ ] Criar `__init__.py` (importa action_detector, body_parser)
- [ ] **Checkpoint CP-11.0**: Revisar estrutura de diretórios (1 min)

### ✅ ENTREGA 2: Implementar `action_detector.py`
- [ ] Criar `app/gate_engine/action_detector.py`
- [ ] Implementar `detect_action(request: Request) -> str`
- [ ] Documentar ACTION_MAP com todas rotas ativas
- [ ] Adicionar docstring detalhada
- [ ] **Checkpoint CP-11.1**: Revisar lógica de detecção (5 min)

### ✅ ENTREGA 3: Implementar `body_parser.py`
- [ ] Criar `app/gate_engine/body_parser.py`
- [ ] Implementar `parse_body_by_method(request: Request) -> Dict`
- [ ] Regra GET/DELETE: retornar `{}`
- [ ] Regra POST/PUT/PATCH: parse JSON obrigatório
- [ ] Tratamento de erro: 422 com mensagem clara
- [ ] **Checkpoint CP-11.2**: Revisar regras de parsing (5 min)

### ✅ ENTREGA 4: Implementar `gate_errors.py`
- [ ] Criar `app/gate_errors.py`
- [ ] Enum `ReasonCode` com G0, G8, G9, G10, G11
- [ ] Classe `GateError(HTTPException)`
- [ ] Documentar cada reason code
- [ ] **Checkpoint CP-11.3**: Revisar reason codes (3 min)

### ✅ ENTREGA 5: Atualizar `action_matrix.py`
- [ ] Adicionar `preferences.get`, `preferences.put`, `preferences.delete`
- [ ] Manter `process` existente
- [ ] Validar que lista está ordenada (legibilidade)
- [ ] **Checkpoint CP-11.4**: Revisar matriz completa (3 min)

### ✅ ENTREGA 6: Atualizar `gate_profiles.py`
- [ ] Adicionar constantes `ACTION_PREFERENCES_{GET,PUT,DELETE}`
- [ ] Criar 3 profiles com allowlists corretos
- [ ] Validar que allowlist reflete schemas Pydantic
- [ ] **Checkpoint CP-11.5**: Revisar profiles vs schemas (5 min)

### ✅ ENTREGA 7: Atualizar `main.py` (gate_request)
- [ ] Importar `detect_action`, `parse_body_by_method`, `GateError`
- [ ] Substituir lógica inline por `detect_action(request)`
- [ ] Adicionar validação: action in action_matrix
- [ ] Adicionar validação: profile is not None
- [ ] Substituir `request.json()` por `parse_body_by_method(request)`
- [ ] **Checkpoint CP-11.6**: Revisar fluxo completo de gate_request (10 min)

### ✅ ENTREGA 8: Criar testes `tests/test_gate_engine.py`
- [ ] Teste: detect_action() com 4 rotas válidas
- [ ] Teste: detect_action() com rota inválida → G8_UNKNOWN_ACTION
- [ ] Teste: parse_body GET → `{}`
- [ ] Teste: parse_body DELETE → `{}`
- [ ] Teste: parse_body POST com JSON válido → dict
- [ ] Teste: parse_body POST sem body → 422
- [ ] Teste: action não no action_matrix → G8_UNKNOWN_ACTION
- [ ] Teste: profile ausente → G9_MISSING_PROFILE
- [ ] **Checkpoint CP-11.7**: Executar testes localmente (5 min)

### ✅ ENTREGA 9: Criar teste de integração 1:1
- [ ] Teste: validar que `action_matrix.allowed_actions` = `gate_profiles.DEFAULT_PROFILES.keys()`
- [ ] Teste: para cada action no matrix, `get_profile(action)` não é None
- [ ] Teste: para cada profile, action está no matrix
- [ ] **Checkpoint CP-11.8**: Validar 1:1 mapping (3 min)

### ✅ ENTREGA 10: Documentação operacional
- [ ] Criar `docs/gate/GATE_ENGINE_SPEC.md` (arquitetura + fluxo)
- [ ] Criar `docs/gate/ACTION_MATRIX.md` (mapa completo path/method → action)
- [ ] Criar `docs/gate/TROUBLESHOOTING.md` (runbook de erros comuns)
- [ ] Atualizar ROADMAP.md com status "EM EXECUÇÃO"
- [ ] **Checkpoint CP-11.9**: Revisar documentação (10 min)

---

## 5. TESTES CRÍTICOS (FAIL-CLOSED)

### 5.1 Unit Tests (app/gate_engine/)

```python
# tests/test_gate_engine.py

def test_detect_action_valid_routes():
    """Valida detecção de todas as rotas ativas."""
    from app.gate_engine.action_detector import detect_action
    from fastapi import Request
    
    cases = [
        ("/process", "POST", "process"),
        ("/preferences", "GET", "preferences.get"),
        ("/preferences", "PUT", "preferences.put"),
        ("/preferences", "DELETE", "preferences.delete"),
    ]
    
    for path, method, expected_action in cases:
        request = mock_request(path=path, method=method)
        assert detect_action(request) == expected_action


def test_detect_action_unknown_route():
    """Rota não mapeada deve lançar GateError(G8)."""
    from app.gate_engine.action_detector import detect_action
    from app.gate_errors import GateError, ReasonCode
    
    request = mock_request(path="/unknown", method="POST")
    
    with pytest.raises(GateError) as exc_info:
        detect_action(request)
    
    assert exc_info.value.reason_code == ReasonCode.G8_UNKNOWN_ACTION
    assert exc_info.value.status_code == 404


def test_parse_body_get_returns_empty():
    """GET sem body deve retornar {} sem erro."""
    from app.gate_engine.body_parser import parse_body_by_method
    
    request = mock_request(method="GET", body=None)
    body = await parse_body_by_method(request)
    
    assert body == {}


def test_parse_body_delete_returns_empty():
    """DELETE sem body deve retornar {} sem erro."""
    from app.gate_engine.body_parser import parse_body_by_method
    
    request = mock_request(method="DELETE", body=None)
    body = await parse_body_by_method(request)
    
    assert body == {}


def test_parse_body_post_valid_json():
    """POST com JSON válido deve retornar dict."""
    from app.gate_engine.body_parser import parse_body_by_method
    
    request = mock_request(method="POST", body='{"text": "hello"}')
    body = await parse_body_by_method(request)
    
    assert body == {"text": "hello"}


def test_parse_body_post_missing_body():
    """POST sem body deve lançar HTTPException(422)."""
    from app.gate_engine.body_parser import parse_body_by_method
    from fastapi import HTTPException
    
    request = mock_request(method="POST", body=None)
    
    with pytest.raises(HTTPException) as exc_info:
        await parse_body_by_method(request)
    
    assert exc_info.value.status_code == 422
```

### 5.2 Integration Test (1:1 Mapping)

```python
# tests/test_gate_integrity.py

def test_action_matrix_and_profiles_are_1_to_1():
    """Valida que action_matrix e gate_profiles são 1:1."""
    from app.action_matrix import get_action_matrix
    from app.gate_profiles import get_profile, DEFAULT_PROFILES
    
    matrix = get_action_matrix()
    matrix_actions = set(matrix.allowed_actions)
    profile_actions = set(DEFAULT_PROFILES.keys())
    
    # Validar que todo action no matrix tem profile
    missing_profiles = matrix_actions - profile_actions
    assert not missing_profiles, f"Actions sem profile: {missing_profiles}"
    
    # Validar que todo profile tem action no matrix
    orphaned_profiles = profile_actions - matrix_actions
    assert not orphaned_profiles, f"Profiles sem action: {orphaned_profiles}"
    
    # Validar que get_profile() funciona para todos
    for action in matrix_actions:
        profile = get_profile(action)
        assert profile is not None, f"get_profile('{action}') retornou None"
```

### 5.3 Smoke Tests (VPS Production)

```bash
# smoke_test_gate.sh

# 1. Rota mapeada: deve funcionar
curl -X GET https://techno-os.veritta.digital/preferences \
  -H "X-API-KEY: $API_KEY" \
  -H "X-VERITTA-USER-ID: test-user"
# Esperado: 200 ou 404 (user não existe), não 500 ou G8

# 2. Rota não mapeada: deve retornar 404 + G8_UNKNOWN_ACTION
curl -X GET https://techno-os.veritta.digital/unknown \
  -H "X-API-KEY: $API_KEY"
# Esperado: 404 + {"reason_code": "G8_UNKNOWN_ACTION"}

# 3. GET sem body: deve funcionar
curl -X GET https://techno-os.veritta.digital/process \
  -H "X-API-KEY: $API_KEY"
# Esperado: 400 ou 422 (por outras razões), não body parse error

# 4. DELETE sem body: deve funcionar
curl -X DELETE https://techno-os.veritta.digital/preferences \
  -H "X-API-KEY: $API_KEY" \
  -H "X-VERITTA-USER-ID: test-user"
# Esperado: 204 ou 404, não body parse error

# 5. POST sem body: deve retornar 422
curl -X POST https://techno-os.veritta.digital/process \
  -H "X-API-KEY: $API_KEY"
# Esperado: 422 + mensagem clara sobre body obrigatório
```

---

## 6. CRITÉRIOS DE SEAL (FAIL-CLOSED)

### ✅ CRITÉRIO 1: Zero G8_UNKNOWN_ACTION em rotas ativas
- Executar smoke tests no VPS
- Validar que todas as 4 rotas retornam action válida
- Log: zero ocorrências de G8 em audit.log

### ✅ CRITÉRIO 2: Zero body parse error em GET/DELETE
- Executar testes unitários: GET/DELETE → `{}`
- Executar smoke tests: GET/DELETE funcionam sem body
- Log: zero ocorrências de "body parse error" em audit.log

### ✅ CRITÉRIO 3: Action Matrix = Gate Profiles (1:1)
- Executar teste de integridade: `test_action_matrix_and_profiles_are_1_to_1()`
- Validar que teste passa: 0 actions órfãs, 0 profiles órfãos

### ✅ CRITÉRIO 4: Non-Regression (404+ testes)
- Executar suite completa: `pytest`
- Validar: 404+ testes (mantém baseline + adiciona 12+)
- Cobertura: gate/ deve ter >90%

### ✅ CRITÉRIO 5: Documentação Operacional Completa
- `docs/gate/GATE_ENGINE_SPEC.md` existe e está completo
- `docs/gate/ACTION_MATRIX.md` documenta todas as rotas
- `docs/gate/TROUBLESHOOTING.md` tem runbook de G8, G9, G10

### ✅ CRITÉRIO 6: Auditoria Estruturada
- Todo DENY gera entrada em `audit.log` com reason_code
- Formato: `{"decision": "DENY", "reason_code": "G8_UNKNOWN_ACTION", "action": "...", "trace_id": "..."}`
- Validar que logs são parseáveis e completos

---

## 7. CHECKPOINTS HUMANOS (4 OBRIGATÓRIOS)

### 🔍 CP-11.1 — Revisar Matriz de Actions vs Profiles
**Quando:** Após entregas 5 e 6 (action_matrix.py + gate_profiles.py atualizados)  
**O quê:** Validar que:
- Toda action no matrix tem profile correspondente
- Toda profile tem action no matrix
- Allowlists refletem schemas Pydantic (preferences.py)

**Aprovação:** Arquiteto V-COF deve confirmar que não há gaps

---

### 🔍 CP-11.2 — Revisar Logs de Auditoria (Sample)
**Quando:** Após entrega 7 (main.py atualizado)  
**O quê:** Executar 5 requests locais e inspecionar `audit.log`:
1. Request válido → ALLOW
2. Request com rota não mapeada → DENY + G8_UNKNOWN_ACTION
3. Request com profile ausente → DENY + G9_MISSING_PROFILE
4. GET sem body → ALLOW (não falha em parse)
5. POST sem body → DENY (422) + log estruturado

**Aprovação:** Logs devem ter reason_code, trace_id, timestamp

---

### 🔍 CP-11.3 — Executar Smoke Tests no VPS
**Quando:** Após entrega 10 (deployment no VPS)  
**O quê:** Executar `smoke_test_gate.sh` no VPS:
- 4 rotas válidas funcionam
- 1 rota inválida retorna G8_UNKNOWN_ACTION
- GET/DELETE sem body funcionam
- POST sem body retorna 422

**Aprovação:** Zero falhas, logs em `/app/logs/audit.log` consistentes

---

### 🔍 CP-11.4 — Revisar SEAL Document + Aprovar Tag
**Quando:** Após todas as entregas + smoke tests
**O quê:** Revisar `docs/SEAL-F11.md`:
- Arquitetura documentada (action_detector, body_parser, gate_errors)
- Testes documentados (unit + integration + smoke)
- Evidências: commits, testes passando, logs
- Lições aprendidas: o que evitar no futuro

**Aprovação:** Tag `F11-SEALED` só após aprovação humana

---

## 8. RISCOS E MITIGAÇÕES

### 🔴 RISCO 1: Quebrar rotas existentes (`/process`)
**Probabilidade:** BAIXA  
**Impacto:** ALTO (produção para de funcionar)  
**Mitigação:**
- Manter lógica existente de `/process` intacta
- Adicionar apenas novas rotas (preferences)
- Executar non-regression: 404+ testes devem passar
- Smoke test em staging antes de VPS

### 🟡 RISCO 2: Action detection não cobrir casos futuros
**Probabilidade:** MÉDIA  
**Impacto:** MÉDIO (novas rotas vão repetir G8)  
**Mitigação:**
- Documentar ACTION_MAP em `ACTION_MATRIX.md`
- Criar teste que valida "rotas ativas vs ACTION_MAP"
- Adicionar checklist: "toda nova rota exige entrada no ACTION_MAP"

### 🟢 RISCO 3: Body parsing quebrar em edge cases (multipart, etc.)
**Probabilidade:** BAIXA  
**Impacto:** BAIXO (não usamos multipart hoje)  
**Mitigação:**
- Escopo atual: apenas JSON
- Documentar em `BODY_PARSING_RULES.md`: "apenas JSON suportado"
- Futuro: adicionar multipart se necessário (fora de F11)

### 🟡 RISCO 4: Profiles muito restritivos (deny legítimos)
**Probabilidade:** MÉDIA  
**Impacto:** MÉDIO (UX degradada, requests válidos negados)  
**Mitigação:**
- Copiar allowlists exatamente dos schemas Pydantic
- Testar com requests reais (smoke tests)
- Checkpoint CP-11.1: revisar allowlists antes de deployment

---

## 9. ESTIMATIVA DE TEMPO

### Breakdown por Entrega

| Entrega | Descrição | Estimativa |
|---------|-----------|------------|
| 1 | Criar módulo gate_engine/ | 5 min |
| 2 | Implementar action_detector.py | 30 min |
| 3 | Implementar body_parser.py | 30 min |
| 4 | Implementar gate_errors.py | 20 min |
| 5 | Atualizar action_matrix.py | 10 min |
| 6 | Atualizar gate_profiles.py | 20 min |
| 7 | Atualizar main.py (gate_request) | 45 min |
| 8 | Criar testes (test_gate_engine.py) | 60 min |
| 9 | Criar teste de integridade 1:1 | 15 min |
| 10 | Documentação operacional | 45 min |
| **SUBTOTAL IMPLEMENTAÇÃO** | | **4h 20min** |
| Checkpoints humanos (4) | | 40 min |
| Smoke tests VPS | | 20 min |
| Buffer (imprevistos) | | 40 min |
| **TOTAL** | | **6h** |

### Distribuição Recomendada
- **Sessão 1** (2h): Entregas 1-4 + CP-11.0 a CP-11.3
- **Sessão 2** (2h): Entregas 5-7 + CP-11.4 a CP-11.6
- **Sessão 3** (2h): Entregas 8-10 + CP-11.7 a CP-11.9 + smoke tests + SEAL

---

## 10. QUESTÕES PARA REVISÃO CRÍTICA (ARQUITETO SAMURAI)

### 🎯 QUESTÃO 1: Action Detection Strategy
**Proposta:** Mapa estático `(path, method) → action` em `action_detector.py`

**Alternativa considerada:** Detectar via router introspection (FastAPI routes)

**Trade-off:**
- ✅ **PRO (mapa estático):** Explícito, simples, testável, sem side-effects
- ❌ **CON (mapa estático):** Precisa atualizar manual ao adicionar rotas
- ✅ **PRO (router introspection):** Auto-atualiza, sem manutenção manual
- ❌ **CON (router introspection):** Acoplamento com FastAPI internals, mais complexo

**Pergunta:** Aceitas mapa estático ou preferes introspection?

---

### 🎯 QUESTÃO 2: Body Parsing — GET com Body
**Proposta:** GET sempre retorna `{}`, mesmo se body presente (ignorar)

**Alternativa considerada:** GET com body → erro 400 (body não permitido)

**Trade-off:**
- ✅ **PRO (ignorar):** Tolerante, não quebra clients mal comportados
- ❌ **CON (ignorar):** Pode mascarar bugs no client
- ✅ **PRO (erro 400):** Fail-closed, reforça spec HTTP
- ❌ **CON (erro 400):** Pode quebrar integrações existentes

**Pergunta:** Ignorar body em GET ou lançar erro?

---

### 🎯 QUESTÃO 3: Profiles — Mandatory vs Optional
**Proposta:** Profile ausente → erro 500 (G9_MISSING_PROFILE)

**Alternativa considerada:** Profile ausente → usar profile padrão vazio

**Trade-off:**
- ✅ **PRO (erro 500):** Fail-closed, força completude de profiles
- ❌ **CON (erro 500):** Deployment quebra se esquecer profile
- ✅ **PRO (profile padrão):** Deployment não quebra
- ❌ **CON (profile padrão):** Pode permitir actions sem governança

**Pergunta:** Erro 500 ou profile padrão vazio?

---

### 🎯 QUESTÃO 4: Escopo de Testes
**Proposta:** 12 unit tests + 1 integration test + 5 smoke tests

**Alternativa considerada:** Adicionar testes de carga (100 req/s)

**Trade-off:**
- ✅ **PRO (escopo atual):** Suficiente para validar correção
- ❌ **CON (escopo atual):** Não valida performance
- ✅ **PRO (testes de carga):** Valida que gate aguenta carga
- ❌ **CON (testes de carga):** Escopo explode, tempo 2x (FASE 15 trata isso)

**Pergunta:** Testes de carga em F11 ou deixar para FASE 15?

---

## 11. PRÓXIMOS PASSOS (PÓS REVISÃO)

### Se aprovado sem mudanças:
1. Iniciar implementação: Entrega 1 (criar módulo gate_engine/)
2. Seguir checklist: 10 entregas + 4 checkpoints
3. Executar testes: unit + integration + smoke
4. Criar SEAL: `docs/SEAL-F11.md`
5. Tag: `F11-SEALED`

### Se aprovado com ajustes:
1. Implementar ajustes sugeridos pelo arquiteto
2. Re-validar arquitetura com checklist revisado
3. Seguir fluxo normal (testes → SEAL → tag)

### Se rejeitado:
1. Entender objeções críticas
2. Reformular arquitetura
3. Re-submeter plano revisado

---

## 12. ASSINATURA E APROVAÇÃO

**Autor (Implementer):** Claude Sonnet 4.5  
**Data:** 2026-01-04  
**Status:** 🟡 AGUARDANDO REVISÃO CRÍTICA

**Revisor (Arquiteto V-COF):** _____________  
**Data da Revisão:** _____________  
**Decisão:** [ ] APROVADO [ ] APROVADO COM AJUSTES [ ] REJEITADO

**Comentários do Revisor:**

```
(Espaço para crítica adversarial — questões, objeções, sugestões)

QUESTÃO 1 (Action Detection):
RESPOSTA: 

QUESTÃO 2 (Body Parsing):
RESPOSTA: 

QUESTÃO 3 (Profiles Mandatory):
RESPOSTA: 

QUESTÃO 4 (Escopo de Testes):
RESPOSTA: 

OUTRAS OBJEÇÕES:
```

---

**FIM DO PLANO DE IMPLEMENTAÇÃO — FASE 11**

---

**Anexos:**
- Roadmap atualizado: `planning/ROADMAP.md` (commit 54f7820)
- Parecer técnico F10-F17: `docs/audits/PARECER-TECNICO-ROADMAP-F10-F17.md` (commit 3f5d510)
- SEAL F9.9-A: `docs/SEAL-F9.9-A.md` (commit 5fcc73a)
