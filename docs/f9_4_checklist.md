# ✅ CHECKLIST F9.4 — SMOKE & CONTRACT TESTS

**Data**: 2026-01-01  
**Versão**: v1.1 (hotfix BASE_URL)  
**Fase**: F9.4 — Smoke & Contract Tests  
**Autor**: Copilot Executor  

## Precondições (Hotfix v1.1)
- [x] **BASE_URL parametrizável**: Scripts suportam `BASE_URL=https://localhost` para testes locais
- [x] **Precheck conectividade**: Todos scripts verificam `$BASE_URL/health` antes de executar
- [x] **Fail-fast**: Precondition failed aborta execução com exit 1
- [x] **Default staging**: `BASE_URL` default para `https://staging.techno-os.com` se não definido

## Mapeamento Teste → Requisito

### Smoke Tests (scripts/smoke_https.sh)
- [x] **Teste 1: /health → 200 OK via HTTPS** → Contrato F8: health endpoint público
- [x] **Teste 2: Endpoint raiz sem auth → 401/403** → Contrato F9.2: auth obrigatório
- [x] **Teste 3: Endpoint raiz com auth → 200/3xx** → Contrato F9.2: auth funcional
- [x] **Teste 4: Grafana requer login** → Contrato F9.2: anonymous OFF

### Contract Tests Observabilidade (scripts/contract_obs.sh)
- [x] **Teste 1: Prometheus targets UP** → Contrato F8.3: scrape ativo
- [x] **Teste 2: Rules carregadas sem erro** → Contrato F9.3: alerting governado
- [x] **Teste 3: Alerting rules presentes** → Contrato F9.3: mínimo 5 rules
- [x] **Teste 4: Grafana datasource** → Contrato F8.4: datasource funcional

### Contract Tests Segurança (scripts/contract_sec.sh)
- [x] **Teste 1: HTTP redireciona HTTPS** → Contrato F9.1: HTTPS obrigatório
- [x] **Teste 2: Backend via proxy** → Contrato F9.1: acesso controlado
- [x] **Teste 3: /metrics acesso controlado** → Contrato F9.2: allowlist Docker
- [x] **Teste 4: Endpoints protegidos** → Contrato F9.2: auth em superfícies

## Execução CI-Friendly
```bash
# Definir env vars
export API_USER=staging
export API_PASS=temp123
export BASE_URL=https://localhost  # Para testes locais

# Executar todos
./scripts/smoke_https.sh
./scripts/contract_obs.sh
./scripts/contract_sec.sh
```

## Critérios de Sucesso
- [x] Todos testes PASS (exit code 0)
- [x] Nenhum teste ignorado
- [x] Logs salvos com timestamps
- [x] Reproduzível em CI (GitHub Actions)

**Status**: ✅ F9.4 CONCLUÍDA - Todos testes PASS em ambiente local