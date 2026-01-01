# ✅ CHECKLIST F9.3 — ALERTING GOVERNADO

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.3 — Alerting Governado  
**Autor**: Copilot Executor  

## Validações Obrigatórias

### 1. Alert Rules Carregadas
```bash
# Verificar se rules carregam sem erro
curl -s http://localhost:9090/api/v1/rules | jq '.status'
# Esperado: "success"
```

### 2. Nenhum Alerta em Estado Saudável
```bash
# Verificar alertas ativos
curl -s http://localhost:9090/api/v1/alerts | jq '.data | length'
# Esperado: 0 (nenhum alerta firing)
```

### 3. Teste de Firing — API DOWN
```bash
# Simular falha: parar API
docker-compose stop techno-os-api
sleep 65  # > 60s

# Verificar firing
curl -s http://localhost:9090/api/v1/alerts | jq '.data[] | select(.labels.alertname == "APIDown") | .state'
# Esperado: "firing"

# Recovery: subir API
docker-compose start techno-os-api
sleep 10

# Verificar resolved
curl -s http://localhost:9090/api/v1/alerts | jq '.data | length'
# Esperado: 0
```

### 4. Teste de Firing — Scrape Failing
```bash
# Simular: parar Grafana (target essencial)
docker-compose stop grafana
sleep 65

# Verificar firing
curl -s http://localhost:9090/api/v1/alerts | jq '.data[] | select(.labels.alertname == "PrometheusScrapeFailing") | .state'
# Esperado: "firing"

# Recovery
docker-compose start grafana
sleep 10
# Verificar resolved
```

### 5. Silencing Funciona
```bash
# Silenciar via API (exemplo)
curl -X POST http://localhost:9090/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [{"name": "alertname", "value": "APIDown"}],
    "startsAt": "2026-01-01T00:00:00Z",
    "endsAt": "2026-01-01T01:00:00Z",
    "comment": "Test silencing"
  }'
# Verificar silencing ativo
```

## Declaração Database DOWN
Database DOWN alert **NÃO IMPLEMENTADO** por limitação técnica: SQLite sem exporter ou métrica de disponibilidade confiável.

## Status
- [ ] Todas validações PASS
- [ ] Rollback testado

**Critério**: Checklist 100% completo para declarar F9.3 concluída.