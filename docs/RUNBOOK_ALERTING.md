# RUNBOOK ALERTING — Techno OS (F9.11)

## O que é o alerta

Sistema de alertas do Techno OS operando via Prometheus + Alertmanager + Grafana (stack containerizado F9.10).

Alertas ativos monitoram:
- **LLM health** (latência, erros, timeout)
- **API health** (disponibilidade, response time)
- **Containers** (Prometheus, Alertmanager, Grafana)

Governança: **Human-in-the-loop** (alertas NÃO acionam auto-remediação).

## Causas prováveis

### LLM_HIGH_LATENCY
- Provider externo lento (OpenAI, Anthropic timeout)
- Rede congestionada
- Rate limiting ativo
- Payload muito grande

### LLM_HIGH_ERROR_RATE
- API key inválida/expirada
- Quota excedida
- Formato de request incorreto
- Provider indisponível

### ApiUnhealthy
- Container techno-os-api crashado
- Database connection lost
- Memory/CPU exhausted
- Dependency failure (postgres)

## Ações recomendadas

### Passo 1: Confirmar alerta no Grafana
- Acesse: http://72.61.219.157:3000
- Dashboard: LLM Metrics F9.10
- Valide timestamps e métricas

### Passo 2: Verificar logs da API
```bash
ssh veritta-vps
docker logs techno-os-api --tail 100
```

### Passo 3: Verificar containers
```bash
docker ps | grep techno-os
docker stats --no-stream
```

### Passo 4: Verificar métricas diretamente
```bash
curl http://localhost:9090/api/v1/query?query=up
curl http://localhost:9090/api/v1/alerts
```

### Passo 5: Se necessário, restart controlado
```bash
# Apenas se API unhealthy confirmado
docker restart techno-os-api
# Aguardar 30s, validar: docker logs techno-os-api
```

## O que NÃO fazer

❌ **NÃO** executar restart sem validar causa raiz  
❌ **NÃO** alterar configuração de containers em runtime  
❌ **NÃO** modificar alert rules sem SEAL  
❌ **NÃO** desabilitar alertas sem documentação  
❌ **NÃO** executar comandos destrutivos (rm, kill -9) sem backup  
❌ **NÃO** expor credenciais em logs ou comandos  

## Quando escalar

### Escalar IMEDIATAMENTE se:
- ✅ Múltiplos containers down simultaneamente
- ✅ Database corrompido ou inacessível
- ✅ Perda de dados detectada
- ✅ Violação de segurança suspeita
- ✅ Falha persiste após 2 tentativas de correção

### Responsável: DevOps Lead
- Slack: #techno-os-alerts
- Email: ops@verittadigital.com
- On-call: verificar planilha de escala

### Evidências necessárias para escalação:
- Screenshots do Grafana
- Logs relevantes (últimas 200 linhas)
- Output de `docker ps` e `docker stats`
- Comandos executados e resultados
