# 🏗️ WORKSPACE REORGANIZATION PLAN — Enterprise Standard
**Preparação para F9.9-B e Colaboração Multi-Arquiteto**

---

## 📋 METADATA

- **Data:** 2026-01-03T23:40:00Z
- **Fase:** Pré-F9.9-B (Workspace Hardening)
- **Objetivo:** Transformar workspace em padrão enterprise seguindo V-COF
- **Criticidade:** MÉDIA (não bloqueia F9.9-B, mas melhora governança)

---

## 🎯 OBJETIVOS DA REORGANIZAÇÃO

### 1. Governança de Documentação (V-COF Compliance)
- **Separar contextos:** Técnico, Comercial, Narrativo (sessões)
- **Rastreabilidade:** Histórico de decisões acessível e organizado
- **Redução de ruído:** Workspace limpo facilita onboarding de novos arquitetos
- **Auditabilidade:** Estrutura clara para compliance LGPD e valuation

### 2. Colaboração Multi-Arquiteto
- **Clareza de entrada:** Novo arquiteto sabe onde procurar contexto
- **Segurança de edição:** SEAL documents são read-only (via README)
- **Consistência:** Convenções de nomenclatura e estrutura de pastas
- **Human-in-the-loop:** Documentação facilita code review e pair programming

### 3. Preparação para Escala
- **CI/CD friendly:** Estrutura compatível com pipelines automatizados
- **Artifact retention:** Política clara de retenção de evidências
- **Disaster recovery:** Backups organizados e documentados
- **Knowledge base:** Documentação técnica separada de sessions logs

---

## 🗂️ ESTRUTURA PROPOSTA (ENTERPRISE STANDARD)

```
techno-os-backend/
├── .github/                      # CI/CD, templates, copilot-instructions
├── app/                          # Código fonte (não modificar estrutura)
├── tests/                        # Testes (não modificar estrutura)
├── scripts/                      # Automações operacionais
│
├── docs/                         # 📚 DOCUMENTAÇÃO TÉCNICA
│   ├── README.md                 # Índice master da documentação
│   ├── architecture/             # Decisões arquiteturais (ADR format)
│   ├── implementation/           # Guias de implementação (atual P3, AG03, etc.)
│   ├── operations/               # Runbooks, procedimentos operacionais
│   ├── audits/                   # Pareceres comerciais, valuation
│   └── governance/               # Políticas V-COF, LGPD, compliance
│
├── sessions/                     # 🔐 SEAL DOCUMENTS (READ-ONLY)
│   ├── README.md                 # IMPORTANTE: "Não editar SEALs, criar novos"
│   ├── f9.7/
│   │   └── SEAL-F9.7.md
│   ├── f9.8/
│   │   ├── SEAL-F9.8-CONSOLIDATED.md
│   │   ├── SEAL-F9.8-HOTFIX.md
│   │   ├── SEAL-F9.8-OBSERVABILITY-EXTERNAL.md
│   │   └── F9.8-SEAL-v1.1-EVIDENCE-BASED-REVIEW.md
│   ├── f9.8a/
│   │   └── SEAL-F9.8A-SSH-SUDO-AUTOMATION.md
│   ├── f9.8.1/
│   │   └── SEAL-F9.8.1-PROMETHEUS-AUTH.md
│   ├── step-10.2/
│   │   └── SEAL-STEP-10.2-SSH-HARDENING.md
│   └── consolidation/
│       └── SEAL-SESSION-20260103-F9.8-CONSOLIDATION.md
│
├── artifacts/                    # 💾 EVIDÊNCIAS E LOGS
│   ├── README.md                 # Política de retenção: 90 dias
│   ├── f9_7/                     # Evidências F9.7
│   ├── f9_8/                     # Evidências F9.8 (múltiplas subpastas)
│   ├── f9_8a/                    # Evidências F9.8A
│   ├── f9_8_1/                   # Evidências F9.8.1
│   └── archive/                  # Artifacts >90 dias (compactados)
│
├── backups/                      # 🔄 BACKUPS E DISASTER RECOVERY
│   ├── README.md                 # Procedimentos de restore
│   ├── pre_f9_9b/                # Backup pré-F9.9-B
│   └── archive/                  # Backups antigos (>30 dias)
│
├── planning/                     # 📝 PLANEJAMENTO E ROADMAP
│   ├── README.md                 # Como usar este diretório
│   ├── ROADMAP.md                # Roadmap consolidado
│   ├── HARDENING-PENDENCIES-F9.9-B.md
│   └── backlog/                  # Issues e pendências futuras
│
├── observability/                # Configs Prometheus, Grafana (não modificar)
├── nginx/                        # Configs Nginx (não modificar)
├── alembic/                      # Migrations (não modificar)
│
├── README.md                     # 🏠 ENTRADA PRINCIPAL DO PROJETO
├── CONTRIBUTING.md               # 🤝 NOVO: Guia para novos arquitetos
├── ARCHITECTURE.md               # 🏛️ NOVO: Visão arquitetural high-level
├── CHANGELOG.md                  # 📜 NOVO: Histórico de releases (auto-gerado)
│
└── [arquivos de configuração raiz]
    ├── docker-compose*.yml
    ├── requirements.txt
    ├── pytest.ini
    └── etc.
```

---

## 🚮 ITENS PARA REMOÇÃO/MOVIMENTAÇÃO

### ❌ Deletar (Ruído)

**Cache e temp files:**
```bash
.mypy_cache/          # 48MB — regenerável, já em .gitignore
.pytest_cache/        # 44KB — regenerável, já em .gitignore
app.db                # DB local de dev (se não usado)
actions_fingerprint.lock  # Lock file de CI
```

**Backups redundantes (root):**
```bash
backup_f9_7_pre_deploy.tar.gz  # Redundante com /artifacts/f9_7/ ou backups/
```

**Documentos obsoletos (root):**
```bash
# Code Citations.md              # Verificar se ainda relevante (pode mover para docs/)
CONFORMIDADE_EXECUTION_SEMANTICS_V1.txt  # Mover para docs/governance/
EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt # Mover para docs/governance/
```

### 📦 Mover para Estrutura Proposta

**SEALs (root → sessions/):**
```bash
SEAL-F9.8-CONSOLIDATED.md                    → sessions/f9.8/
SEAL-F9.8-HOTFIX.md                          → sessions/f9.8/
SEAL-F9.8-OBSERVABILITY-EXTERNAL.md          → sessions/f9.8/
SEAL-F9.8-OBSERVABILITY-EXTERNAL-v1.0-ORIGINAL.md → sessions/f9.8/
F9.8-SEAL-v1.1-EVIDENCE-BASED-REVIEW.md      → sessions/f9.8/
F9.8-SEAL-v1.1-CHANGELOG.md                  → sessions/f9.8/
SEAL-F9.8.1-PROMETHEUS-AUTH.md               → sessions/f9.8.1/
SEAL-F9.8A-SSH-SUDO-AUTOMATION.md            → sessions/f9.8a/
SEAL-STEP-10.2-SSH-HARDENING.md              → sessions/step-10.2/
SEAL-SESSION-20260103-F9.8-CONSOLIDATION.md  → sessions/consolidation/
```

**Planning (root → planning/):**
```bash
ROADMAP.md                        → planning/
HARDENING-PENDENCIES-F9.9-B.md    → planning/
BACKUP-PRE-F9.9-B.md              → backups/pre_f9_9b/README.md (renomear)
```

**Documentation (root → docs/):**
```bash
FILE-INDEX.md                     → docs/FILE-INDEX.md (ou deletar se obsoleto)
CONFORMIDADE_EXECUTION_SEMANTICS_V1.txt → docs/governance/
EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt → docs/governance/
```

**Artifacts (reorganizar por fase):**
```bash
artifacts/workspace_cleanup_*     → artifacts/f9_6/ (consolidar)
artifacts/f9_5_3_1_full_edge_gate → artifacts/f9_5/
artifacts/f9_6_0_post_go          → artifacts/f9_6/
artifacts/audit_report.md         → docs/audits/ (se ainda relevante)
```

---

## 🆕 ARQUIVOS NOVOS A CRIAR

### 1. CONTRIBUTING.md (Onboarding de Arquitetos)
**Localização:** `/CONTRIBUTING.md`  
**Conteúdo:**
- Como configurar ambiente local
- Convenções de commit (conventional commits)
- Como criar SEAL documents (nunca editar, sempre criar novo)
- Fluxo de trabalho Git (branches, PRs)
- Governança V-COF resumida
- Como interagir com GitHub Copilot (copilot-instructions.md)

### 2. ARCHITECTURE.md (Visão High-Level)
**Localização:** `/ARCHITECTURE.md`  
**Conteúdo:**
- Diagrama de componentes (API, LLM Gateway, DB, Observability)
- Decisões arquiteturais principais (ADRs resumidas)
- Stack tecnológico (FastAPI, PostgreSQL, Prometheus, Grafana)
- Fluxo de requisição (cliente → API → LLM → response)
- Separação de responsabilidades (camadas)

### 3. CHANGELOG.md (Histórico de Releases)
**Localização:** `/CHANGELOG.md`  
**Conteúdo:**
- Formato: Keep a Changelog (https://keepachangelog.com/)
- Baseado em tags Git (v9.8-observability-complete, etc.)
- Seções: Added, Changed, Fixed, Security
- Geração automática via script (scripts/generate_changelog.sh)

### 4. sessions/README.md (Governança de SEALs)
**Localização:** `/sessions/README.md`  
**Conteúdo:**
```markdown
# SEAL Documents — Governança V-COF

## ⚠️ IMPORTANTE: READ-ONLY

SEALs são **registros imutáveis** de sessões de trabalho.

**NUNCA edite um SEAL existente.** Se precisar corrigir ou atualizar:
1. Crie novo SEAL com sufixo `-v1.1`, `-v1.2`, etc.
2. Referencie o SEAL original no novo documento
3. Documente o motivo da correção

## Estrutura

- `f9.x/` — SEALs de cada fase (F9.7, F9.8, etc.)
- `consolidation/` — Snapshots canônicos de continuidade
- Nomenclatura: `SEAL-[FASE]-[DESCRIÇÃO].md`

## Consulta

Para entender estado atual do projeto, leia:
1. `/sessions/consolidation/SEAL-SESSION-[DATA]-*.md` (último snapshot)
2. `/planning/ROADMAP.md` (próximas fases)
3. `/ARCHITECTURE.md` (visão geral)
```

### 5. artifacts/README.md (Política de Retenção)
**Localização:** `/artifacts/README.md`  
**Conteúdo:**
```markdown
# Artifacts — Evidence Collection

## Política de Retenção

- **Fase ativa:** 90 dias (evidências rastreáveis)
- **Após 90 dias:** Mover para `archive/` (compactado .tar.gz)
- **Após 1 ano:** Deletar de `archive/` (manter apenas em backup VPS)

## Estrutura

- `f9_x/` — Evidências de cada fase
- `archive/` — Artifacts compactados antigos
- Nomenclatura: `[fase]_[descrição]_[timestamp]/`

## Consulta

Para validar implementação de uma fase:
1. Localizar pasta da fase (ex: `f9_8_1_risk1_*/`)
2. Verificar `checksums.sha256` (integridade)
3. Ler logs e outputs coletados
```

### 6. backups/README.md (Disaster Recovery)
**Localização:** `/backups/README.md`  
**Conteúdo:**
```markdown
# Backups — Disaster Recovery

## Procedimento de Restore

Veja: `/docs/operations/DISASTER_RECOVERY.md`

## Política de Retenção

- **Pre-deploy backups:** 30 dias (antes de cada fase crítica)
- **Daily backups (VPS):** 7 dias (se implementado)
- **Após 30 dias:** Mover para `archive/` (compactado)

## Backup Atual

- `pre_f9_9b/` — Backup VPS antes de F9.9-B LLM Hardening
  - Localização VPS: `/opt/techno-os/backups/pre_f9_9b_20260103_161929`
  - Tamanho: 160KB (configs + observability + artifacts)
```

### 7. docs/operations/DISASTER_RECOVERY.md (Procedimentos)
**Localização:** `/docs/operations/DISASTER_RECOVERY.md`  
**Conteúdo:**
- Procedimento de restore de backup VPS
- Rollback de docker-compose stack
- Rollback de configs Nginx
- Restore de dados Grafana/Prometheus
- Testes de validação pós-restore
- Tempo estimado: 15-20min

---

## 📝 CHECKLIST DE EXECUÇÃO

### Fase 1: Preparação (5min)
- [ ] Criar branch: `chore/workspace-reorganization`
- [ ] Backup local: `tar czf ~/workspace_backup_$(date +%s).tar.gz .`
- [ ] Validar que workspace está clean: `git status` → no uncommitted changes

### Fase 2: Criar Estrutura Nova (3min)
- [ ] Criar diretórios: `sessions/`, `planning/`, `backups/`
- [ ] Criar READMEs em cada diretório novo
- [ ] Criar arquivos novos: `CONTRIBUTING.md`, `ARCHITECTURE.md`, `CHANGELOG.md`

### Fase 3: Movimentação de Arquivos (10min)
- [ ] Mover SEALs (root → sessions/)
- [ ] Mover planning docs (root → planning/)
- [ ] Mover backups (root → backups/)
- [ ] Mover governance docs (root → docs/governance/)
- [ ] Reorganizar artifacts/ por fase

### Fase 4: Limpeza (2min)
- [ ] Deletar caches: `.mypy_cache/`, `.pytest_cache/`
- [ ] Deletar backups redundantes root
- [ ] Deletar lock files temporários

### Fase 5: Atualização de Links (5min)
- [ ] Atualizar links internos em README.md principal
- [ ] Atualizar links em ROADMAP.md
- [ ] Validar que SEALs ainda referenciam corretamente evidências em artifacts/

### Fase 6: Validação (3min)
- [ ] Executar testes: `pytest` → todos passam
- [ ] Validar imports: `python -m app.main` → sem erros
- [ ] Git status: Apenas movimentações esperadas

### Fase 7: Commit e Documentação (2min)
- [ ] Stage all: `git add .`
- [ ] Commit: `chore: reorganize workspace to enterprise standard (V-COF)`
- [ ] Create PR: `chore/workspace-reorganization` → `stage/f9.9-b-llm-hardening`
- [ ] Self-review: Validar diff no GitHub

**Tempo Total Estimado:** 30 minutos

---

## 🎯 BENEFÍCIOS PÓS-REORGANIZAÇÃO

### Para Arquitetos Atuais
- ✅ Workspace limpo facilita foco em F9.9-B
- ✅ SEALs organizados permitem consulta rápida de decisões passadas
- ✅ Artifacts não poluem root directory

### Para Novos Arquitetos (Onboarding)
- ✅ `CONTRIBUTING.md` → Como começar
- ✅ `ARCHITECTURE.md` → Entender sistema em 10min
- ✅ `sessions/` → Histórico de decisões rastreável
- ✅ `docs/` → Documentação técnica centralizada

### Para Compliance e Auditoria
- ✅ SEALs imutáveis provam governança V-COF
- ✅ Artifacts rastreáveis para cada fase
- ✅ Política de retenção clara (LGPD compliance)
- ✅ Disaster recovery documentado

### Para Operações (DevOps/SRE)
- ✅ `docs/operations/` → Runbooks padronizados
- ✅ `backups/` → Disaster recovery claro
- ✅ `scripts/` → Automações documentadas
- ✅ `observability/` → Configs de monitoramento isoladas

---

## 🚨 RISCOS E MITIGAÇÕES

### RISCO: Links quebrados após movimentação
**Mitigação:** Fase 5 do checklist valida links internos  
**Rollback:** Git revert (branch separada)

### RISCO: Perda de histórico Git em movimentações
**Mitigação:** Usar `git mv` (preserva histórico)  
**Validação:** `git log --follow sessions/f9.8/SEAL-F9.8-CONSOLIDATED.md`

### RISCO: CI/CD quebra após reorganização
**Mitigação:** Validar pytest e imports antes de commit  
**Rollback:** Branch isolada permite rollback fácil

### RISCO: Tempo de execução excede estimado
**Mitigação:** Executar em etapas, commit intermediários permitidos  
**Alternativa:** Fazer reorganização parcial (apenas SEALs primeiro)

---

## 🔄 ALTERNATIVA: REORGANIZAÇÃO INCREMENTAL

Se 30min é muito tempo agora, **fazer em 3 etapas:**

### Etapa 1 (10min): SEALs e Planning
- Mover apenas SEALs → `sessions/`
- Mover planning docs → `planning/`
- Criar READMEs básicos

### Etapa 2 (10min): Documentação Nova
- Criar `CONTRIBUTING.md`, `ARCHITECTURE.md`
- Criar READMEs em `sessions/`, `artifacts/`, `backups/`

### Etapa 3 (10min): Limpeza e Artifacts
- Deletar caches e backups redundantes
- Reorganizar `artifacts/` por fase

**Cada etapa é um commit isolado, pode ser pausada entre F9.9-B tasks.**

---

## 📊 MÉTRICAS DE SUCESSO

**Workspace considerado "Enterprise Standard" quando:**

1. ✅ Novo arquiteto consegue entender projeto lendo 3 arquivos:
   - `README.md` → O que é o projeto
   - `ARCHITECTURE.md` → Como funciona
   - `CONTRIBUTING.md` → Como contribuir

2. ✅ SEALs estão organizados e protegidos contra edição acidental

3. ✅ Root directory tem <10 arquivos .md/.txt (atualmente 19)

4. ✅ Artifacts organizados por fase (não misturados no root)

5. ✅ Políticas de retenção documentadas (artifacts, backups)

6. ✅ Disaster recovery testável (procedimentos claros)

---

## 🎬 PRÓXIMOS PASSOS

**APÓS APROVAÇÃO DESTE PLANO:**

1. **Decisão:** Reorganização completa (30min) ou incremental (3x 10min)?
2. **Aprovação:** Tech Lead valida estrutura proposta
3. **Execução:** Seguir checklist fase por fase
4. **Validação:** Self-review no PR antes de merge
5. **Prosseguir:** Iniciar F9.9-B com workspace limpo

**Aguardando sua decisão para prosseguir.**

---

**FIM DO PLANO DE REORGANIZAÇÃO**  
**Data:** 2026-01-03T23:40:00Z  
**Assinatura V-COF:** Evidence-based planning, human-in-the-loop
