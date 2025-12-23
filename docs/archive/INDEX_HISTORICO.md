# Índice Histórico — Techno OS Backend

**Data:** 2025-12-23  
**Processo:** Higienização Samurai — Consolidação de artefatos históricos  
**Princípio:** Rastreabilidade + Zero Automação Destrutiva

---

## Estrutura de Archive

```
docs/archive/
├── fase-1/               (Documentação e specs de Phase 1)
├── fase-2/               (Documentação e specs de Phase 2 + atualizações)
├── canonical/            (Documentação canônica estável)

artifacts/archive/
├── audits/               (Logs e auditoria históricos)
├── diagnostics/          (Diagnostics de fases anteriores)
├── opinions/             (Pareceres técnicos históricos)
├── patches/              (Patches e hotfixes históricos)
├── phases/               (Documentação de fases)
├── reports/              (Relatórios e análises antigas)
├── sprints/              (Planejamento de sprints antigos)
```

---

## Conteúdo Movido

### docs/archive/fase-2/
| Item | Origem | Motivo | Status |
|---|---|---|---|
| AG02_SEAL_CRITERIA.txt | `docs/AG02_SEAL_CRITERIA.txt` | Critérios de seal Phase 2 (histórico) | Arquivado |
| AG03_SEAL_CRITERIA.txt | `docs/AG03_SEAL_CRITERIA.txt` | Critérios de seal Phase 3 (histórico) | Arquivado |
| dev-requirements.txt | `dev-requirements.txt` (raiz) | Dev dependencies (duplicação; consolidado em requirements.txt) | Arquivado |

### artifacts/archive/
| Item | Origem | Motivo | Status |
|---|---|---|---|
| audits/ | `artifacts/audits/` | Logs de auditoria históricos | Arquivado |
| diagnostics/ | `artifacts/diagnostics/` | Diagnósticos de fases anteriores | Arquivado |
| opinions/ | `artifacts/opinions/` | Pareceres técnicos históricos | Arquivado |
| patches/ | `artifacts/patches/` | Patches e hotfixes históricos | Arquivado |
| phases/ | `artifacts/phases/` | Documentação de fases | Arquivado |
| reports/ | `artifacts/reports/` | Relatórios antigos | Arquivado |
| sprints/ | `artifacts/sprints/` | Planejamento antigo | Arquivado |

---

## Arquivos Deletados

| Arquivo | Razão | Data |
|---|---|---|
| smoke_test_event_type.py | Teste legado (Phase 1); não utilizado em Stage 2 | 2025-12-23 |
| diagnose-tests.py | Script diagnose (Phase 1); não utilizado | 2025-12-23 |

---

## Mudanças em Workflows

### `.github/workflows/ag03-governance.yml`
**Mudança:** Removida referência a `dev-requirements.txt` (consolidado em `requirements.txt`)

**Antes:**
```yaml
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

**Depois:**
```yaml
pip install -r requirements.txt
```

---

## Referências Ativas (MANTIDAS)

✅ **Documentação ativa (não movida):**

- `docs/active/` — Documentação ativa
- `docs/api/` — Especificações API
- `docs/contracts/` — Contatos técnicos
- `docs/governance/` — Governança V-COF
- `docs/implementation/` — Guias de implementação
- `docs/protocols/` — Protocolos ativos
- `docs/ADMIN_API.md` — Especificação ADMIN API
- `docs/AUDIT_LOG_SPEC.md` — Especificação Audit Log
- `docs/ERROR_ENVELOPE.md` — Protocolo ERROR_ENVELOPE
- `docs/RUNBOOK_SAMURAI.md` — Runbook operacional
- `requirements.txt` — Dependências consolidadas
- `.github/workflows/` — CI/CD ativos

✅ **Código ativo (não movido):**

- `app/` — Código backend principal
- `tests/` — Suite de testes
- `scripts/` — Utilitários de operação

---

## Verificação de Integridade

✅ **Ripgrep verification:**
- ✅ smoke_test_event_type.py: Nenhuma referência interna (SEGURO para deletar)
- ✅ diagnose-tests.py: Nenhuma referência interna (SEGURO para deletar)
- ✅ dev-requirements.txt: Consolidado em requirements.txt (SEGURO para arquivo)
- ⚠️ Referências externas em docs/archive/ (histórico — esperado)

✅ **Workflow validation:**
- `.github/workflows/ag03-governance.yml` atualizado (sem quebras)
- CI/CD: Ready para próxima execução

✅ **Build validation:**
- `pytest` → PASS
- Nenhum import quebrado
- Nenhuma referência externa quebrada

---

## Recuperação

Se houver necessidade de restaurar algum arquivo:

1. Dentro do mesmo repositório:  
   `docs/archive/` ou `artifacts/archive/`

2. Histórico git:  
   `git log --all -- <arquivo>`  
   `git checkout <commit> -- <arquivo>`

---

## Assinatura

- **Processo:** Higienização Samurai v1
- **Executor:** Copilot (GitHub)
- **Status:** ✅ VALIDADO + PYTEST PASSING
- **Data Conclusão:** 2025-12-23
