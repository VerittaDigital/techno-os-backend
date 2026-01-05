# F9.9-B Evidence Pack

**Sprint**: F9.9-B — LLM Hardening  
**Branch**: feature/f9-9-b-llm-hardening  
**Commit**: [pending]  
**Testes**: 17/17 PASS  
**Linhas**: 752 linhas (5 novos + 3 modificados)

---

## ARTEFATOS

1. **git_history.txt** — Histórico git (últimos 10 commits)
2. **test_results.txt** — Output completo pytest (17 testes)
3. **diff_summary.txt** — Diff summary main vs branch
4. **lines_of_code.txt** — Contagem de linhas por arquivo

---

## MÉTRICAS

### Arquivos
- **Criados**: 5
  - errors.py (28 linhas)
  - response.py (39 linhas)
  - retry.py (71 linhas)
  - circuit_breaker.py (95 linhas)
  - metrics.py (35 linhas)

- **Modificados**: 3
  - factory.py (+30 linhas, fail-closed)
  - openai_client.py (+22 linhas, metrics)
  - test_f9_9_b_llm_hardening.py (282 linhas, 17 testes)

### Cobertura de Testes
- **Factory**: 6 testes
  - fail_closed_no_allowlist
  - fail_closed_empty_allowlist
  - fail_closed_provider_not_allowed
  - success_fake_in_allowlist
  - timeout_default_30s
  - missing_api_key

- **Retry**: 5 testes
  - success_first_attempt
  - fail_after_max_retries
  - timeout_no_retry
  - non_retryable_error
  - exponential_backoff

- **Circuit Breaker**: 6 testes
  - closed_by_default
  - open_after_threshold
  - blocks_when_open
  - half_open_after_timeout
  - success_resets_counter
  - metrics_registered

### Governança V-COF
- ✅ Fail-closed: VERITTA_LLM_ALLOWED_PROVIDERS obrigatória
- ✅ Timeout endurecido: 10s → 30s
- ✅ Retry limitado: max 2 tentativas
- ✅ Circuit breaker: 3 falhas → 60s cooldown
- ✅ Observabilidade: 3 métricas Prometheus
- ✅ Zero logs de prompts/respostas (privacy)

---

## VALIDAÇÕES

### Critérios de Sucesso (F9.9-B)
1. ✅ Factory fail-closed com allowlist ENV
2. ✅ LLMResponse Pydantic normalizado
3. ✅ Retry automático (429, 5xx) com exponential backoff
4. ✅ Circuit breaker thread-safe (CLOSED/OPEN/HALF_OPEN)
5. ✅ 3 métricas Prometheus (latência, tokens, erros)
6. ✅ 17 testes unitários passando
7. ✅ Zero regressões em testes existentes

### Conformidade
- ✅ Privacy by design (sem log de PII)
- ✅ Centralidade humana (retry limitado, circuit breaker configurável)
- ✅ IA como instrumento (não decisões autônomas)
- ✅ Código legível (funções pequenas, fluxo linear)

---

## APROVAÇÕES

- [ ] Arquiteto principal
- [ ] Code review técnico
- [ ] Smoke test em dev
- [ ] Merge para main

---

**Evidências geradas em**: 2025-06-XX  
**Status**: ✅ COMPLETO
