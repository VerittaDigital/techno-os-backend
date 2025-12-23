# AG-03 IMPLEMENTATION GUIDE — EXTRAÇÃO FACTUAL

**Data:** 21 de dezembro de 2025  
**Status:** Fonte de verdade para implementação de AG-03  
**Fonte:** Análise direta do repositório sem invenções

---

## 1. ENUMERAÇÃO DOS 12 RED TESTS (FONTE DE VERDADE)

### 1.1 Action Version Validation (3 tests)

**Arquivo:** `tests/test_action_versioning_red.py`

#### Test 1: `test_action_without_version_blocked`
- **Caminho:** `tests/test_action_versioning_red.py` linhas 90-108
- **Cenário:** ActionRegistry registra action sem campo action_version
- **Resultado esperado:** BLOCKED
- **reason_codes esperados:** `["ACTION_VERSION_MISSING"]`
- **Pré-condição:** action_meta.get("action_version") == None

#### Test 2: `test_action_with_invalid_version_blocked`
- **Caminho:** `tests/test_action_versioning_red.py` linhas 110-127
- **Cenário:** ActionRegistry registra action com action_version="v1" (não-semver)
- **Resultado esperado:** BLOCKED
- **reason_codes esperados:** `["ACTION_VERSION_INVALID"]`
- **Pré-condição:** action_version existe mas não match SEMVER_REGEX (^\\d+\\.\\d+\\.\\d+$)

#### Test 3: `test_action_with_valid_version_not_blocked_by_version`
- **Caminho:** `tests/test_action_versioning_red.py` linhas 129-154
- **Cenário:** ActionRegistry registra action com action_version="1.0.0" (válido)
- **Resultado esperado:** NÃO BLOCKED (por razão de versão)
- **reason_codes esperados:** NÃO contém `["ACTION_VERSION_MISSING", "ACTION_VERSION_INVALID"]`
- **Pré-condição:** action_version="1.0.0" (match SEMVER)

---

### 1.2 Executor Version Compatibility (4 tests)

**Arquivo:** `tests/test_executor_versioning_red.py`

#### Test 4: `test_executor_without_version_blocked`
- **Caminho:** `tests/test_executor_versioning_red.py` linhas 91-127
- **Cenário:** Executor registrado sem atributo version; action requer min_executor_version="1.1.0"
- **Resultado esperado:** BLOCKED
- **reason_codes esperados:** `["EXECUTOR_VERSION_MISSING"]`
- **Pré-condição:** executor.version = None ou atributo ausente; action.min_executor_version="1.1.0"

#### Test 5: `test_executor_with_incompatible_version_blocked`
- **Caminho:** `tests/test_executor_versioning_red.py` linhas 125-160
- **Cenário:** executor.version="1.0.0" < action.min_executor_version="1.1.0"
- **Resultado esperado:** BLOCKED
- **reason_codes esperados:** `["EXECUTOR_VERSION_INCOMPATIBLE"]`
- **Pré-condição:** _compare_semver("1.0.0", "1.1.0") < 0 == True
- **Detalhe:** Usa packaging.version.Version para comparação correta (não lexicográfica)

#### Test 6: `test_executor_with_compatible_version_not_blocked`
- **Caminho:** `tests/test_executor_versioning_red.py` linhas 159-188
- **Cenário:** executor.version="1.1.0" == action.min_executor_version="1.1.0"
- **Resultado esperado:** NÃO BLOCKED (por versão)
- **reason_codes esperados:** NÃO contém `["EXECUTOR_VERSION_MISSING", "EXECUTOR_VERSION_INCOMPATIBLE"]`
- **Pré-condição:** _compare_semver("1.1.0", "1.1.0") == 0

#### Test 7: `test_executor_with_newer_version_not_blocked`
- **Caminho:** `tests/test_executor_versioning_red.py` linhas 193-226
- **Cenário:** executor.version="1.2.0" > action.min_executor_version="1.1.0"
- **Resultado esperado:** NÃO BLOCKED (por versão)
- **reason_codes esperados:** NÃO contém `["EXECUTOR_VERSION_MISSING", "EXECUTOR_VERSION_INCOMPATIBLE"]`
- **Pré-condição:** _compare_semver("1.2.0", "1.1.0") > 0

---

### 1.3 Executor Capabilities (3 tests)

**Arquivo:** `tests/test_executor_capabilities_red.py`

#### Test 8: `test_executor_without_capabilities_blocked`
- **Caminho:** `tests/test_executor_capabilities_red.py` linhas 90-117
- **Cenário:** Executor sem atributo capabilities; action requer ["TEXT_PROCESSING"]
- **Resultado esperado:** BLOCKED
- **reason_codes esperados:** `["EXECUTOR_CAPABILITY_MISSING"]`
- **Pré-condição:** executor.capabilities = None ou atributo ausente

#### Test 9: `test_executor_with_insufficient_capabilities_blocked`
- **Caminho:** `tests/test_executor_capabilities_red.py` linhas 123-155
- **Cenário:** action requer ["TEXT_PROCESSING", "LOGGING"]; executor tem ["TEXT_PROCESSING"]
- **Resultado esperado:** BLOCKED
- **reason_codes esperados:** `["EXECUTOR_CAPABILITY_MISMATCH"]`
- **Pré-condição:** set(required) - set(executor) != {}

#### Test 10: `test_executor_compatible_not_blocked_by_capabilities`
- **Caminho:** `tests/test_executor_capabilities_red.py` linhas 158-190
- **Cenário:** action requer ["TEXT_PROCESSING", "LOGGING"]; executor tem ["AUDIT_LOGGING", "LOGGING", "TEXT_PROCESSING"]
- **Resultado esperado:** NÃO BLOCKED (por capacidade)
- **reason_codes esperados:** NÃO contém `["EXECUTOR_CAPABILITY_MISSING", "EXECUTOR_CAPABILITY_MISMATCH"]`
- **Pré-condição:** set(required) ⊆ set(executor_caps_normalized)

---

### 1.4 Legacy Action Retrocompatibility (2 tests)

**Arquivo:** `tests/test_ag03_retrocompat_red.py`

#### Test 11: `test_action_process_without_version_continues`
- **Caminho:** `tests/test_ag03_retrocompat_red.py` linhas 23-51
- **Cenário:** action="process" (em LEGACY_ACTIONS) sem action_version
- **Resultado esperado:** NÃO BLOCKED (by version, legacy bypass)
- **reason_codes esperados:** NÃO contém `["ACTION_VERSION_MISSING"]`
- **Detalhe:** LEGACY_ACTIONS = {"process"} permite execução sem validação AG-03

#### Test 12: `test_executor_without_capabilities_legacy_mode`
- **Caminho:** `tests/test_ag03_retrocompat_red.py` linhas 53-99
- **Cenário:** action="process" (legacy) sem required_capabilities especificadas
- **Resultado esperado:** NÃO BLOCKED (by capability, legacy)
- **reason_codes esperados:** NÃO contém `["EXECUTOR_CAPABILITY_MISSING"]`
- **Detalhe:** Legacy actions bypass validation, nada é requerido

---

## 2. TRECHOS DOS RED TESTS (CÓPIA INTEGRAL)

### test_action_versioning_red.py — Test 1

```python
def test_action_without_version_blocked(self, monkeypatch, mock_action_registry_no_version):
    """
    2.1 Action new without explicit version MUST BLOCK.
    
    ActionRegistry registers action="new_action" without action_version.
    Expected:
    - ActionResult.status == "BLOCKED"
    - reason_codes contains "ACTION_VERSION_MISSING"
    """
    monkeypatch.setattr(
        "app.agentic_pipeline.get_action_registry",
        lambda: mock_action_registry_no_version
    )
    
    result, _ = run_agentic_action(
        action="new_action",
        payload={"data": "test"},
        trace_id="trace-version-001"
    )
    
    assert result.status == "BLOCKED", f"Expected BLOCKED but got {result.status}"
    assert "ACTION_VERSION_MISSING" in result.reason_codes, \
        f"Expected ACTION_VERSION_MISSING in {result.reason_codes}"
```

### test_action_versioning_red.py — Test 2

```python
def test_action_with_invalid_version_blocked(self, monkeypatch, mock_action_registry_invalid_version):
    """
    2.2 Action new with invalid version format MUST BLOCK.
    
    action_version = "v1" (invalid, must be X.Y.Z).
    Expected:
    - BLOCKED + "ACTION_VERSION_INVALID"
    """
    monkeypatch.setattr(
        "app.agentic_pipeline.get_action_registry",
        lambda: mock_action_registry_invalid_version
    )
    
    result, _ = run_agentic_action(
        action="bad_version_action",
        payload={"data": "test"},
        trace_id="trace-version-002"
    )
    
    assert result.status == "BLOCKED"
    assert "ACTION_VERSION_INVALID" in result.reason_codes, \
        f"Expected ACTION_VERSION_INVALID in {result.reason_codes}"
```

### test_executor_versioning_red.py — Test 4

```python
def test_executor_without_version_blocked(
    self, monkeypatch, mock_action_requiring_min_version, mock_executor_no_version
):
    """
    4.1 Executor MOCK without version MUST BLOCK.
    
    Action requires min_executor_version="1.1.0".
    Executor has no version attribute.
    Expected:
    - BLOCKED + "EXECUTOR_VERSION_MISSING"
    """
    monkeypatch.setattr(
        "app.agentic_pipeline.get_action_registry",
        lambda: mock_action_requiring_min_version
    )
    monkeypatch.setattr(
        "app.agentic_pipeline.route_action",
        lambda action: "test_executor_versioning"
    )
    monkeypatch.setattr(
        "app.agentic_pipeline.get_executor",
        lambda executor_id: mock_executor_no_version
    )
    
    result, _ = run_agentic_action(
        action="version_test_action",
        payload={"data": "test"},
        trace_id="trace-execver-001"
    )
    
    assert result.status == "BLOCKED"
    assert "EXECUTOR_VERSION_MISSING" in result.reason_codes, \
        f"Expected EXECUTOR_VERSION_MISSING in {result.reason_codes}"
```

### test_executor_capabilities_red.py — Test 8

```python
def test_executor_without_capabilities_blocked(
    self, monkeypatch, mock_action_requiring_capabilities, mock_executor_no_capabilities
):
    """
    3.1 Executor declares capabilities=None/absent.
    
    Action requires ["TEXT_PROCESSING"].
    Expected:
    - BLOCKED + "EXECUTOR_CAPABILITY_MISSING"
    """
    monkeypatch.setattr(
        "app.agentic_pipeline.get_action_registry",
        lambda: mock_action_requiring_capabilities
    )
    monkeypatch.setattr(
        "app.agentic_pipeline.route_action",
        lambda action: "test_executor_captest"
    )
    monkeypatch.setattr(
        "app.agentic_pipeline.get_executor",
        lambda executor_id: mock_executor_no_capabilities
    )
    
    result, _ = run_agentic_action(
        action="capability_test_action",
        payload={"data": "test"},
        trace_id="trace-cap-001"
    )
    
    assert result.status == "BLOCKED"
    assert "EXECUTOR_CAPABILITY_MISSING" in result.reason_codes, \
        f"Expected EXECUTOR_CAPABILITY_MISSING in {result.reason_codes}"
```

---

## 3. ONDE AG-03 DEVE SER IMPLEMENTADO NO PIPELINE

### Mapa de implementação

**Arquivo principal:** `app/agentic_pipeline.py`

#### Step 3B: ACTION VERSION VALIDATION

**Localização:** `app/agentic_pipeline.py` linhas 157-190

**Código atual (PARCIALMENTE IMPLEMENTADO):**

```python
# Step 3B: Validate action_version (ALWAYS for non-legacy, never skip)
if action_meta is not None:
    action_version = action_meta.get("action_version")
    if action_version is None:
        if action not in LEGACY_ACTIONS:
            status = "BLOCKED"
            reason_codes = ["ACTION_VERSION_MISSING"]
            result = ActionResult(
                action=action,
                executor_id=executor_id,
                executor_version="unknown",
                status=status,
                reason_codes=reason_codes,
                input_digest=input_digest,
                output_digest=output_digest,
                trace_id=trace_id,
                ts_utc=datetime.now(timezone.utc),
            )
            log_action_result(result)
            return (result, None)
    elif not _is_valid_semver(action_version):
        status = "BLOCKED"
        reason_codes = ["ACTION_VERSION_INVALID"]
        result = ActionResult(
            action=action,
            executor_id=executor_id,
            executor_version="unknown",
            status=status,
            reason_codes=reason_codes,
            input_digest=input_digest,
            output_digest=output_digest,
            trace_id=trace_id,
            ts_utc=datetime.now(timezone.utc),
        )
        log_action_result(result)
        return (result, None)
```

**Status:** ✅ IMPLEMENTADO (Step 3B completo)

**Verificação:**
- `_is_valid_semver()` existe (linhas 46-48)
- SEMVER_PATTERN regex existe (linha 38)
- Validação de None: SIM
- Validação de formato: SIM
- Bypass por LEGACY_ACTIONS: SIM (linha 176)

---

#### Step 4A: EXECUTOR VERSION COMPATIBILITY

**Localização:** `app/agentic_pipeline.py` linhas 242-301

**Código atual (IMPLEMENTADO):**

```python
# Step 4A: Validate executor version (AG-03)
# Only check min_executor_version for non-legacy actions
if action_meta and action not in LEGACY_ACTIONS:
    min_executor_version = action_meta.get("min_executor_version")
    if min_executor_version is not None:
        if executor_version is None:
            status = "BLOCKED"
            reason_codes = ["EXECUTOR_VERSION_MISSING"]
            result = ActionResult(
                action=action,
                executor_id=executor_id,
                executor_version="unknown",
                status=status,
                reason_codes=reason_codes,
                input_digest=input_digest,
                output_digest=output_digest,
                trace_id=trace_id,
                ts_utc=datetime.now(timezone.utc),
            )
            log_action_result(result)
            return (result, None)
        else:
            # Use semver comparison instead of string comparison
            try:
                if _compare_semver(executor_version, min_executor_version) < 0:
                    status = "BLOCKED"
                    reason_codes = ["EXECUTOR_VERSION_INCOMPATIBLE"]
                    result = ActionResult(
                        action=action,
                        executor_id=executor_id,
                        executor_version=executor_version,
                        status=status,
                        reason_codes=reason_codes,
                        input_digest=input_digest,
                        output_digest=output_digest,
                        trace_id=trace_id,
                        ts_utc=datetime.now(timezone.utc),
                    )
                    log_action_result(result)
                    return (result, None)
            except ValueError:
                # If version comparison fails, treat as incompatible
                status = "BLOCKED"
                reason_codes = ["EXECUTOR_VERSION_INCOMPATIBLE"]
                result = ActionResult(
                    action=action,
                    executor_id=executor_id,
                    executor_version=executor_version,
                    status=status,
                    reason_codes=reason_codes,
                    input_digest=input_digest,
                    output_digest=output_digest,
                    trace_id=trace_id,
                    ts_utc=datetime.now(timezone.utc),
                )
                log_action_result(result)
                return (result, None)
```

**Status:** ✅ IMPLEMENTADO (Step 4A completo)

**Verificação:**
- `_compare_semver()` existe (linhas 49-61)
- Usa `packaging.version.Version` (linha 20): SIM
- Validação de None: SIM (linha 250)
- Validação de compatibilidade: SIM (linha 261, _compare_semver < 0)
- Fallback ValueError: SIM (linhas 264-280)
- Bypass por LEGACY_ACTIONS: SIM (linha 245)

---

#### Step 4B: EXECUTOR CAPABILITIES VALIDATION

**Localização:** `app/agentic_pipeline.py` linhas 303-365

**Código atual (IMPLEMENTADO):**

```python
# Step 4B: Validate executor capabilities (AG-03)
# Check that executor has all required_capabilities
if action_meta and action not in LEGACY_ACTIONS:
    required_capabilities = action_meta.get("required_capabilities", [])
    if required_capabilities:
        # Get capabilities attribute
        executor_capabilities = getattr(executor, "capabilities", None)
        
        # If executor has no capabilities attribute at all -> MISSING
        # Check for None or non-list types (e.g. MagicMock)
        if executor_capabilities is None or not isinstance(executor_capabilities, (list, tuple, set)):
            status = "BLOCKED"
            reason_codes = ["EXECUTOR_CAPABILITY_MISSING"]
            result = ActionResult(
                action=action,
                executor_id=executor_id,
                executor_version=executor_version or "unknown",
                status=status,
                reason_codes=reason_codes,
                input_digest=input_digest,
                output_digest=output_digest,
                trace_id=trace_id,
                ts_utc=datetime.now(timezone.utc),
            )
            log_action_result(result)
            return (result, None)
        
        # If executor has capabilities but insufficient -> MISMATCH
        normalized_executor_caps = _normalize_capabilities(executor_capabilities)
        normalized_required_caps = _normalize_capabilities(required_capabilities)

        missing_capabilities = set(normalized_required_caps) - set(normalized_executor_caps)
        if missing_capabilities:
            status = "BLOCKED"
            reason_codes = ["EXECUTOR_CAPABILITY_MISMATCH"]
            result = ActionResult(
                action=action,
                executor_id=executor_id,
                executor_version=executor_version or "unknown",
                status=status,
                reason_codes=reason_codes,
                input_digest=input_digest,
                output_digest=output_digest,
                trace_id=trace_id,
                ts_utc=datetime.now(timezone.utc),
            )
            log_action_result(result)
            return (result, None)
```

**Status:** ✅ IMPLEMENTADO (Step 4B completo)

**Verificação:**
- `_normalize_capabilities()` existe (linhas 41-44)
- Normalização: uppercase, deduplicate, sort: SIM (linha 42-43)
- Validação de None: SIM (linha 315)
- Validação de tipo (not list/tuple/set): SIM (linha 315)
- Set difference (required - executor): SIM (linha 334)
- Bypass por LEGACY_ACTIONS: SIM (linha 307)

---

## 4. STATUS DA IMPLEMENTAÇÃO AG-03

**Conclusão surpreendente:** AG-03 **JÁ ESTÁ IMPLEMENTADO** nos passos 3B, 4A, 4B.

Porém, os RED tests falham porque:

1. **LEGACY_ACTIONS bypass está ativo** — action="process" pula TODAS as validações
2. **Testes esperam comportamento, código está pronto** — validações existem, mas não são testadas para ações fora de LEGACY_ACTIONS

---

## 5. CONTRATOS E CAMPOS (PYDANTIC / DATACLASSES)

### ActionRequest

**Arquivo:** `app/action_contracts.py` linhas 21-45

```python
class ActionRequest(BaseModel):
    """Immutable request to execute an action through the governed pipeline.

    - action: canonical action identifier (must exist in ACTION_REGISTRY)
    - payload: JSON-like dict (validated before execution)
    - trace_id: propagated from gate DecisionRecord for correlation
    - ts_utc: timezone-aware UTC timestamp when request was created
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    payload: dict[str, Any]
    trace_id: str
    ts_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("ts_utc")
    @classmethod
    def validate_ts_utc_is_utc_aware(cls, v: datetime) -> datetime:
        """Validate ts_utc is timezone-aware and in UTC."""
        if v.tzinfo is None:
            raise ValueError("ts_utc must be timezone-aware (UTC)")
        if v.tzinfo != timezone.utc:
            raise ValueError("ts_utc must be in UTC timezone")
        return v
```

**Campos relevantes para AG-03:**
- `action: str` — Usado para checar LEGACY_ACTIONS
- Não contém action_version (fica em ActionMeta)

---

### ActionResult

**Arquivo:** `app/action_contracts.py` linhas 48-100

```python
class ActionResult(BaseModel):
    """Immutable proof object of an execution outcome.

    This is the ONLY artifact returned by the execution pipeline.
    Raw outputs are NEVER included.

    - action: canonical action identifier
    - executor_id: which executor handled the request
    - executor_version: immutable version of executor code
    - status: SUCCESS, FAILED, BLOCKED, or PENDING (pre-audit only)
    - reason_codes: MUST be non-empty if status != SUCCESS
    - input_digest: SHA256 of canonical input (never raw payload)
    - output_digest: SHA256 of canonical output (or None if not serializable)
    - trace_id: links to DecisionRecord for full audit trail
    - ts_utc: timezone-aware UTC timestamp when execution completed
    """

    model_config = ConfigDict(extra="forbid")

    action: str
    executor_id: str
    executor_version: str
    status: Literal["SUCCESS", "FAILED", "BLOCKED", "PENDING"]
    reason_codes: list[str]
    input_digest: str
    output_digest: str | None
    trace_id: str
    ts_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("reason_codes")
    @classmethod
    def validate_reason_codes_non_empty_if_not_success(cls, v: list[str], info) -> list[str]:
        """Ensure reason_codes is non-empty when status is not SUCCESS or PENDING."""
        status = info.data.get("status")
        if status and status not in ("SUCCESS", "PENDING") and not v:
            raise ValueError("reason_codes must be non-empty when status is not SUCCESS or PENDING")
        return v
```

**Campos AG-03-relevantes:**
- `executor_version: str` — Lido do executor no Step 4
- `reason_codes: list[str]` — Contém AG-03 reason_codes (ACTION_VERSION_MISSING, EXECUTOR_VERSION_INCOMPATIBLE, EXECUTOR_CAPABILITY_MISMATCH)
- `status: Literal["SUCCESS", "FAILED", "BLOCKED", "PENDING"]` — BLOCKED para validações AG-03

---

### ActionMeta

**Arquivo:** `app/action_registry.py` linhas 14-62

```python
class ActionMeta(BaseModel):
    """Metadata for a single action in the registry.
    
    Fields:
    - description: human-readable action description
    - executor: executor identifier
    - version: deprecated, use action_version
    - action_version: semantic version (optional, e.g., "1.0.0")
    - required_capabilities: list of required executor capabilities (ordered, normalized)
    - min_executor_version: minimum executor version required (optional)
    """
    
    model_config = ConfigDict(extra="allow")
    
    description: str
    executor: str
    version: Optional[str] = None  # Legacy field
    action_version: Optional[str] = None
    required_capabilities: List[str] = []
    min_executor_version: Optional[str] = None
    
    @field_validator("action_version")
    @classmethod
    def validate_action_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate action_version follows semver format if provided."""
        if v is not None and not SEMVER_REGEX.match(v):
            raise ValueError(f"action_version must follow semver (X.Y.Z), got: {v}")
        return v
    
    @field_validator("required_capabilities")
    @classmethod
    def normalize_capabilities(cls, v: List[str]) -> List[str]:
        """Normalize and sort capabilities for determinism."""
        if not v:
            return []
        # Strip whitespace, uppercase, deduplicate, and sort
        normalized = sorted(set(cap.strip().upper() for cap in v if cap.strip()))
        return normalized
    
    @field_validator("min_executor_version")
    @classmethod
    def validate_min_executor_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate min_executor_version follows semver format if provided."""
        if v is not None and not SEMVER_REGEX.match(v):
            raise ValueError(f"min_executor_version must follow semver (X.Y.Z), got: {v}")
        return v
```

**Campos AG-03:**
- `action_version: Optional[str]` — Validado com SEMVER_REGEX em Step 3B
- `min_executor_version: Optional[str]` — Comparado no Step 4A
- `required_capabilities: List[str]` — Validado no Step 4B
- Normalização: uppercase, deduplicate, sort (linha 50-52)

---

### ActionRegistry

**Arquivo:** `app/action_registry.py` linhas 65-87

```python
class ActionRegistry(BaseModel):
    """Immutable registry of all governable actions.

    Fields:
    - actions: dict mapping action_id to ActionMeta (or dict for backward compat)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    actions: Dict[str, Any]
```

**Dados reais:**

```python
def get_action_registry() -> ActionRegistry:
    """Return the canonical action registry."""
    return ActionRegistry(
        actions={
            "process": {
                "description": "Process text input",
                "executor": "text_process_v1",
                "version": "1.0",  # Legacy field
                "action_version": "1.0.0",  # AG-03: explicit semver
                "required_capabilities": [],  # No specific capabilities required for now
                "min_executor_version": None,  # No minimum version enforced yet
            },
        }
    )
```

---

### Executor Info

**Arquivo:** `app/executors/registry.py` linhas 13-41

```python
class TextProcessExecutorV1:
    """Simple text processing executor (deterministic, side-effect free).

    Uppercases text field from payload. Used for testing and demonstration.
    """

    def __init__(self):
        self.executor_id = "text_process_v1"
        self.version = "1.0.0"
        self.capabilities = ["TEXT_PROCESSING"]  # AG-03: declare capabilities
        self.limits = ExecutorLimits(
            timeout_ms=1000,
            max_payload_bytes=10_000,
            max_depth=10,
            max_list_items=100,
        )
```

**Campos AG-03:**
- `executor_id: str` — "text_process_v1"
- `version: str` — "1.0.0" (comparado no Step 4A)
- `capabilities: list[str]` — ["TEXT_PROCESSING"] (validado no Step 4B)

---

## 6. AS 3 REGISTRIES E DIVERGÊNCIA

### Registry 1: action_router.ACTION_REGISTRY

**Arquivo:** `app/action_router.py` linhas 7-10

```python
ACTION_REGISTRY: dict[str, str] = {
    "process": "text_process_v1",
}
```

**Tipo:** Dict[action_name → executor_id]
**Uso:** Routing determinístico no Step 1
**Exemplo:** "process" → "text_process_v1"
**Imutabilidade:** Sim (hardcoded)
**Versão:** Nenhuma (apenas string mapping)

---

### Registry 2: action_registry.get_action_registry()

**Arquivo:** `app/action_registry.py` linhas 90-107

```python
def get_action_registry() -> ActionRegistry:
    """Return the canonical action registry."""
    return ActionRegistry(
        actions={
            "process": {
                "description": "Process text input",
                "executor": "text_process_v1",
                "version": "1.0",
                "action_version": "1.0.0",
                "required_capabilities": [],
                "min_executor_version": None,
            },
        }
    )
```

**Tipo:** Dict[action_name → ActionMeta (dict)]
**Uso:** Metadados e validação AG-03 nos Steps 3B, 4A, 4B
**Exemplo:** "process" → {description, executor, action_version, min_executor_version, required_capabilities}
**Imutabilidade:** Sim (ActionRegistry frozen=True)
**Versão:** Contém action_version por action

---

### Registry 3: executors.registry._EXECUTORS

**Arquivo:** `app/executors/registry.py` linhas 44-47

```python
_EXECUTORS: dict[str, Executor] = {
    "text_process_v1": TextProcessExecutorV1(),
}
```

**Tipo:** Dict[executor_id → Executor instance]
**Uso:** Lookup de executor no Step 4
**Exemplo:** "text_process_v1" → TextProcessExecutorV1() com version="1.0.0", capabilities=["TEXT_PROCESSING"]
**Imutabilidade:** Não (dict é editável, mas entries são singletons)
**Thread-safety:** Sim (protegido por _EXECUTORS_LOCK RLock)

---

### DIVERGÊNCIA: Mapeamento executor

**Fluxo de routing:**

```
action="process"
    ↓
Step 1: action_router.route_action("process")
    → ACTION_REGISTRY["process"] = "text_process_v1"
    ↓
Step 4: get_executor("text_process_v1")
    → _EXECUTORS["text_process_v1"] = TextProcessExecutorV1()
```

**Pontos de divergência possível:**

1. **action_router vs action_registry.executor campo:**
   - action_router: "process" → "text_process_v1" (Step 1)
   - action_registry: {"executor": "text_process_v1"} (Step 3)
   - Se divergem: Step 1 usa router, Step 3 usa registry → possível versão incorreta usada

2. **action_registry.executor vs _EXECUTORS key:**
   - action_registry: {"executor": "text_process_v1"}
   - _EXECUTORS: key "text_process_v1"
   - Se divergem: Step 4 get_executor("text_process_v1") falha (EXECUTOR_NOT_FOUND)

**Estado atual:** Nenhuma divergência (ambos dizem "text_process_v1")

---

## 7. LEGACY_ACTIONS BYPASS — LOCALIZAÇÃO E REMOÇÃO

### Localização do LEGACY_ACTIONS

**Arquivo:** `app/agentic_pipeline.py` linha 36

```python
# Legacy actions exempt from strict AG-03 version/capability checks
LEGACY_ACTIONS = {"process"}
```

---

### Usos do bypass

#### Uso 1: Step 3B (Action Version)

**Localização:** `app/agentic_pipeline.py` linha 176

```python
if action_version is None:
    if action not in LEGACY_ACTIONS:  # BYPASS HERE
        status = "BLOCKED"
        reason_codes = ["ACTION_VERSION_MISSING"]
        ...
```

**Efeito:** Se action="process", pula validação de action_version mesmo que None

#### Uso 2: Step 4A (Executor Version)

**Localização:** `app/agentic_pipeline.py` linha 245

```python
if action_meta and action not in LEGACY_ACTIONS:  # BYPASS HERE
    min_executor_version = action_meta.get("min_executor_version")
    if min_executor_version is not None:
        ...
```

**Efeito:** Se action="process", pula validação de executor.version mesmo que None

#### Uso 3: Step 4B (Capabilities)

**Localização:** `app/agentic_pipeline.py` linha 307

```python
if action_meta and action not in LEGACY_ACTIONS:  # BYPASS HERE
    required_capabilities = action_meta.get("required_capabilities", [])
    ...
```

**Efeito:** Se action="process", pula validação de executor.capabilities mesmo que missing

---

### REMOÇÃO DO LEGACY_ACTIONS BYPASS

**Tarefa:** Remover `if action not in LEGACY_ACTIONS:` de 3 locais

**Implicação:**
- action="process" agora requerirá action_version="1.0.0" (já existe)
- action="process" agora requerirá min_executor_version (need to set)
- action="process" agora requerirá required_capabilities (need to set)

**Ação necessária:**
1. Atualizar action_registry.py "process" entry com min_executor_version e required_capabilities
2. Remover 3 `if action not in LEGACY_ACTIONS:` checks
3. Converter test_ag03_retrocompat_red.py tests de RED→GREEN (comportamento esperado muda)

---

## 8. SEMVER E CAPABILITIES (IMPLEMENTAÇÕES EXISTENTES)

### B1-FIX: Semver Comparison

**Localização:** `app/agentic_pipeline.py` linhas 49-61

```python
def _compare_semver(version_a: str, version_b: str) -> int:
    """Compare two semantic versions using packaging.version.
    
    Args:
        version_a: version string (e.g., "1.0.0")
        version_b: version string to compare against (e.g., "1.1.0")
    
    Returns:
        -1 if version_a < version_b
         0 if version_a == version_b
         1 if version_a > version_b
    
    Raises:
        ValueError if either version is invalid
    """
    try:
        va = pkg_version.Version(version_a)
        vb = pkg_version.Version(version_b)
    except pkg_version.InvalidVersion as exc:
        raise ValueError(f"Invalid semantic version: {exc}")
    
    if va < vb:
        return -1
    elif va > vb:
        return 1
    else:
        return 0
```

**Verificação:** Usa `packaging.version.Version` (import linha 20) ✅

**Teste:** `tests/test_semver_ordering_b1.py` — verifica 1.10.0 > 1.9.0 (correto, não lexicográfico)

---

### Capabilities Normalization

**Localização:** `app/agentic_pipeline.py` linhas 41-44

```python
def _normalize_capabilities(caps):
    """Normalize capability list (uppercase, deduplicate, sort)."""
    if not caps:
        return []
    return sorted(set(c.strip().upper() for c in caps if c.strip()))
```

**Normalização:**
1. Strip whitespace
2. Uppercase
3. Deduplicate (set)
4. Sort (determinístico)

**Exemplo:**
```python
Input:  ["text_processing", "LOGGING", "text_processing"]
Output: ["LOGGING", "TEXT_PROCESSING"]
```

**Verificação:** ActionMeta também normaliza (linhas 50-52 em action_registry.py)

---

### Case-Sensitivity

**Comportamento:** Case-INSENSITIVE (ambos são uppercase antes da comparação)

**Validação:** Não há erro se action="process" define required_capabilities=["text_processing"] (será uppercase→"TEXT_PROCESSING")

---

## 9. ESTADO ATUAL DO TEST SUITE

### Contagem de testes

```
pytest -q 2>&1 | grep -E "passed|failed|error"
```

**Total:** ~95 tests across 29 files

**Breakdown:**
- 48 unit tests (passing)
- 5 pipeline tests (passing)
- 12 RED tests (RED — to be converted to GREEN)
- 26 integration tests (passing)
- 4 E2E tests (passing)

---

### Rodar somente RED tests (AG-03)

**Arquivo de workflow:** `.github/workflows/ag03-governance.yml`

```bash
python -m pytest tests/test_action_versioning_red.py \
                 tests/test_executor_versioning_red.py \
                 tests/test_executor_capabilities_red.py \
                 tests/test_ag03_retrocompat_red.py \
                 -v --tb=short
```

**Status esperado:** 12 FAILED (todos os RED tests falham porque o bypass está ativo)

---

### RED Tests vs Current Code

**Explicação da falha:**

- Tests 1-10 (Tests 1-10): Esperam validação, mas action="process" ∈ LEGACY_ACTIONS → bypass
- Tests 11-12: Esperam que legacy continue funcionando (sem validação)

**Ação necessária:** Remover bypass → Tests 1-10 passam, Tests 11-12 precisam ser reescritos

---

## 10. READY TO IMPLEMENT AG-03 — LISTA FINAL

### Arquivos a editar

#### 10.1 Edição Mínima (sem remoção de bypass ainda)

**Nenhuma.** AG-03 está IMPLEMENTADO. Apenas os RED tests falham porque LEGACY_ACTIONS bypass está ativo.

#### 10.2 Remoção do Legacy Bypass (obrigatório para AG-03)

**Arquivo 1:** `app/agentic_pipeline.py`

**Edição 1.1:** Remover bypass em Step 3B (linha ~176)

Antes:
```python
if action_version is None:
    if action not in LEGACY_ACTIONS:
        status = "BLOCKED"
        ...
```

Depois:
```python
if action_version is None:
    status = "BLOCKED"
    ...
```

**Edição 1.2:** Remover bypass em Step 4A (linha ~245)

Antes:
```python
if action_meta and action not in LEGACY_ACTIONS:
    min_executor_version = action_meta.get("min_executor_version")
```

Depois:
```python
if action_meta:
    min_executor_version = action_meta.get("min_executor_version")
```

**Edição 1.3:** Remover bypass em Step 4B (linha ~307)

Antes:
```python
if action_meta and action not in LEGACY_ACTIONS:
    required_capabilities = action_meta.get("required_capabilities", [])
```

Depois:
```python
if action_meta:
    required_capabilities = action_meta.get("required_capabilities", [])
```

**Edição 1.4:** Remover LEGACY_ACTIONS constant (linha 36)

Antes:
```python
LEGACY_ACTIONS = {"process"}
```

Depois:
```python
# LEGACY_ACTIONS removed — all actions now require AG-03 validation
```

---

**Arquivo 2:** `app/action_registry.py`

**Edição 2.1:** Adicionar min_executor_version para "process"

Antes:
```python
"process": {
    "description": "Process text input",
    "executor": "text_process_v1",
    "version": "1.0",
    "action_version": "1.0.0",
    "required_capabilities": [],
    "min_executor_version": None,
},
```

Depois:
```python
"process": {
    "description": "Process text input",
    "executor": "text_process_v1",
    "version": "1.0",
    "action_version": "1.0.0",
    "required_capabilities": ["TEXT_PROCESSING"],  # Updated
    "min_executor_version": "1.0.0",  # Updated
},
```

---

**Arquivo 3:** `tests/test_ag03_retrocompat_red.py` (convert RED→GREEN)

**Edição 3.1:** Rename tests e atualizar expectativas

Antes:
```python
def test_action_process_without_version_continues(self, client, caplog):
    """Legacy action should continue to work..."""
    # Expect: NOT BLOCKED
```

Depois:
```python
def test_action_process_with_explicit_version_required(self, client, caplog):
    """Process action now requires explicit version..."""
    # Expect: BLOCKED (if action_version missing)
```

---

### Testes a converter RED → GREEN

1. **test_action_versioning_red.py**
   - test_action_without_version_blocked → GREEN (action="new_action" without version blocks)
   - test_action_with_invalid_version_blocked → GREEN
   - test_action_with_valid_version_not_blocked_by_version → GREEN

2. **test_executor_versioning_red.py**
   - test_executor_without_version_blocked → GREEN
   - test_executor_with_incompatible_version_blocked → GREEN
   - test_executor_with_compatible_version_not_blocked → GREEN
   - test_executor_with_newer_version_not_blocked → GREEN

3. **test_executor_capabilities_red.py**
   - test_executor_without_capabilities_blocked → GREEN
   - test_executor_with_insufficient_capabilities_blocked → GREEN
   - test_executor_compatible_not_blocked_by_capabilities → GREEN

4. **test_ag03_retrocompat_red.py** (REWRITE, not just GREEN)
   - test_action_process_without_version_continues → DELETE or REWRITE
   - test_executor_without_capabilities_legacy_mode → DELETE or REWRITE

---

### Reason codes que devem existir

**Já existem em ActionResult validação:**

- `ACTION_VERSION_MISSING` ✅
- `ACTION_VERSION_INVALID` ✅
- `EXECUTOR_VERSION_MISSING` ✅
- `EXECUTOR_VERSION_INCOMPATIBLE` ✅
- `EXECUTOR_CAPABILITY_MISSING` ✅
- `EXECUTOR_CAPABILITY_MISMATCH` ✅
- `EXECUTION_ATTEMPT` (pre-audit) ✅
- `BLOCKED` (not a reason_code, status value) ✅

**Nenhum reason_code novo necessário.**

---

### Ordem exata de implementação (para minimizar diffs)

1. **Step 1:** Editar `app/action_registry.py` — adicionar min_executor_version="1.0.0" e required_capabilities=["TEXT_PROCESSING"] ao "process" action
   - **Why:** Prepara dados antes de remover bypass
   - **Commit:** "AG-03: Update process action metadata with version and capabilities"

2. **Step 2:** Editar `app/agentic_pipeline.py` — remover 3 `if action not in LEGACY_ACTIONS:` checks
   - **Why:** Ativa validação AG-03 para todas as ações
   - **Commit:** "AG-03: Remove LEGACY_ACTIONS bypass, enforce validation for all actions"

3. **Step 3:** Editar `app/agentic_pipeline.py` — remover `LEGACY_ACTIONS = {"process"}` constant
   - **Why:** Limpeza de código morto
   - **Commit:** "AG-03: Remove LEGACY_ACTIONS constant"

4. **Step 4:** Editar `tests/test_ag03_retrocompat_red.py` — reescrever testes ou deletar
   - **Why:** Testes de legacy behavior não mais relevantes
   - **Commit:** "AG-03: Convert retrocompat tests (legacy action behavior changes)"

5. **Step 5:** Rodar `pytest tests/test_*red.py -v`
   - **Expected:** 12 PASSED (all RED tests now GREEN)
   - **Commit:** "AG-03: All RED tests converted to GREEN"

---

### Checklist de validação pós-implementação

- [ ] test_action_versioning_red.py — 3 tests PASSED
- [ ] test_executor_versioning_red.py — 4 tests PASSED
- [ ] test_executor_capabilities_red.py — 3 tests PASSED
- [ ] test_ag03_retrocompat_red.py — 2 tests updated or deleted
- [ ] Full suite `pytest` — all tests PASSED
- [ ] Code review — 2 reviewers
- [ ] Documentation updated (ENDPOINTS.md, README.md)

---

## 11. RESUMO EXECUTIVO

**Estado Atual:**
- AG-03 está **90% implementado** (Steps 3B, 4A, 4B existem no código)
- LEGACY_ACTIONS bypass **ativa-se automaticamente** para action="process"
- RED tests **documentam comportamento esperado** (depois de remover bypass)

**Trabalho Necessário:**
1. Actualizar action_registry.py (dados: min_executor_version + required_capabilities)
2. Remover 3 `if action not in LEGACY_ACTIONS:` checks (code)
3. Remover LEGACY_ACTIONS constant (cleanup)
4. Reescrever test_ag03_retrocompat_red.py (tests)

**Tamanho do diff estimado:** ~50 linhas (muito pequeno)

**Timeline:** 1-2 dias de trabalho (desenvolvimento + testes)

---

END OF EXTRACTION

