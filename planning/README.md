# Planning — Roadmap e Backlog

## 📋 Propósito

Este diretório centraliza planejamento de fases, roadmap e backlog do projeto.

---

## 🗂️ Estrutura

```
planning/
├── README.md                          # Este arquivo
├── ROADMAP.md                         # Roadmap consolidado (todas as fases)
├── HARDENING-PENDENCIES-F9.9-B.md     # Pendências fase atual (F9.9-B)
├── WORKSPACE-REORGANIZATION-PLAN.md   # Plano de reorganização workspace
└── backlog/                           # Issues e pendências futuras
```

---

## 📚 Documentos Principais

### ROADMAP.md
**Propósito:** Visão geral de todas as fases do projeto.

**Conteúdo:**
- Fases concluídas (F9.7, F9.8, F9.8A, F9.8.1, STEP 10.2)
- Fase atual (F9.9-B: LLM Hardening)
- Próximas fases (F10, F11, F12, ...)
- Objetivos e critérios de sucesso por fase

**Atualização:** Após cada release tag.

### HARDENING-PENDENCIES-F9.9-B.md
**Propósito:** Registro de riscos e pendências para F9.9-B.

**Conteúdo:**
- RISK-1 a RISK-8 (status: resolvido/pendente)
- Acceptance criteria por risco
- Mitigations propostas
- Pré-requisitos e bloqueadores

**Atualização:** Durante execução de F9.9-B.

### WORKSPACE-REORGANIZATION-PLAN.md
**Propósito:** Plano detalhado de reorganização de workspace.

**Conteúdo:**
- Objetivos da reorganização
- Estrutura proposta (enterprise standard)
- Checklist de execução
- Riscos e mitigações

**Status:** Executado em 2026-01-03 (ver commit).

---

## 🔄 Workflow de Planejamento

### 1. Definir Nova Fase
```bash
# Criar documento de pendências
vim planning/HARDENING-PENDENCIES-F[fase].md
```

**Template:**
```markdown
# HARDENING PENDENCIES — F[fase]

## METADATA
- Fase: F[fase]
- Dependência: F[fase-anterior]
- Status: PLANNING
- Data: [data]

## OBJETIVOS
1. Objetivo 1
2. Objetivo 2

## RISCOS
### RISK-1: [descrição]
- Impacto: [alto/médio/baixo]
- Mitigação: [proposta]

## ACCEPTANCE CRITERIA
- [ ] Critério 1
- [ ] Critério 2

## EVIDÊNCIAS NECESSÁRIAS
- Artifact 1: [descrição]
- Artifact 2: [descrição]
```

### 2. Atualizar ROADMAP
```bash
vim planning/ROADMAP.md

# Adicionar fase na seção apropriada:
## Próximas Fases
### F[fase] — [Nome da Fase]
**Objetivo:** [descrição]
**Status:** PLANNING
**Prazo estimado:** [data]
```

### 3. Durante Execução
- Atualizar status de riscos no documento de pendências
- Marcar critérios de aceitação conforme completados
- Adicionar referências a artifacts coletados

### 4. Após Conclusão
```bash
# Mover documento para archive (opcional)
# ou manter em planning/ com status COMPLETE

# Atualizar ROADMAP
vim planning/ROADMAP.md
# Mover fase de "Próximas" para "Concluídas"
```

---

## 📝 Backlog

**Diretório:** `planning/backlog/`

**Propósito:** Issues e pendências não priorizadas ainda.

**Estrutura:**
```
backlog/
├── features/      # Novas funcionalidades
├── bugs/          # Bugs conhecidos (não críticos)
├── tech-debt/     # Débito técnico
└── research/      # Spikes de pesquisa
```

**Workflow:**
1. Criar arquivo markdown para cada item
2. Priorizar durante planning
3. Quando priorizado, mover para documento de pendências da fase correspondente

---

## 🎯 Critérios de Sucesso de Planning

**Planning considerado completo quando:**

1. ✅ Objetivos da fase claramente definidos
2. ✅ Riscos identificados com mitigações propostas
3. ✅ Acceptance criteria mensuráveis
4. ✅ Dependências de fases anteriores validadas
5. ✅ Estimativa de esforço (tempo, recursos)
6. ✅ Evidências necessárias listadas
7. ✅ Aprovação de Tech Lead

---

## 📚 Referências

- **Estado Atual:** `/sessions/consolidation/SEAL-SESSION-*.md`
- **Arquitetura:** `/ARCHITECTURE.md`
- **Governança:** `.github/copilot-instructions.md`
- **Histórico:** `/sessions/f9.x/SEAL-*.md`

---

**Criado:** 2026-01-03  
**Atualização:** Contínua durante desenvolvimento  
**Governança:** Human-in-the-loop, evidence-based planning
