# 🔗 LINKAGEM: PARECER BACKEND → EXECUTION PLAN

**Objetivo:** Conectar o parecer do DEV SENIOR com o plano de execução estruturado.

---

## 📍 MAPEAMENTO DE RESPONSABILIDADES

### Parecer do Arquiteto Backend (Fonte)
```
⚠️ IMPORTANTE: "Velocidade sem contrato gera retrabalho.
Contrato sólido permite paralelização segura."
```

### Plano de Execução (Destino)
```
docs/EXECUTION_PLAN_F-CONSOLE-0.1_PHASE2.md
```

---

## 📊 RASTREABILIDADE: Parecer → Etapas

| Recomendação do Backend | Etapa do Plano | Entregável | Status |
|-------------------------|----------------|-----------|--------|
| Validar endpoints reais | Etapa 1 | console-inventory.md | ⏳ TODO |
| Criar OpenAPI skeleton | Etapa 2 | openapi/console-v0.1.yaml | ⏳ TODO |
| Documentar contrato | Etapa 3 | docs/CONTRACT.md | ⏳ TODO |
| Implementar fail-closed | Etapa 4 | docs/ERROR_POLICY.md | ⏳ TODO |
| Remover segredos | Etapa 5 | .env.example, AUTH_MIGRATION.md | ⏳ TODO |
| Build reprodutível | Etapa 6 | scripts/build.sh, CI validation | ⏳ TODO |

---

## 🎯 CHECK-IN POINTS (Pontos de Verificação)

### ✅ PRÉ-EXECUÇÃO (Antes de iniciar)
```
- [ ] Parecer do DEV SENIOR lido e compreendido
- [ ] EXECUTION_PLAN_F-CONSOLE-0.1_PHASE2.md preparado
- [ ] Backend d:\Projects\techno-os-backend acessível (ou documentação disponível)
- [ ] Ferramentas instaladas (grep, npm, docker, swagger-cli)
- [ ] Todo list atualizado
```

### ✅ PÓS-ETAPA 1 (Inventário completo)
```
- [ ] Grep search executado e documentado
- [ ] console-inventory.md criado
- [ ] Todos os endpoints encontrados classificados (LEGACY/ACTIVE/DEPRECATED)
- [ ] Campos marcados como [OBSERVADO] ou [INFERIDO]
- [ ] Resultado compartilhado com DEV SENIOR para validação cruzada
```

### ✅ PÓS-ETAPA 2 (OpenAPI pronto)
```
- [ ] openapi/console-v0.1.yaml criado com validação swagger-cli ✅
- [ ] Todos os endpoints mapeados
- [ ] Schemas explícitos definidas
- [ ] Arquivo revisado por Arquiteto Backend
```

### ✅ PÓS-ETAPA 3 (Contrato explícito)
```
- [ ] docs/CONTRACT.md criado
- [ ] Versionamento de endpoints claro
- [ ] Regra de mudanças definida
- [ ] README.md atualizado com referência ao contrato
```

### ✅ PÓS-ETAPA 4 (Fail-closed implementado)
```
- [ ] docs/ERROR_POLICY.md criado
- [ ] lib/error-handling.ts implementado
- [ ] fetchWithTimeout funcionando (AbortController)
- [ ] Todos os catch blocks loggam trace_id
```

### ✅ PÓS-ETAPA 5 (Segurança validada)
```
- [ ] Grep search feito (X-API-Key, NEXT_PUBLIC_API_KEY)
- [ ] Decisão documentada (remover ou manter)
- [ ] .env.example criado (SEM segredos)
- [ ] Validação em código implementada (fail-closed)
- [ ] docs/AUTH_MIGRATION.md criado
- [ ] .env.local em .gitignore
```

### ✅ PÓS-ETAPA 6 (Build reprodutível)
```
- [ ] scripts/build.sh criado com versionamento de commit
- [ ] CI/CD workflow com validação de segredos
- [ ] BUILDING.md atualizado com procedimentos
- [ ] Docker build testado localmente
```

### ✅ PÓS-CHECK FINAL
```
- [ ] Auto-avaliação: todas as perguntas respondidas SIM
- [ ] Nenhum bloqueador pendente
- [ ] Documentação completa
- [ ] Código pronto para revisão
```

---

## 📋 CHECKLIST DE ENTREGA

**Documentação Obrigatória (8 files):**
- [ ] `docs/console-inventory.md`
- [ ] `openapi/console-v0.1.yaml`
- [ ] `docs/CONTRACT.md`
- [ ] `docs/ERROR_POLICY.md`
- [ ] `docs/AUTH_MIGRATION.md`
- [ ] `.env.example`
- [ ] `scripts/build.sh`
- [ ] Atualização de `README.md`

**Código Obrigatório (3 files):**
- [ ] `lib/error-handling.ts`
- [ ] `lib/config.ts` (com validação)
- [ ] Atualização de `lib/api-client.ts` (usar fetchWithTimeout)

**Validação Obrigatória:**
- [ ] `npm run build` ✅
- [ ] `swagger-cli validate openapi/console-v0.1.yaml` ✅
- [ ] `docker build -t techno-os-console:test .` ✅
- [ ] Nenhum segredo em bundle
- [ ] Nenhum erro em console.log (dev ou prod)

---

## 🔄 INTEGRAÇÃO COM WORKFLOW EXISTENTE

```
ANTES (estado anterior):
  └─ BACKEND_INTEGRATION_WORKFLOW.md (Phase 1: Prompt & Intake)

AGORA (novo):
  └─ EXECUTION_PLAN_F-CONSOLE-0.1_PHASE2.md (Phase 1.5: Implementation)

DEPOIS (Phase 2):
  └─ BACKEND_INTEGRATION_WORKFLOW.md (Phase 2: Evaluation)
  └─ BACKEND_INTEGRATION_WORKFLOW.md (Phase 3-6: Integration)
```

### Como usar ambos em paralelo:

1. **Atualmente (console):** Execute EXECUTION_PLAN_F-CONSOLE-0.1_PHASE2
2. **Em paralelo (backend):** Backend team implementa endpoints per OpenAPI
3. **Quando ambos prontos:** Usar BACKEND_INTEGRATION_WORKFLOW para integração conjunta

---

## 📞 ESKALAÇÃO & REVISÃO

### Se encontrar discrepância com parecer:

1. **Documentar a discrepância** no comentário do commit
2. **Contactar DEV SENIOR** via:
   - Documento: `docs/EXECUTION_DISCREPANCY_LOG.md`
   - Formato: Data | Etapa | Problema | Ação Tomada
3. **Proceder com fail-closed** (quando em dúvida, bloqueia)

### Exemplo de discrepância:

```markdown
# EXECUTION_DISCREPANCY_LOG.md

## 2026-01-04

### Discrepância 1
- **Etapa:** 1 (Inventário)
- **Encontrado:** Endpoint POST /process usa AMBOS F2.1 E F2.3
- **Parecer esperava:** Apenas F2.1
- **Ação:** Classificado como LEGACY+HYBRID, documentado em console-inventory.md
- **Status:** Resolvido (documentar em CONTRACT.md)

### Discrepância 2
- **Etapa:** 5 (Hardening)
- **Encontrado:** X-API-Key em código comentado
- **Parecer esperava:** Nenhuma referência
- **Ação:** Removido comentário, documentado em AUTH_MIGRATION.md
- **Status:** Resolvido
```

---

## 🚀 FLUXO DE EXECUÇÃO (Recomendado)

```
┌─ DIA 1 ──────────────────────────┐
│                                  │
│ 1. Ler este documento (15 min)   │
│ 2. Ler EXECUTION_PLAN (20 min)   │
│ 3. Executar Etapa 1 (2-4h)       │
│ 4. Executar Etapa 2 (4-6h)       │
│                                  │
│ Checkpoint: console-inventory.md │
│            + openapi-v0.1.yaml   │
│            ambos revisados       │
└──────────────────────────────────┘

┌─ DIA 2 ──────────────────────────┐
│                                  │
│ 5. Executar Etapa 3 (1-2h)       │
│ 6. Executar Etapa 4 (2-3h)       │
│ 7. Executar Etapa 5 (1-2h)       │
│ 8. Executar Etapa 6 (1h)         │
│                                  │
│ Checkpoint: Auto-avaliação       │
│            (todas as perguntas   │
│            respondidas SIM)      │
└──────────────────────────────────┘

┌─ FINAL ───────────────────────────┐
│                                   │
│ ✅ Documentação completa          │
│ ✅ Código implementado            │
│ ✅ Validações passando            │
│ ✅ Pronto para integração backend │
│                                   │
│ Próximo passo: Phase 2 do         │
│ BACKEND_INTEGRATION_WORKFLOW      │
└───────────────────────────────────┘
```

---

## 📍 PRÓXIMAS ETAPAS (Após EXECUTION_PLAN)

Quando este plano estiver **COMPLETO**:

1. **Backend implementa endpoints** per OpenAPI:
   - POST /api/execute
   - GET /api/audit
   - GET /api/memory
   - POST /api/diagnostic/metrics

2. **Console integra com backend:**
   - Atualizar API client calls
   - Testar fail-closed scenarios
   - Validar trace_id flow

3. **Deployment conjunto:**
   - Docker compose stack test
   - Integration tests
   - Production deployment

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Target | Atual | Final |
|---------|--------|-------|-------|
| Documentos criados | 8 | 0 | 8 ✅ |
| Código implementado | 3 | 0 | 3 ✅ |
| Validações passando | 4 | ? | 4 ✅ |
| Check final SIM | 5/5 | 0/5 | 5/5 ✅ |
| Segredos em bundle | 0 | ? | 0 ✅ |
| Tempo total | 11-18h | 0h | 11-18h ✅ |

---

**Versão:** 1.0  
**Data:** 4 de janeiro de 2026  
**Status:** ✅ PRONTO PARA EXECUÇÃO

**"Documento é contrato. Contrato é lei."** 📋
