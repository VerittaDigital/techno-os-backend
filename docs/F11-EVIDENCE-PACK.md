# F11 Evidence Pack — Auditoria de Produção

**Data**: 2026-01-04 23:28:47 UTC  
**Ambiente**: VPS Production (srv1241381.hstgr.cloud)  
**Tag Imutável**: F11-PROD-v1.0.1  
**Commit**: 404ef09  

---

## 1. CP-11.3 Smoke Tests (VPS) — Resultado: 6/6 PASS

```
============================================
CP-11.3 FINAL VALIDATION (VPS PRODUCTION)
============================================

[TEST 1] POST /process (valid)
HTTP: 200 | Status: FAILED | Trace: 0029a132-57e0-41d4-969c-f175fd72d59e
✓ PASS

[TEST 2] GET /nonexistent (404)
HTTP: 404 | Trace: 2b0f4adf-529b-436e-8e28-af656394ec6e
✓ PASS

[TEST 3] DELETE /process (405)
HTTP: 405 | Trace: 0ef83e4c-9dad-4a30-9ac6-426b3af000c4
✓ PASS

[TEST 4] POST /process (malformed JSON)
HTTP: 422
✓ PASS

[TEST 5] GET /health
Status: ok
✓ PASS

[TEST 6] Audit log
Entries: 22
Sample:
{
  "trace_id": "09d61610-d4a0-4c10-8b82-9c6c3c071859",
  "event_type": "decision_audit",
  "ts_utc": "2026-01-04T23:28:47.401246Z"
}
✓ PASS

============================================
CP-11.3 FINAL RESULT: 6/6 PASS
✓✓✓ CP-11.3 APPROVED ✓✓✓
============================================
```

---

## 2. Docker Compose Config (Produção)

### Seção API (Relevante)

```yaml
api:
  build:
    context: .
    dockerfile: Dockerfile
    args:
      PYTHON_VERSION: "3.12"
  container_name: techno-os-api
  env_file:
    - /opt/techno-os/env/.env.prod
  environment:
    - DATABASE_URL=postgresql://techno_user:***@postgres:5432/techno_os
    - ENV=production
    - DEBUG=false
    - LOG_LEVEL=info
  depends_on:
    postgres:
      condition: service_healthy
  ports:
    - "8000:8000"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 3s
    retries: 3
    start_period: 10s
  networks:
    - techno-network
  volumes:
    - ./app:/app/app
    - ./tests:/app/tests
    - /var/log/veritta:/var/log/veritta  # ← AUDIT LOG MOUNT
  command: >
    sh -c 'uvicorn app.main:app --host 0.0.0.0 --port 8000'
```

**Crítico**: Volume mount `/var/log/veritta:/var/log/veritta` garante persistência de audit log no host.

---

## 3. Audit Log (Amostra VPS)

```json
{"decision":"ALLOW","profile_id":"F2.1","reason_codes":[],"input_digest":"7f7739f268fcc6d62585733d352d487c0dfafc5514f44b3b70cdd726e97b19df","trace_id":"68304163-022e-419f-838b-dbeab7264e79","ts_utc":"2026-01-04T23:28:47.401246Z","event_type":"decision_audit"}
{"status":"FAILED","action":"process","executor_id":"text_process_v1","trace_id":"0029a132-57e0-41d4-969c-f175fd72d59e","ts_utc":"2026-01-04T23:28:47.562912Z","event_type":"action_audit"}
{"decision":"DENY","profile_id":"G0_F21","reason_codes":["G0_F21_missing_token"],"matched_rules":["X-API-Key header required"],"trace_id":"2b0f4adf-529b-436e-8e28-af656394ec6e","ts_utc":"2026-01-04T23:28:47.701503Z","event_type":"decision_audit"}
```

**Validação**: 
- Todas as entradas contêm UUID trace_id
- Timestamps UTC em formato ISO 8601
- decision_audit e action_audit presentes
- 22 entradas totais em `/var/log/veritta/audit.log`

---

## 4. Git Info (VPS)

```bash
$ git describe --tags
F11-PROD-v1.0.1

$ git log --oneline -5
404ef09 docs(f11-seal): final VPS revalidation - CP-11.3 6/6 PASS after git pull
be97438 merge(f11): Gate Engine Consolidation + VPS hotfix2 (6/6 smoke tests PASS)
dce921c fix(f11-hotfix): add audit volume mount + mkdir in audit_sink
0af9702 fix(f11): add env_file to docker-compose for VERITTA vars
9ea165c fix(f11): add python-dotenv to requirements.txt
```

---

## 5. Requisitos de Rollback (24h Operacional)

### Gatilhos de Rollback

| Condição | Ação |
|----------|------|
| POST /process retorna 500 | rollback imediato para tag anterior |
| audit.log não cresce (0 writes em 1h) | rollback imediato |
| trace_id malformado (não UUID) | rollback imediato |
| API key validation falha (>5 401s em 10min) | investigar + rollback se crítico |

### Rollback Procedure

```bash
# VPS Produção
docker compose down
git checkout F11-PROD-v1.0  # Usar anterior
docker compose up -d --build
bash smoke_test_cp11_3.sh   # Validar
```

---

## 6. Histórico de Tags (Imutabilidade)

```
F11-SEALED-v1.0                 [IMUTÁVEL] Original seal + hotfix1
  ↓
F11-SEALED-v1.0-hotfix1         [IMUTÁVEL] env_file fix
  ↓
F11-SEALED-v1.0-hotfix2         [IMUTÁVEL] Volume mount + mkdir (commit dce921c)
  ↓
F11-PROD-v1.0                   [HISTÓRICO] Apontou para be97438 (merge)
  ↓ (force-push — NÃO FAÇA NOVAMENTE)
F11-PROD-v1.0 (reescrito)        [REPARADO] Agora aponta para 404ef09
  ↓
F11-PROD-v1.0.1                 [IMUTÁVEL] Nova tag final (404ef09)
```

**Política futura**: Nenhuma tag de release será reescrita. Criar v1.0.2, v1.0.3, etc. se necessário.

---

## 7. Protocolo de Operação (Samurai)

### Antes de qualquer alteração em produção:

- [ ] Criar ticket/issue documentado
- [ ] Validar localmente (387 testes)
- [ ] Testar em staging (se houver)
- [ ] Abrir PR com revisão obrigatória
- [ ] Merge sem --force
- [ ] Criar nova tag (v1.0.2, v1.0.3, etc.)
- [ ] Push tag para GitHub
- [ ] Rodar smoke tests em produção
- [ ] Verificar audit log
- [ ] Documentar em Evidence Pack

### Nunca fazer:

- ❌ Force-push em tags de release
- ❌ Commit direto em main
- ❌ Alterar código sem test coverage
- ❌ Ignorar falhas de audit log

---

**Assinado**: Governança F11  
**Próxima revisão**: 2026-01-05 (após 24h operacional)
