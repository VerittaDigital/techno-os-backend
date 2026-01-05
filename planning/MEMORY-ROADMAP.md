# ROADMAP — Memória Dignificada (Post-F9.9-A)

**Documento:** Intenção Estratégica V-COF  
**Fase Atual:** F9.9-A (Preferências 1:1 user)  
**Data:** 2026-01-04  

---

## 📊 ESTADO ATUAL (F9.9-A)

### Capacidades Implementadas
- ✅ Preferências persistentes por usuário (1:1)
- ✅ Modelo wide-column (3 campos fixos)
- ✅ Allowlist fechada: tone, output_format, language
- ✅ Enums fail-closed (Pydantic validation)
- ✅ Auth via F2.3 (Bearer + X-VERITTA-USER-ID)
- ✅ No-log policy (privacy-by-design)

### Garantias Técnicas
O que "contexto permanente" significa hoje:
- Preferências persistem entre chamadas HTTP
- Associadas a user_id estável (formato `u_[a-z0-9]{8}`)
- Governadas por validação explícita
- Sem inferência automática

### Limitações Conhecidas
O que NÃO está disponível (por design):
- ❌ Histórico de conversas
- ❌ Memória semântica
- ❌ Contexto organizacional (multi-tenant)
- ❌ Perfis por agente persistentes
- ❌ Identidade visual complexa
- ❌ Escopos session/org/agent

---

## 🎯 EVOLUÇÃO PLANEJADA (F10+)

### Fase 1 — Migração Key-Value (F10.1)
**Objetivo:** Tornar preferências extensíveis sem explosão de colunas.

**Schema proposto:**
```sql
user_preferences_v2 (
  id              UUID           PRIMARY KEY,
  user_id         VARCHAR(255)   NOT NULL,
  scope           VARCHAR(16)    NOT NULL CHECK IN ('global','session'),
  key             VARCHAR(64)    NOT NULL,
  value           JSONB          NOT NULL,
  created_at      TIMESTAMPTZ    NOT NULL,
  updated_at      TIMESTAMPTZ    NOT NULL,
  UNIQUE (user_id, scope, key)
)
```

**Migração de dados:**
- Preservar dados de `user_preferences` (wide-column)
- Mapear colunas fixas → key-value:
  - `tone_preference` → `{scope: "global", key: "tone", value: "institucional"}`
  - `output_format` → `{scope: "global", key: "output_format", value: "markdown"}`
  - `language` → `{scope: "global", key: "language", value: "pt-BR"}`
- Validar integridade pós-migração
- Deprecar tabela antiga após 1 sprint de estabilidade

**Riscos:**
- Breaking change para API (compatibilidade via adapter)
- Downtime necessário? (avaliar blue-green deployment)

---

### Fase 2 — Escopos Multi-Nível (F10.2)
**Objetivo:** Suportar preferências por contexto.

**Escopos planejados:**
- `global`: Preferências do usuário (já existente)
- `session`: Preferências da sessão/chat atual (efêmera ou persistente)
- `org`: Preferências da organização (multi-tenant)
- `agent`: Preferências por agente/bot (ex: "samurai_strict_mode")

**Hierarquia de overrides:**
```
agent > session > org > global > default
```

**API proposta:**
```http
GET /api/v1/preferences?scope=session
PUT /api/v1/preferences?scope=session
```

**Governança:**
- Apenas scopes na allowlist são aceitos
- user_id obrigatório para todos os scopes
- org_id obrigatório para scope=org (multi-tenant)

---

### Fase 3 — Perfis por Agente (F10.3)
**Objetivo:** Permitir configuração persistente por agente.

**Exemplo:**
```json
{
  "scope": "agent",
  "agent_id": "samurai_code_reviewer",
  "preferences": {
    "strictness": "maximum",
    "audit_mode": "verbose",
    "language": "pt-BR"
  }
}
```

**Tabela adicional:**
```sql
agent_profiles (
  id              UUID           PRIMARY KEY,
  user_id         VARCHAR(255)   NOT NULL,
  agent_id        VARCHAR(64)    NOT NULL,
  config          JSONB          NOT NULL,
  created_at      TIMESTAMPTZ    NOT NULL,
  updated_at      TIMESTAMPTZ    NOT NULL,
  UNIQUE (user_id, agent_id)
)
```

---

### Fase 4 — Identidade Visual Persistente (F10.4)
**Objetivo:** Permitir configuração de aparência/comportamento da UI.

**Preferências UI:**
- `theme`: "dark" | "light" | "auto"
- `font_size`: "small" | "medium" | "large"
- `sidebar_collapsed`: boolean
- `notifications_enabled`: boolean

**Storage:**
- Mesmo modelo key-value (scope: "ui")
- Frontend consome via GET /preferences?scope=ui

---

### Fase 5 — Histórico Auditável (F11)
**Objetivo:** Armazenar histórico mínimo de interações (sem prompts brutos).

**NÃO armazenar:**
- ❌ Prompts completos (privacy violation)
- ❌ Respostas LLM completas
- ❌ Dados sensíveis de clientes

**ARMAZENAR (apenas metadados):**
- ✅ Timestamp da interação
- ✅ action executado (ex: "code_review")
- ✅ executor_id (qual LLM)
- ✅ status (SUCCESS/FAILED)
- ✅ trace_id (correlação com audit log)

**Tabela proposta:**
```sql
interaction_history (
  id              UUID           PRIMARY KEY,
  user_id         VARCHAR(255)   NOT NULL,
  action          VARCHAR(64)    NOT NULL,
  executor_id     VARCHAR(64)    NOT NULL,
  status          VARCHAR(16)    NOT NULL,
  trace_id        VARCHAR(36)    NOT NULL,
  created_at      TIMESTAMPTZ    NOT NULL,
  INDEX (user_id, created_at DESC)
)
```

**Retenção:**
- 90 dias default (configurável por org)
- Purge automático via cron
- Export para S3 antes de purge (compliance)

---

## 🔐 PRINCÍPIOS V-COF INVARIANTES

**Não negociáveis em todas as fases:**

1. **Estado Explícito**
   - Usuário define todas as preferências
   - Sem inferência automática de padrões comportamentais
   - Sem "aprendizado" silencioso

2. **Fail-Closed**
   - Preferência inválida → rejeitar request (não usar default silencioso)
   - Scope desconhecido → HTTP 400
   - Key fora da allowlist → HTTP 400

3. **Privacy-by-Design**
   - Nenhum log de valores de preferências
   - Nenhum log de prompts/respostas
   - user_id hasheado em logs externos
   - Dados sensíveis nunca em métricas Prometheus

4. **Governança > Conveniência**
   - Preferir rejeição explícita a comportamento ambíguo
   - Validação rigorosa em todas as camadas
   - Auditabilidade completa (trace_id em tudo)

5. **Memória Dignificada**
   - Usuário sempre pode visualizar o que foi armazenado
   - Usuário sempre pode editar/apagar
   - Transparência total sobre o que o sistema "lembra"

---

## 📅 CRONOGRAMA TENTATIVO

| Fase | Sprint | Duração | Dependências |
|------|--------|---------|--------------|
| F9.9-A (atual) | Sprint 1 | ✅ CONCLUÍDO | - |
| F10.1 (Key-Value) | Sprint 2-3 | 5-7 dias | F9.9-A ✅ |
| F10.2 (Escopos) | Sprint 4 | 3-4 dias | F10.1 ✅ |
| F10.3 (Agentes) | Sprint 5 | 4-5 dias | F10.2 ✅ |
| F10.4 (UI Identity) | Sprint 6 | 2-3 dias | F10.1 ✅ |
| F11 (Histórico) | Sprint 7-8 | 5-7 dias | F10.x ✅ |

**Total estimado:** 6-8 semanas (conservador)

---

## 🚨 RISCOS ESTRATÉGICOS

### Risco 1: Migração Key-Value
**Descrição:** Alteração de schema pode causar downtime ou inconsistência.  
**Mitigação:** Blue-green deployment + rollback testado.

### Risco 2: Multi-Tenancy
**Descrição:** Escopos org/agent aumentam complexidade de segurança.  
**Mitigação:** Isolation por row-level security (PostgreSQL RLS).

### Risco 3: Performance (Histórico)
**Descrição:** Tabela interaction_history pode crescer indefinidamente.  
**Mitigação:** Particionamento por mês + purge automático.

### Risco 4: LGPD (Histórico)
**Descrição:** Armazenar metadados pode violar direito ao esquecimento.  
**Mitigação:** Export + purge obrigatório, usuário pode solicitar delete.

---

## 🔗 REFERÊNCIAS

- Copilot Instructions: `.github/copilot-instructions.md`
- V-COF Principles: Documentação Verittà (interna)
- F9.9-A Implementation: `app/routes/preferences.py`
- SEAL F9.9-A: `sessions/f9.9-a/SEAL-F9.9-A.md` (pending)

---

**Última revisão:** 2026-01-04  
**Revisores:** Vinícius Soares de Souza (Tech Lead)  
**Status:** PLANEJAMENTO (não implementação)  

---

**NOTA IMPORTANTE:**  
Este documento registra **intenções** para roadmap futuro.  
Não altera o escopo do Sprint 1 (F9.9-A).  
Decisões finais de priorização são do Product Owner.
