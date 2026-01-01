# 🔕 PROCEDIMENTO DE SILENCING — F9.3

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.3 — Alerting Governado  
**Autor**: Copilot Executor  

## Método Autorizado: Via Prometheus API

### Silenciar Alerta Específico
```bash
curl -X POST http://localhost:9090/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "APIDown"},
      {"name": "service", "value": "techno-os-api"}
    ],
    "startsAt": "2026-01-01T00:00:00Z",
    "endsAt": "2026-01-01T01:00:00Z",
    "comment": "Manutenção programada"
  }'
```

### Verificar Silencings Ativos
```bash
curl -s http://localhost:9090/api/v1/silences | jq '.data'
```

### Remover Silencing
```bash
# Obter ID do silencing
SILENCE_ID=$(curl -s http://localhost:9090/api/v1/silences | jq -r '.data[0].id')

# Deletar
curl -X DELETE http://localhost:9090/api/v1/silence/$SILENCE_ID
```

## Duração Típica
- Manutenção: 1-2 horas
- Testes: 30 minutos
- Emergência: Até resolução

## Notas
- Silencing é reversível e auditável via API.
- Não afeta outros alertas.