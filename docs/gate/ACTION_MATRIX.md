# Action Matrix — Mapeamento completo

## Visão geral
Mapeamento canônico entre rotas HTTP e actions executáveis.

**Fonte de verdade:** `app/gate_canonical/action_detector.py` (`ACTION_MAP`)

---

## Tabela de mapeamento

| Path (normalizado)       | Método HTTP | Action              | Profile requerido         | Notas                          |
|--------------------------|-------------|---------------------|---------------------------|--------------------------------|
| `/process`               | POST        | `process`           | `process`                 | LLM pipeline principal         |
| `/preferences/{user_id}` | GET         | `preferences.get`   | `preferences.get`         | Recuperar preferências         |
| `/preferences/{user_id}` | PUT         | `preferences.put`   | `preferences.put`         | Atualizar preferências         |
| `/preferences/{user_id}` | DELETE      | `preferences.delete`| `preferences.delete`      | Deletar preferências           |

---

## Detalhamento por action

### 1. `process`
**Rota:** `POST /process`  
**Propósito:** Executar LLM pipeline (V-COF governance + OpenAI).

**Body schema (Pydantic):**
```python
class ProcessRequest(BaseModel):
    text: str  # Texto de entrada para LLM
    user_id: Optional[str] = None  # Opcional, para audit
```

**Profile allowlist:**
- `text` (obrigatório)
- `user_id` (opcional)

**Resposta:**
```json
{
  "output": "Resposta da LLM",
  "trace_id": "uuid",
  "audit_id": "uuid"
}
```

**Erros comuns:**
- G10 (422): Body JSON inválido
- G11 (422): Campo `text` ausente ou tipo incorreto
- 403: Policy violation (allow_external=False + external URL detectado)

---

### 2. `preferences.get`
**Rota:** `GET /preferences/{user_id}`  
**Propósito:** Recuperar preferências de tom/formato do usuário.

**Path parameters:**
- `user_id`: string (alfabético + underscore, max 50 chars)

**Body:** Vazio (GET não exige body).

**Profile allowlist:**
- `user_id` (obrigatório, path param)

**Resposta:**
```json
{
  "user_id": "abc123",
  "tone_preference": "institucional",
  "output_format": "texto",
  "language": "pt-BR",
  "trace_id": "uuid"
}
```

**Erros comuns:**
- G8 (500): `user_id` não alfanumérico (não match template)
- 404: Preferências não encontradas no DB

---

### 3. `preferences.put`
**Rota:** `PUT /preferences/{user_id}`  
**Propósito:** Atualizar preferências do usuário.

**Path parameters:**
- `user_id`: string (alfabético + underscore, max 50 chars)

**Body schema (Pydantic):**
```python
class PreferencesUpdate(BaseModel):
    tone_preference: Optional[str] = None  # "institucional" | "informal" | "neutro"
    output_format: Optional[str] = None    # "texto" | "topicos" | "checklist"
    language: Optional[str] = None         # "pt-BR" | "en-US"
```

**Profile allowlist:**
- `user_id` (path param)
- `tone_preference` (opcional)
- `output_format` (opcional)
- `language` (opcional)

**Resposta:**
```json
{
  "user_id": "abc123",
  "updated_fields": ["tone_preference"],
  "trace_id": "uuid"
}
```

**Erros comuns:**
- G10 (422): Body JSON inválido
- G11 (422): Campo não permitido enviado (ex: `extra_field`)
- 403: `deny_unknown_fields=True` + campo desconhecido

---

### 4. `preferences.delete`
**Rota:** `DELETE /preferences/{user_id}`  
**Propósito:** Deletar todas as preferências do usuário.

**Path parameters:**
- `user_id`: string (alfabético + underscore, max 50 chars)

**Body:** Vazio (DELETE não exige body).

**Profile allowlist:**
- `user_id` (obrigatório, path param)

**Resposta:**
```json
{
  "user_id": "abc123",
  "deleted": true,
  "trace_id": "uuid"
}
```

**Erros comuns:**
- G8 (500): `user_id` não alfanumérico
- 404: Preferências não encontradas (idempotente, pode retornar 200)

---

## Normalização de paths

**Função:** `normalize_path(raw_path: str) -> str`

### Regras:
1. **Remove prefixo `/api/v1`:**
   - `/api/v1/process` → `/process`
   - `/api/v1/preferences/abc123` → `/preferences/{user_id}`

2. **Colapsa path params dinâmicos:**
   - `/preferences/abc123` → `/preferences/{user_id}`
   - `/preferences/xyz789` → `/preferences/{user_id}`
   - Regex: `/preferences/[a-zA-Z0-9_]+` → `/preferences/{user_id}`

### Exemplos:
| Input                              | Output                     |
|------------------------------------|----------------------------|
| `/process`                         | `/process`                 |
| `/api/v1/process`                  | `/process`                 |
| `/preferences/user_123`            | `/preferences/{user_id}`   |
| `/api/v1/preferences/user_abc`     | `/preferences/{user_id}`   |
| `/unknown/route`                   | `/unknown/route` (no match) |

---

## Adicionar nova action (processo)

### Passo 1: Definir rota
Criar endpoint em `app/action_router.py`:
```python
@action_router.post("/my-new-action")
async def my_new_action_handler(payload: MyNewActionRequest):
    # Implementação
    pass
```

### Passo 2: Adicionar ao ACTION_MAP
Em `app/gate_canonical/action_detector.py`:
```python
ACTION_MAP = {
    ("/process", "POST"): "process",
    ("/my-new-action", "POST"): "my_new_action",  # NOVO
    ...
}
```

### Passo 3: Atualizar action_matrix
Em `app/action_matrix.py`:
```python
allowed_actions = [
    "process",
    "preferences.delete",
    "preferences.get",
    "preferences.put",
    "my_new_action",  # NOVO (manter ordem alfabética)
]
```

### Passo 4: Criar PolicyProfile
Em `app/gate_profiles.py`:
```python
ACTION_MY_NEW_ACTION = "my_new_action"
DEFAULT_PROFILES[ACTION_MY_NEW_ACTION] = PolicyProfile(
    id="my_new_action",
    allowlist={"field1", "field2"},
    allow_external=False,
    deny_unknown_fields=True
)
```

### Passo 5: Validar
```bash
pytest tests/test_gate_integrity.py  # 1:1 mapping
pytest tests/test_action_matrix.py   # Matrix integrity
```

### Passo 6: Atualizar lock files
```bash
# Atualizar profiles_fingerprint.lock
python -c "from app.gate_artifacts import profiles_fingerprint_sha256; print(profiles_fingerprint_sha256())" > app/profiles_fingerprint.lock

# Documentar mudança em GOVERNANCE_PROFILES.md
```

---

## Validação de integridade

**Test:** `tests/test_gate_integrity.py`

Valida que:
- Toda action em `action_matrix.allowed_actions` tem um `PolicyProfile`
- `get_profile(action) is not None` para todas as actions

**Se falhar:** drift de governança detectado.

**Correção:** Adicionar PolicyProfile faltante em `gate_profiles.py`.

---

## Referências
- [GATE_ENGINE_SPEC.md](./GATE_ENGINE_SPEC.md)
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- [F11-GATE-CONSOLIDATION-PLAN.md](../implementation/F11-GATE-CONSOLIDATION-PLAN.md)

