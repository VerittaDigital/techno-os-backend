# ✅ CHECKLIST F9.2 — VALIDAÇÃO AUTH & ACCESS CONTROL

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.2 — Auth & Access Control  
**Autor**: Copilot Executor  

## Validações Obrigatórias

### 1. Grafana — Login Obrigatório
```bash
# Tentar acesso sem login (deve redirecionar para login)
curl -I https://staging.techno-os.com/grafana/
# Esperado: 302 Found (redirect to login)
```

### 2. API — /health Público
```bash
# Health deve ser acessível sem auth
curl -I https://staging.techno-os.com/health
# Esperado: 200 OK
```

### 3. API — /metrics Acessível para Prometheus
```bash
# Metrics acessível (simulando Prometheus IP)
curl -I https://staging.techno-os.com/metrics
# Esperado: 200 OK (se IP allowed)
```

### 4. API — Endpoints Protegidos Exigem Auth
```bash
# Acesso sem auth deve falhar
curl -I https://staging.techno-os.com/
# Esperado: 401 Unauthorized

# Com auth deve liberar
curl -I -u <STAGING_USER>:<STAGING_PASS> https://staging.techno-os.com/
# Esperado: 200 OK ou 3xx
```

### 5. Prometheus Scrape Continua UP
```bash
# Verificar targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[0].health'
# Esperado: "up"
```

### 6. Grafana Datasource Funcional
```bash
# Após login, verificar datasource (via API se possível)
# Manual: Acessar UI e verificar dashboards carregam
```

## Status
- [ ] Todas validações PASS
- [ ] Rollback testado

**Critério**: Checklist 100% completo para declarar F9.2 concluída.