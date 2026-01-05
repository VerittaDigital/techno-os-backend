# SEAL F9.9-B — LLM Hardening

**Fase**: F9.9-B  
**Data**: 2025-06-08  
**Branch**: feature/f9-9-b-llm-hardening  
**Commit**: 91efd86  
**Status**: ✅ CONCLUÍDO

---

## OBJETIVO

Endurecer stack LLM com governança V-COF:
- Factory fail-closed com allowlists obrigatórias
- Normalização de respostas (LLMResponse Pydantic)
- Retry automático (429, 5xx) com exponential backoff
- Circuit breaker (3 falhas → 60s cooldown)
- Observabilidade Prometheus (latência, tokens, erros)

---

## EVIDÊNCIAS

### Arquivos Criados (5)
1. `app/llm/errors.py` — Exceções específicas LLM (ConfigurationError, ProviderError, PolicyViolation)
2. `app/llm/response.py` — LLMResponse Pydantic com TokenUsage normalizado
3. `app/llm/retry.py` — Decorator `@with_retry` (max 2 retries, exponential backoff)
4. `app/llm/circuit_breaker.py` — CircuitBreaker class (CLOSED/OPEN/HALF_OPEN)
5. `app/llm/metrics.py` — Métricas Prometheus (3 métricas obrigatórias)

### Arquivos Modificados (3)
1. `app/llm/factory.py` — Fail-closed com VERITTA_LLM_ALLOWED_PROVIDERS, timeout 30s
2. `app/llm/openai_client.py` — LLMResponse + Prometheus instrumentation
3. `tests/test_f9_9_b_llm_hardening.py` — 17 testes (factory, retry, circuit breaker)

**Total**: 8 arquivos, ~620 linhas

---

## CRITÉRIOS DE SUCESSO

### ✅ Factory Fail-Closed
- VERITTA_LLM_ALLOWED_PROVIDERS obrigatória (ConfigurationError se ausente)
- Provider validado contra allowlist (fail-closed)
- API keys obrigatórias (ConfigurationError se ausentes)
- Timeout default alterado de 10s → 30s

### ✅ LLMResponse Normalizado
- Pydantic model com campos: text, model, usage, latency_ms, provider
- TokenUsage breakdown (prompt_tokens, completion_tokens, total_tokens)
- Validação fail-closed: text nunca vazio

### ✅ Retry Automático
- Max 2 retries (3 tentativas totais)
- Exponential backoff: 1s, 2s
- Retry apenas erros temporários (429, 5xx)
- Timeout: fail-fast sem retry
- 4xx (exceto 429): sem retry

### ✅ Circuit Breaker
- Estados: CLOSED, OPEN, HALF_OPEN
- 3 falhas consecutivas → OPEN (60s cooldown)
- OPEN: bloqueia chamadas com CIRCUIT_OPEN error
- HALF_OPEN após cooldown: 1 tentativa de recuperação
- Sucesso em HALF_OPEN → volta para CLOSED
- Thread-safe (threading.Lock)

### ✅ Observabilidade Prometheus
1. **llm_request_latency_seconds** (Histogram)
   - Labels: provider, model
   - Buckets: 0.1s, 0.5s, 1s, 2s, 5s, 10s, 30s
   
2. **llm_tokens_total** (Counter)
   - Labels: provider, model, type (prompt/completion)
   - Incremental acumulativo
   
3. **llm_errors_total** (Counter)
   - Labels: provider, error_type (timeout, provider_error)
   - Incremental acumulativo

### ✅ Testes
- 17 testes passando (pytest)
- Cobertura: factory (6), retry (5), circuit breaker (6)
- Zero regressões em testes existentes

---

## CONFORMIDADE V-COF

### Fail-Closed
- ✅ Factory: ConfigurationError se ENV ausente ou provider bloqueado
- ✅ LLMResponse: Validação Pydantic (text não-vazio)
- ✅ Circuit breaker: Bloqueia chamadas quando open

### Privacy by Design
- ✅ Nenhum log de prompts ou respostas
- ✅ Métricas agregadas (sem PII)
- ✅ Erros normalizados (sem stack trace externo)

### Centralidade Humana
- ✅ Circuit breaker preserva controle (cooldown configurável)
- ✅ Retry automático limitado (max 2)
- ✅ Observabilidade expõe comportamento ao operador

### Governança
- ✅ Allowlist obrigatória (ENV)
- ✅ Timeout endurecido (30s hard max)
- ✅ Retry apenas erros temporários (não 4xx)

---

## COMMITS

```bash
git add -A
git commit -m "feat(F9.9-B): LLM Hardening - factory fail-closed + retry + circuit breaker + metrics"
git push -u origin feature/f9-9-b-llm-hardening
```

---

## PRÓXIMOS PASSOS (F9.9-C)

1. **Integrar retry + circuit breaker no executor**
   - Modificar `llm_executor_v1.py` para usar `@with_retry`
   - Adicionar circuit breaker singleton global
   - Garantir que todas as chamadas LLM passam por resiliência

2. **Atualizar Policy.TIMEOUT_S**
   - `app/llm/policy.py`: alterar de 10.0s → 30.0s
   - Alinhar com factory default

3. **Documentar ENV obrigatórias**
   - Atualizar README com `VERITTA_LLM_ALLOWED_PROVIDERS`
   - Exemplos de configuração por ambiente (dev/prod)

4. **Testes de integração LLM**
   - Smoke test com FakeLLMClient
   - Validar métricas Prometheus no /metrics endpoint
   - Simular circuit breaker open em staging

---

## ASSINATURAS

**Arquiteto**: _[aprovação pendente]_  
**Implementador**: GitHub Copilot  
**Revisor**: _[código review pendente]_  

---

**FASE F9.9-B SELADA** ✅
