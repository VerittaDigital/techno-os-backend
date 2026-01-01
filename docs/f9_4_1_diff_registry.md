# F9.4.1 Diff Registry

Arquivos tocados em F9.4.1, com justificativa e risco estimado.

## App Changes (Mypy Fixes)
- app/action_matrix.py: Removido global desnecessário (F824 fix). Risco: Baixo (global não usado).
- app/db/database.py: get_db annotation para Generator. Risco: Baixo (correção de tipo).
- app/gates/admin_rate_limit.py: _requests annotation. Risco: Baixo (tipo explícito).
- app/gates/gate_f23_sessions_db.py: input_payload Optional. Risco: Baixo (correção de tipo).
- app/tools/audit_parser.py: event_type Optional. Risco: Baixo (correção de tipo).
- app/tools/orphan_reconciler.py: _parse_ts Optional[datetime]. Risco: Baixo (correção de tipo).

## Test Changes
- tests/conftest.py: Adicionado tracing_available() helper. Risco: Baixo (skip tests sem deps).
- tests/test_*.py: Removidos imports F401 triviais. Risco: Baixo (imports não usados).
- tests/test_*tracing*.py: Adicionados @pytest.mark.skipif para tracing tests. Risco: Baixo (skip quando deps indisponíveis).

Risco geral: Baixo. Mudanças mínimas, focadas em linting e tipos sem alterar lógica.