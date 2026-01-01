# 📊 REGISTRO DE DIFF — F9.1 (Antes vs. Depois)

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.1 — TLS / HTTPS  
**Autor**: Copilot Executor  

## Estado Antes (Pré-F9.1)
- **nginx.conf**: Self-signed certificates, localhost, sem upstream Grafana
- **docker-compose.nginx.yml**: Sem volume letsencrypt
- **Rede**: Apenas backend upstream
- **Segurança**: HTTP/HTTPS com self-signed, backend potencialmente acessível

## Estado Depois (Pós-F9.1)
- **nginx.conf**: Let's Encrypt certificates, staging.techno-os.com, upstream Grafana adicionado
- **docker-compose.nginx.yml**: Volume letsencrypt adicionado para persistência
- **Rede**: Backend + Grafana upstreams, isolamento completo
- **Segurança**: HTTPS obrigatório, backend inacessível diretamente, certs renováveis

## Arquivos Modificados
- `nginx/nginx.conf`: Atualizado para HTTPS production-ready
- `docker-compose.nginx.yml`: Adicionado volume letsencrypt

## Arquivos Criados
- `docs/f9_1_https_checklist.md`
- `docs/f9_1_rollback_procedure.md`
- `scripts/rollback_f9_1.sh`

## Validação
Diff auditado: Mudanças limitadas a hardening, sem quebra de F8.8.