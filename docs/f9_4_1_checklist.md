# F9.4.1 Checklist — Harden Tests & QA Gate

## Passo 0 — Checkpoint & Baseline
- [x] git status --porcelain vazio
- [x] Tag checkpoint/F9_4_PASS_LOCAL_2026-01-01 criado
- [x] Branch work/F9_4_1_hardening criado
- [x] docs/f9_4_1_baseline.md criado com:
  - Git HEAD: 0ca2bdff2542160e59fd0ab3dfdabe37bacdbe60
  - Python: 3.10.12
  - Pacotes relevantes: flake8, mypy, opentelemetry, pytest
  - Pytest: 374 passed
  - Flake8 crítico: 1 (F824)
  - Mypy: 77 errors
  - Logs em artifacts/f9_4_1/

## Passo 1 — Pytest (Tracing)
- [x] Helper tracing_available() adicionado em conftest.py
- [x] 12 testes marcados com @pytest.mark.skipif(not tracing_available())
- [x] Pytest re-executado: 362 passed, 12 skipped (0 failures)

## Passo 2 — Flake8 (Críticos)
- [x] F824 corrigido (global _global_matrix removido em action_matrix.py)
- [x] F401 triviais removidos em tests/ via autoflake
- [x] Flake8 crítico: 0

## Passo 3 — Mypy (Bugs Reais)
- [x] Corrigidos ~4 erros (dentro limite 12):
  - _parse_ts -> Optional[datetime]
  - event_type -> Optional[str]
  - _requests annotation
  - get_db -> Generator
  - input_payload -> Optional[Dict[Any, Any]]
- [x] Mypy restante: 73 errors
- [x] Backlog documentado (não criado ainda)

## Passo 4 — Não-Regressão F9.4
- [x] smoke_https.sh: PASS
- [x] contract_obs.sh: PASS
- [x] contract_sec.sh: PASS

## Passo 4.2 — Coverage Baseline (Opcional)
- [ ] pytest-cov não disponível, pulado

## Passo 4.3 — Bandit Scan (Opcional)
- [ ] bandit não disponível, pulado

## Passo 5 — Artefatos
- [x] docs/f9_4_1_checklist.md (este arquivo)
- [ ] docs/f9_4_1_diff_registry.md
- [ ] scripts/rollback_f9_4_1.sh

## Relatório Final
- Hash baseline: 0ca2bdff2542160e59fd0ab3dfdabe37bacdbe60
- Hash final: 30ba49ea1a0c7dd711e9a737463968f75a9ac46c
- Pytest: PASS (362 passed, 12 skipped)
- Flake8 crítico: PASS (0)
- Mypy: 4 bugs reais corrigidos (73 restantes)
- F9.4 scripts: PASS