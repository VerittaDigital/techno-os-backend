# ✅ CHECKLIST DE VALIDAÇÃO HTTPS — F9.1

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.1 — TLS / HTTPS  
**Autor**: Copilot Executor  

## Validações Obrigatórias

### 1. HTTPS Ativo e Válido
```bash
# Verificar certificado Let's Encrypt
curl -I https://staging.techno-os.com/health
# Esperado: HTTP/2 200, certificado válido (não self-signed)
```

### 2. HTTP Redireciona para HTTPS
```bash
# Testar redirect
curl -I http://staging.techno-os.com/health
# Esperado: HTTP/1.1 301 Moved Permanently, Location: https://...
```

### 3. Backend Inacessível Diretamente
```bash
# Tentar acesso direto (deve falhar)
curl http://localhost:8000/health
# Esperado: Connection refused ou timeout
```

### 4. Grafana Acessível via HTTPS
```bash
# Verificar Grafana atrás do proxy
curl -I https://staging.techno-os.com/grafana/
# Esperado: HTTP/2 200 (ou redirect para login)
```

### 5. Prometheus Targets Continuam UP
```bash
# Verificar scrape
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[0].health'
# Esperado: "up"
```

### 6. Renovação de Certificados
```bash
# Simular renovação (dry-run)
certbot renew --dry-run
# Esperado: Sucesso sem erros
```

## Status
- [ ] Todas validações PASS
- [ ] Rollback testado com sucesso

**Critério**: Checklist 100% completo para declarar F9.1 concluída.