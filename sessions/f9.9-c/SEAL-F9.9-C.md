# SEAL F9.9-C: Integration + Observability

**Sprint:** F9.9-C  
**Objetivo:** Integração de retry + circuit breaker no executor LLM + observabilidade operacional  
**Base:** F9.9-B-SEALED (7141cad)  
**Status:** ✅ SEALED  
**Data:** 2026-01-05

---

## Resumo Executivo

Sprint focado em integração dos componentes de resiliência (retry + circuit breaker) no executor LLM e operacionalização da observabilidade.

**Entregas:**
- ✅ EIXO 1: Integration (circuit breaker singleton, executor integrado, timeout 30s)
- ❌ EIXO 2: Prometheus alerts (**BLOQUEADO**: Prometheus não está em docker-compose.yml)
- ✅ EIXO 3: Backup automation (script + 7-day retention)
- ✅ EIXO 4: Documentation (RUNBOOK_OBSERVABILITY.md + README)
- ✅ EIXO 5: Tests (8 cenários, 100% pass rate)

---

## Eixos Implementados

### EIXO 1: Integration — ✅ COMPLETO

**Artefatos:**
- [app/llm/circuit_breaker_singleton.py](../../app/llm/circuit_breaker_singleton.py) (45 linhas)
  - Singleton thread-safe (double-check locking)
  - `get_circuit_breaker()` com constants `THRESHOLD=3`, `TIMEOUT=60`
  - ENV support planejado para F9.10+

- [app/llm/policy.py](../../app/llm/policy.py) (modificado)
  - `Policy.TIMEOUT_S` atualizado: 10.0 → 30.0
  - Comentário F9.9-C adicionado

- [app/executors/llm_executor_v1.py](../../app/executors/llm_executor_v1.py) (modificado)
  - `__init__`: `self._circuit_breaker = get_circuit_breaker()`
  - `execute()`: Wrapper `self._circuit_breaker.call()`
  - Novo método `_call_llm_with_retry()` com decorador `@with_retry(max_retries=2)`
  - Fluxo: Request → Circuit Breaker → Retry → LLM Provider

**Validação:**
```python
# tests/test_f9_9_c_integration.py
- test_circuit_breaker_opens_after_3_failures  ✅
- test_circuit_breaker_blocks_when_open        ✅
- test_circuit_breaker_half_open_after_timeout ✅
- test_retry_on_429_error                      ✅
- test_retry_max_2_attempts                    ✅
- test_no_retry_on_timeout                     ✅
- test_timeout_policy_30s                      ✅
- test_executor_respects_policy_timeout        ✅
```

---

### EIXO 2: Prometheus Alerts — ❌ BLOQUEADO

**Blocker:**
Prometheus não está em `docker-compose.yml`. Configuração atual usa Prometheus standalone (fora do docker-compose), o que impede a definição de alert rules no contexto containerizado.

**Arquivos inspecionados:**
- `prometheus.yml` existe (standalone configuration)
- `docker-compose.yml` não contém serviço `prometheus`
- Pre-flight validation detectou ausência (checkpoint 5 failed)

**Documentação:**
- RUNBOOK_OBSERVABILITY.md documenta Prometheus como standalone
- Backup script tem seção comentada para prometheus/grafana (futuro)

**Resolução:**
Blocker documentado para sprint F9.10+ (containerização completa do stack observabilidade).

---

### EIXO 3: Backup Automation — ✅ COMPLETO

**Artefato:**
- [scripts/backup_observability.sh](../../scripts/backup_observability.sh) (55 linhas)
  - Backup de `techno-os-backend_postgres_data` volume
  - Retenção: 7 dias (`find -mtime +7 -delete`)
  - Symlink `postgres_latest.tar.gz`
  - Fail-closed (`set -euo pipefail`)
  - Executable: `chmod +x`

**Validação:**
```bash
$ ./scripts/backup_observability.sh
# Smoke test: artefato em backups/postgres_YYYYMMDD_HHMMSS.tar.gz ✅
```

**Integração:**
- Documentado em RUNBOOK_OBSERVABILITY.md (seção "Backup/Restore")
- Exemplo cron em README.md (0 2 * * *)

---

### EIXO 4: Documentation — ✅ COMPLETO

**Artefatos:**
- [docs/RUNBOOK_OBSERVABILITY.md](../../docs/RUNBOOK_OBSERVABILITY.md) (352 linhas)
  - Health checks (Backend, PostgreSQL, Prometheus standalone)
  - Métricas LLM (PromQL queries: p50/p95/p99, tokens, errors)
  - Circuit breaker diagnostics (CLOSED/OPEN/HALF_OPEN states)
  - Backup/restore procedures (6 passos, ETA 5-10min)
  - ENV variables (VERITTA_LLM_ALLOWED_PROVIDERS, API keys)
  
- [README.md](../../README.md) (modificado)
  - Status table: F9.9-A, F9.9-B, F9.9-C adicionados
  - Seção "Observability Stack (F9.9-C)":
    - Prometheus standalone (scrape :9090)
    - 3 métricas LLM com exemplos PromQL
    - Circuit breaker states (60s cooldown)
    - Backup automation (cron example)
  - Seção "Variáveis ENV Obrigatórias (F9.9-B/C)"
  - Link para RUNBOOK_OBSERVABILITY.md

---

### EIXO 5: Tests — ✅ COMPLETO

**Artefato:**
- [tests/test_f9_9_c_integration.py](../../tests/test_f9_9_c_integration.py) (223 linhas)
  - 8 testes determinísticos
  - Isolamento: circuit breakers isolados por teste (evita singleton contamination)
  - Cobertura:
    - Circuit breaker: abertura após 3 falhas, bloqueio OPEN, transição HALF_OPEN → CLOSED
    - Retry: 429 rate limit, max 2 retries (3 tentativas total)
    - Timeout: fail-fast (sem retry), Policy.TIMEOUT_S=30.0

**Resultado:**
```
8 passed in 5.93s
```

---

## Critérios de Aceitação

| Critério | Status | Evidência |
|----------|--------|-----------|
| Executor usa retry + circuit breaker | ✅ | [llm_executor_v1.py](../../app/executors/llm_executor_v1.py) L65-77 |
| Timeout de 30s efetivo | ✅ | [policy.py](../../app/llm/policy.py) L15, test_executor_respects_policy_timeout |
| Métricas Prometheus disponíveis | ✅ | [metrics.py](../../app/llm/metrics.py) (F9.9-B) |
| Circuit breaker abre após 3 falhas | ✅ | test_circuit_breaker_opens_after_3_failures |
| Retry max 2 em 429 | ✅ | test_retry_max_2_attempts |
| Timeout sem retry (fail-fast) | ✅ | test_no_retry_on_timeout |
| Backup script operacional | ✅ | [backup_observability.sh](../../scripts/backup_observability.sh) |
| Runbook completo | ✅ | [RUNBOOK_OBSERVABILITY.md](../../docs/RUNBOOK_OBSERVABILITY.md) 352 linhas |
| README atualizado | ✅ | [README.md](../../README.md) seção Observability Stack |
| Prometheus alerting | ❌ | **BLOQUEADO** (prometheus fora docker-compose) |

---

## Evidências

Artefatos em [`artifacts/f9_9_c/`](../../artifacts/f9_9_c/):
- `git_commit_head.txt` - Commit hash HEAD
- `diff_stat_preview.txt` - `git diff --stat` preview
- `test_output.txt` - pytest output (8 passed)
- `backup_smoke.txt` - Backup script smoke test (ls backups/)
- `prometheus_rules_blocker.txt` - Documentação do blocker EIXO 2

---

## Compatibilidade

- ✅ F9.9-A (user preferences): Não afetado
- ✅ F9.9-B (LLM hardening): **Integrado** (retry + circuit breaker agora em uso)
- ✅ F2.1 (X-API-Key): Não afetado
- ✅ F2.3 (Bearer): Não afetado
- ✅ Prometheus standalone: Compatível (sem alertas por enquanto)

---

## Débitos Técnicos

1. **ENV variables para circuit breaker** (F9.10+)
   - Hardcoded constants: `THRESHOLD=3`, `TIMEOUT=60`
   - Plano: `VERITTA_CB_THRESHOLD`, `VERITTA_CB_TIMEOUT`

2. **Containerizar Prometheus + Grafana** (F9.10+)
   - Adicionar serviço `prometheus` em docker-compose.yml
   - Definir alert rules para:
     - LLM latency p95 > 5s
     - Circuit breaker OPEN
     - Error rate > 5%

3. **Backup automation com Grafana** (F9.10+)
   - Uncomment seção grafana em backup_observability.sh
   - Volume: `grafana_data`

---

## Governança V-COF

- ✅ Fail-closed respeitado (backup script `set -e`)
- ✅ Human-in-the-loop (métricas expõem estado, não decidem)
- ✅ Linguagem técnica purificada (runbook sem jargão)
- ✅ Privacy LGPD: Backup apenas PostgreSQL (dados estruturados), sem PII
- ✅ Testes determinísticos (sem flakiness)

---

## Aprovação

**Executor:** GitHub Copilot  
**Revisor:** DEV (next)  
**Tag:** `F9.9-C-SEALED`  
**Branch:** `feature/f9-9-c-integration-observability` → merge to `main`

> IA como instrumento. Humano como centro.

---

## Próximo Sprint

**F9.10 (Proposta):**
- Containerizar Prometheus + Grafana
- Alert rules (latency, circuit breaker, error rate)
- ENV variables para circuit breaker
- Grafana dashboards (LLM metrics, circuit breaker)
- Backup automation completo (postgres + prometheus + grafana)
