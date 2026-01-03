# SEAL Documents — Governança V-COF

## ⚠️ IMPORTANTE: READ-ONLY

SEALs (Session Evidence and Audit Logs) são **registros imutáveis** de sessões de trabalho.

**NUNCA edite um SEAL existente.** Se precisar corrigir ou atualizar:
1. Crie novo SEAL com sufixo `-v1.1`, `-v1.2`, etc.
2. Referencie o SEAL original no novo documento
3. Documente o motivo da correção

---

## 📂 Estrutura

```
sessions/
├── f9.7/           # Fase 9.7: Observability setup
├── f9.8/           # Fase 9.8: External observability
├── f9.8a/          # Fase 9.8A: SSH hardening
├── f9.8.1/         # Fase 9.8.1: Prometheus auth
├── step-10.2/      # Step 10.2: SSH reload
└── consolidation/  # Snapshots canônicos de continuidade
```

**Nomenclatura:** `SEAL-[FASE]-[DESCRIÇÃO].md`

---

## 🔍 Consulta

Para entender o estado atual do projeto:

1. **Snapshot mais recente:**  
   `/sessions/consolidation/SEAL-SESSION-[DATA]-*.md`

2. **Próximas fases:**  
   `/planning/ROADMAP.md`

3. **Visão geral arquitetural:**  
   `/ARCHITECTURE.md`

4. **Histórico de uma fase específica:**  
   `/sessions/f9.x/SEAL-*.md`

---

## 📋 Governança

**Por que SEALs são imutáveis?**

1. **Auditabilidade:** Histórico de decisões rastreável
2. **Integridade:** Evidências não podem ser alteradas retroativamente
3. **Compliance:** LGPD e valuation exigem registros fidedignos
4. **Rastreabilidade:** Git log preserva histórico (`git log --follow`)

**Como corrigir um erro em SEAL?**

```bash
# NUNCA faça:
vim sessions/f9.8/SEAL-F9.8-CONSOLIDATED.md  # ❌ PROIBIDO

# SEMPRE faça:
cp sessions/f9.8/SEAL-F9.8-CONSOLIDATED.md \
   sessions/f9.8/SEAL-F9.8-CONSOLIDATED-v1.1.md

# Edite v1.1 e adicione no topo:
## CORREÇÃO v1.1 (2026-01-03)
Corrigindo [descrição do erro] identificado no SEAL original.
Referência: SEAL-F9.8-CONSOLIDATED.md (original)

# Commit a correção
git add sessions/f9.8/SEAL-F9.8-CONSOLIDATED-v1.1.md
git commit -m "docs(seal): correct [erro] in F9.8 SEAL (v1.1)"
```

---

## 📊 Índice de SEALs

### Fase 9.7
- **SEAL-F9.7.md** — Observability setup inicial

### Fase 9.8
- **SEAL-F9.8-CONSOLIDATED.md** — Consolidação F9.8
- **SEAL-F9.8-HOTFIX.md** — Hotfixes aplicados
- **SEAL-F9.8-OBSERVABILITY-EXTERNAL.md** — Observability externa
- **F9.8-SEAL-v1.1-EVIDENCE-BASED-REVIEW.md** — Review baseado em evidências

### Fase 9.8A
- **SEAL-F9.8A-SSH-SUDO-AUTOMATION.md** — SSH hardening + sudo automation

### Fase 9.8.1
- **SEAL-F9.8.1-PROMETHEUS-AUTH.md** — Prometheus Basic Auth (RISK-1)

### Step 10.2
- **SEAL-STEP-10.2-SSH-HARDENING.md** — SSH passwordauth disabled

### Consolidation
- **SEAL-SESSION-20260103-F9.8-CONSOLIDATION.md** — Snapshot canônico 2026-01-03

---

## 🤝 Para Novos Arquitetos

**Primeiro SEAL a ler:**  
`sessions/consolidation/SEAL-SESSION-[DATA]-*.md` (snapshot mais recente)

Este documento contém:
- Estado atual completo do sistema
- Fases concluídas e pendentes
- Decisões técnicas preservadas
- Próxima ação inequívoca

**Depois:**
- Ler SEALs de fases relevantes ao seu trabalho
- Consultar `planning/ROADMAP.md` para entender prioridades
- Consultar `ARCHITECTURE.md` para visão geral

---

**Criado:** 2026-01-03  
**Governança:** V-COF compliant  
**Política:** SEAL documents são read-only
