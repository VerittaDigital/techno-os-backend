# 📊 REGISTRO DE DIFF — F9.2 (Antes vs. Depois)

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.2 — Auth & Access Control  
**Autor**: Copilot Executor  

## Estado Antes (Pós-F9.1)
- **Grafana**: Anonymous access enabled (F8.4 config)
- **Nginx**: Sem auth em API routes, /metrics deny all
- **Segurança**: HTTPS ativo, mas acesso aberto

## Estado Depois (Pós-F9.2)
- **Grafana**: Anonymous disabled, login obrigatório via GF_SECURITY_ADMIN_USER/PASSWORD
- **Nginx**: Basic Auth em / (exceto /health, /metrics), /metrics allow Docker networks
- **Segurança**: Controle de acesso ativo, superfície protegida

## Arquivos Modificados
- `docker-compose.grafana.yml`: Adicionado GF_AUTH_ANONYMOUS_ENABLED=false
- `nginx/nginx.conf`: Adicionado auth_basic em location /, allow em /metrics
- `docker-compose.nginx.yml`: Adicionado volume para .htpasswd

## Arquivos Criados
- `nginx/.htpasswd`: Credenciais Basic Auth (staging:temp123)
- `docs/f9_2_checklist.md`
- `scripts/rollback_f9_2.sh`

## Validação
Diff auditado: Mudanças limitadas a hardening, sem quebra de F8.8.