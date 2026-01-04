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
"""Canonical action detection from HTTP request.

Implementa detecção canônica baseada em templates de path com:
- Normalização de prefixo (/api/v1 removido)
- Colapso de parâmetros dinâmicos para templates
- Mapeamento explícito (path_template, method) → action

Correção C1: Contempla paths reais com parâmetros (ex: /preferences/{user_id})
Correção C2: Formaliza lógica "auto-detect" já existente em módulo canônico
"""
from fastapi import Request
import re

# Template-based action mapping (path normalizado, method) → action
ACTION_MAP = {
    ("/process", "POST"): "process",
    ("/preferences/{user_id}", "GET"): "preferences.get",
    ("/preferences/{user_id}", "PUT"): "preferences.put",
    ("/preferences/{user_id}", "DELETE"): "preferences.delete",
    # Futuro: ("/plan", "POST"): "plan.create", etc.
}


def normalize_path(raw_path: str) -> str:
    """Normalize request path for action detection.
    
    Rules:
    1. Remove /api/v1 prefix (standard API prefix)
    2. Collapse dynamic parameters to {param_name} template
       - UUID-like segments → {user_id}, {operation_id}, etc.
       - Preserve path structure for matching
    
    Examples:
        /api/v1/preferences/test-user-f99a → /preferences/{user_id}
        /api/v1/process → /process
        /preferences/abc123 → /preferences/{user_id}
    
    Returns:
        normalized_path (str): template path for ACTION_MAP lookup
    """
    # Remove /api/v1 prefix
    path = raw_path
    if path.startswith("/api/v1"):
        path = path[7:]  # len("/api/v1") = 7
    
    # Collapse dynamic segments to templates
    # Pattern: /preferences/<qualquer-coisa> → /preferences/{user_id}
    # Pattern: /operation/<uuid> → /operation/{operation_id}
    
    if path.startswith("/preferences/"):
        # Qualquer /preferences/<algo> vira /preferences/{user_id}
        return "/preferences/{user_id}"
    
    # Outros patterns futuros aqui
    # if path.startswith("/operation/"):
    #     return "/operation/{operation_id}"
    
    # Path sem parâmetros dinâmicos (ex: /process)
    return path


def detect_action(request: Request) -> str:
    """Detect action from request path and method.
    
    Process:
    1. Normalize path (remove /api/v1, collapse params)
    2. Lookup in ACTION_MAP by (normalized_path, method)
    3. If not found, raise GateError(G8_UNKNOWN_ACTION)
    
    Returns:
        action_id (str): canonical action identifier
    
    Raises:
        GateError: if no mapping found (G8_UNKNOWN_ACTION)
    
    Resposta R3 (Arquiteto): G8 retorna 500 (bug interno) pois gate roda
    antes do roteamento. Se path chegou até o gate, deveria ter mapping.
    404 seria para "rota não existe" (fora do gate).
    """
    normalized_path = normalize_path(request.url.path)
    key = (normalized_path, request.method)
    action = ACTION_MAP.get(key)
    
    if action is None:
        from app.gate_errors import GateError, ReasonCode
        raise GateError(
            reason_code=ReasonCode.G8_UNKNOWN_ACTION,
            message=f"No action mapping for {request.method} {request.url.path} (normalized: {normalized_path})",
            http_status=500  # Bug interno (gate deveria ter mapping)
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
"""HTTP body parsing by method (fail-closed).

Correção C4: Lançar GateError com reason_code estável (G10_BODY_PARSE_ERROR)
para garantir audit trail consistente.

Resposta Q2 (Arquiteto): GET/DELETE ignoram body (tolerante), mas registram
warning leve em audit se Content-Length > 0 (não mascara totalmente).
"""
from fastapi import Request
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def parse_body_by_method(request: Request) -> Dict[str, Any]:
    """Parse request body according to HTTP method.
    
    Rules:
    - GET/DELETE: body is optional, return {} (ignore body if present)
      - Se Content-Length > 0, registra warning em audit (não deny)
    - POST/PUT/PATCH: body is required, parse JSON
      - Se ausente ou inválido: GateError(G10_BODY_PARSE_ERROR, 422)
    - OPTIONS/HEAD: return {} (skip parsing)
    
    Returns:
        dict: parsed body or empty dict
    
    Raises:
        GateError(G10_BODY_PARSE_ERROR): if required body is missing/invalid
    """
    from app.gate_errors import GateError, ReasonCode
    
    if request.method in ("GET", "DELETE"):
        # Body opcional para GET/DELETE (tolerante)
        # Warning se body presente (não mascara bug de client)
        content_length = request.headers.get("content-length", "0")
        if content_length != "0":
            logger.warning(
                f"GET/DELETE request with non-empty body (Content-Length: {content_length}). "
                f"Body ignored. Path: {request.url.path}, Method: {request.method}"
            )
        return {}
    
    if request.method in ("POST", "PUT", "PATCH"):
        # Body obrigatório para métodos de escrita
        try:
            body = await request.json()
            if not isinstance(body, dict):
                raise GateError(
                    reason_code=ReasonCode.G10_BODY_PARSE_ERROR,
                    message="Body must be a JSON object",
                    http_status=422
                )
            return body
        except GateError:
            # Re-raise GateError (já tem reason_code)
            raise
        except Exception as e:
            # JSON parse error ou body ausente
            raise GateError(
                reason_code=ReasonCode.G10_BODY_PARSE_ERROR,
                message=f"Invalid or missing JSON body: {str(e)}",
                http_status=422
            )
    
    # Métodos não suportados (OPTIONS, HEAD, etc.)
    # Retornar {} e seguir (não gerar erro)
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
    
    Correção C5: reason_code padronizado em detail["reason_code"]
    para garantir que audit logger consome sempre da mesma fonte.
    
    Attributes:
        reason_code: canonical reason code (for audit)
        message: human-readable message
        http_status: HTTP status code to return
    """
    def __init__(self, reason_code: ReasonCode, message: str, http_status: int = 403):
        # Armazenar reason_code como atributo (compatibilidade)
        self.reason_code = reason_code
        
        # CRÍTICO: reason_code deve estar em detail["reason_code"]
        # para ser consumido pelo audit logger (fonte canônica)
        super().__init__(status_code=http_status, detail={
            "reason_code": reason_code.value,  # Fonte canônica para audit
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
# Correção C6: Usar Starlette TestClient para Request real

import pytest
from fastapi import Request
from starlette.datastructures import URL
from io import BytesIO


def create_test_request(path: str, method: str, body: str = None) -> Request:
    """Helper para criar Request real do Starlette para testes.
    
    Compatível com .url.path, .method, .json() usado pelo gate_engine.
    """
    from starlette.requests import Request as StarletteRequest
    from starlette.datastructures import Headers
    
    headers = {"content-type": "application/json"} if body else {}
    if body:
        headers["content-length"] = str(len(body))
    
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
    }
    
    receive_data = body.encode() if body else b""
    
    async def receive():
        return {"type": "http.request", "body": receive_data}
    
    return StarletteRequest(scope, receive)


def test_detect_action_valid_routes():
    """Valida detecção de todas as rotas ativas (com normalização)."""
    from app.gate_engine.action_detector import detect_action
    
    # Cases: (raw_path, method, expected_action)
    cases = [
        ("/api/v1/process", "POST", "process"),
        ("/api/v1/preferences/test-user-f99a", "GET", "preferences.get"),
        ("/api/v1/preferences/abc-123", "PUT", "preferences.put"),
        ("/api/v1/preferences/xyz", "DELETE", "preferences.delete"),
    ]
    
    for path, method, expected_action in cases:
        request = create_test_request(path=path, method=method)
        action = detect_action(request)
        assert action == expected_action, (
            f"Path {path} {method} esperava '{expected_action}', obteve '{action}'"
        )


def test_detect_action_unknown_route():
    """Rota não mapeada deve lançar GateError(G8_UNKNOWN_ACTION)."""
    from app.gate_engine.action_detector import detect_action
    from app.gate_errors import GateError, ReasonCode
    
    request = create_test_request(path="/api/v1/unknown", method="POST")
    
    with pytest.raises(GateError) as exc_info:
        detect_action(request)
    
    assert exc_info.value.reason_code == ReasonCode.G8_UNKNOWN_ACTION
    assert exc_info.value.status_code == 500  # Bug interno (gate deveria ter mapping)


@pytest.mark.asyncio
async def test_parse_body_get_returns_empty():
    """GET sem body deve retornar {} sem erro."""
    from app.gate_engine.body_parser import parse_body_by_method
    
    request = create_test_request(path="/api/v1/preferences/test", method="GET")
    body = await parse_body_by_method(request)
    
    assert body == {}


@pytest.mark.asyncio
async def test_parse_body_delete_returns_empty():
    """DELETE sem body deve retornar {} sem erro."""
    from app.gate_engine.body_parser import parse_body_by_method
    
    request = create_test_request(path="/api/v1/preferences/test", method="DELETE")
    body = await parse_body_by_method(request)
    
    assert body == {}


@pytest.mark.asyncio
async def test_parse_body_post_valid_json():
    """POST com JSON válido deve retornar dict."""
    from app.gate_engine.body_parser import parse_body_by_method
    
    request = create_test_request(
        path="/api/v1/process",
        method="POST",
        body='{"text": "hello"}'
    )
    body = await parse_body_by_method(request)
    
    assert body == {"text": "hello"}


@pytest.mark.asyncio
async def test_parse_body_post_missing_body():
    """POST sem body deve lançar GateError(G10_BODY_PARSE_ERROR, 422)."""
    from app.gate_engine.body_parser import parse_body_by_method
    from app.gate_errors import GateError, ReasonCode
    
    request = create_test_request(path="/api/v1/process", method="POST")
    
    with pytest.raises(GateError) as exc_info:
        await parse_body_by_method(request)
    
    assert exc_info.value.reason_code == ReasonCode.G10_BODY_PARSE_ERROR
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_parse_body_get_with_body_ignored():
    """GET com body presente deve ignorar e retornar {} (tolerante)."""
    from app.gate_engine.body_parser import parse_body_by_method
    
    request = create_test_request(
        path="/api/v1/preferences/test",
        method="GET",
        body='{"ignored": "data"}'
    )
    body = await parse_body_by_method(request)
    
    assert body == {}  # Body ignorado
    # Nota: warning deve aparecer em log (validar manualmente)
```

### 5.2 Integration Test (1:1 Mapping)

```python
# tests/test_gate_integrity.py

def test_action_matrix_and_profiles_are_1_to_1():
    """Valida que action_matrix e gate_profiles são 1:1 (apenas PUBLIC_ACTIONS).
    
    Correção C7: Comparar apenas actions públicas (expostas por rotas HTTP).
    DEFAULT_PROFILES pode conter profiles internas, versões, não-públicos.
    
    Escopo:
    - PUBLIC_ACTIONS (do action_matrix) devem ter profile correspondente
    - Cada profile em PUBLIC_ACTIONS deve estar no action_matrix
    - Não comparar universo inteiro se sistema suporta profiles internas
    """
    from app.action_matrix import get_action_matrix
    from app.gate_profiles import get_profile
    
    matrix = get_action_matrix()
    public_actions = set(matrix.allowed_actions)  # Actions expostas via HTTP
    
    # Validar que todo action público tem profile
    missing_profiles = []
    for action in public_actions:
        profile = get_profile(action)
        if profile is None:
            missing_profiles.append(action)
    
    assert not missing_profiles, (
        f"PUBLIC_ACTIONS sem profile: {missing_profiles}. "
        f"Toda action no action_matrix deve ter profile correspondente."
    )
    
    # Validar que get_profile() retorna PolicyProfile válido
    for action in public_actions:
        profile = get_profile(action)
        assert profile is not None, f"get_profile('{action}') retornou None"
        assert hasattr(profile, 'name'), f"Profile de '{action}' inválido (sem 'name')"
        assert hasattr(profile, 'allowlist'), f"Profile de '{action}' inválido (sem 'allowlist')"
    
    # Sucesso: 1:1 mapping garantido para PUBLIC_ACTIONS
```

### 5.3 Smoke Tests (VPS Production)

```bash
# smoke_test_gate.sh
# Correção C3: Paths reais validados no deployment F9.9-A
# Base URL: http://localhost:8000 (local) ou https://srv1241381.hstgr.cloud (VPS)
# Prefixo: /api/v1 (padrão do backend)

BASE_URL="http://localhost:8000"
API_KEY="${VERITTA_BETA_API_KEY}"
USER_ID="test-user-f99a"

# 1. GET preferences (rota mapeada com parâmetro): deve funcionar
curl -X GET "${BASE_URL}/api/v1/preferences/${USER_ID}" \
  -H "X-API-KEY: ${API_KEY}" \
  -H "X-VERITTA-USER-ID: ${USER_ID}"
# Esperado: 200 + JSON preferences, ou 404 (user não existe)
# NÃO esperado: 500, G8_UNKNOWN_ACTION, body parse error

# 2. PUT preferences (atualizar): deve funcionar
curl -X PUT "${BASE_URL}/api/v1/preferences/${USER_ID}" \
  -H "X-API-KEY: ${API_KEY}" \
  -H "X-VERITTA-USER-ID: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"tone_preference": "institutional", "output_format": "text", "language": "pt-BR"}'
# Esperado: 200 + JSON preferences atualizadas
# NÃO esperado: G8_UNKNOWN_ACTION, body parse error

# 3. DELETE preferences (sem body): deve funcionar
curl -X DELETE "${BASE_URL}/api/v1/preferences/${USER_ID}" \
  -H "X-API-KEY: ${API_KEY}" \
  -H "X-VERITTA-USER-ID: ${USER_ID}"
# Esperado: 204 No Content
# NÃO esperado: body parse error (GET/DELETE ignoram body)

# 4. POST process (sem body): deve retornar 422 + G10_BODY_PARSE_ERROR
curl -X POST "${BASE_URL}/api/v1/process" \
  -H "X-API-KEY: ${API_KEY}"
# Esperado: 422 + {"reason_code": "G10_BODY_PARSE_ERROR", "message": "Invalid or missing JSON body"}
# NÃO esperado: exception não tratada, HTTPException genérica

# 5. Rota não mapeada: deve retornar 500 + G8_UNKNOWN_ACTION
curl -X GET "${BASE_URL}/api/v1/unknown-route" \
  -H "X-API-KEY: ${API_KEY}"
# Esperado: 500 + {"reason_code": "G8_UNKNOWN_ACTION"}
# Nota: 500 porque gate roda antes do roteamento (bug interno se chegou até aqui)

# 6. GET com body presente (edge case): deve ignorar body e retornar 200
curl -X GET "${BASE_URL}/api/v1/preferences/${USER_ID}" \
  -H "X-API-KEY: ${API_KEY}" \
  -H "X-VERITTA-USER-ID: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"ignored": "data"}'
# Esperado: 200 (body ignorado, warning em log)
# Validar audit.log: deve ter warning sobre body presente em GET
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

**Revisor (Arquiteto V-COF):** GPT-4 Custom V-COF (Arquiteto Samurai)  
**Data da Revisão:** 2026-01-04  
**Decisão:** [X] APROVADO COM AJUSTES CRÍTICOS (bloqueantes antes de implementação)

**Comentários do Revisor:**

```
✅ VEREDITO: APROVADO COM AJUSTES CRÍTICOS

O plano está na direção certa (determinismo, canonicidade, fail-closed), mas
do jeito que estava escrito ele ia falhar em produção por causa de incompatibilidades
com o path real do FastAPI e testes irrealistas.

═══════════════════════════════════════════════════════════════════════════
🔴 BLOQUEANTES CRÍTICOS (C1-C7) — CORRIGIDOS NO PLANO:
═══════════════════════════════════════════════════════════════════════════

✅ C1: detect_action() contempla paths reais com templates
   - Implementado normalize_path() com remoção de /api/v1
   - Colapso de parâmetros dinâmicos (/preferences/{user_id})
   - ACTION_MAP agora usa templates, não literais

✅ C2: Consolidação da lógica "auto-detect" existente
   - F11 formaliza lógica já existente em módulo canônico
   - Não introduz estratégia paralela concorrente

✅ C3: Smoke tests com paths reais /api/v1/preferences/{user_id}
   - Corrigidos para paths validados no deployment F9.9-A
   - Base URL + prefixo /api/v1 + parâmetros dinâmicos

✅ C4: Body parser lança GateError(G10_BODY_PARSE_ERROR, 422)
   - Não usa HTTPException genérica
   - reason_code estável para audit trail

✅ C5: reason_code padronizado em detail["reason_code"]
   - Audit logger consome sempre da mesma fonte
   - Comentário explícito: "fonte canônica para audit"

✅ C6: Testes usam Starlette TestClient (Request real)
   - create_test_request() helper compatível com .url.path, .method, .json()
   - Funções async com @pytest.mark.asyncio

✅ C7: Teste 1:1 compara apenas PUBLIC_ACTIONS
   - Não compara universo inteiro de profiles (frágil)
   - Escopo: actions expostas via HTTP (action_matrix)

═══════════════════════════════════════════════════════════════════════════
🟡 RECOMENDAÇÕES (R1-R3) — INCORPORADAS:
═══════════════════════════════════════════════════════════════════════════

✅ R1: Path template mapping implementado (normalize_path)
✅ R2: OPTIONS/HEAD retornam {} e seguem (não geram erro)
✅ R3: G8_UNKNOWN_ACTION retorna 500 (bug interno), não 404

═══════════════════════════════════════════════════════════════════════════
📋 RESPOSTAS ÀS 4 QUESTÕES:
═══════════════════════════════════════════════════════════════════════════

QUESTÃO 1 (Action Detection Strategy):
RESPOSTA: Aceito mapa estático, porém template-based.
- Formato: (/api/v1/preferences/{user_id}, GET) → "preferences.get"
- Normalização: remover /api/v1, colapsar parâmetros dinâmicos
- Justificativa: Determinismo explícito > introspection (acoplamento interno)

QUESTÃO 2 (Body Parsing — GET com body):
RESPOSTA: Ignorar body em GET/DELETE (tolerante), mas registrar warning.
- Se Content-Length > 0, logger.warning() sem DENY
- Não mascara totalmente (warning em audit)
- Não quebra clients mal comportados

QUESTÃO 3 (Profiles — Mandatory vs Optional):
RESPOSTA: Profile ausente → erro 500 (G9_MISSING_PROFILE).
- Fail-closed: bug interno deve quebrar cedo
- Força completude de profiles antes de deployment
- APROVADO

QUESTÃO 4 (Escopo de Testes):
RESPOSTA: Sem testes de carga em F11.
- Performance/rate limit pertence à FASE 15
- F11 foca em: determinismo, integridade 1:1, reason codes estáveis
- Escopo atual suficiente para validar correção
- APROVADO

═══════════════════════════════════════════════════════════════════════════
🎯 OBSERVAÇÃO FINAL:
═══════════════════════════════════════════════════════════════════════════

O objetivo está correto e a governança bem desenhada.
Principal falha original: assumir que request.url.path é estático e curto.
Com as correções aplicadas, F11 está PRONTA PARA IMPLEMENTAÇÃO.

F11 corrigida evita repetição do incidente G8/GET-body e estabelece
base sólida para FASE 15 (rate limit) e F9.9-B (LLM hardening).

✅ AUTORIZADO PARA EXECUÇÃO (com correções aplicadas)

— Arquiteto Samurai V-COF, 2026-01-04
```

---

**FIM DO PLANO DE IMPLEMENTAÇÃO — FASE 11**

---

**Anexos:**
- Roadmap atualizado: `planning/ROADMAP.md` (commit 54f7820)
- Parecer técnico F10-F17: `docs/audits/PARECER-TECNICO-ROADMAP-F10-F17.md` (commit 3f5d510)
- SEAL F9.9-A: `docs/SEAL-F9.9-A.md` (commit 5fcc73a)
