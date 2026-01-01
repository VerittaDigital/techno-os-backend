# 🔄 PROCEDIMENTO DE ROLLBACK F9.1

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.1 — TLS / HTTPS  
**Autor**: Copilot Executor  

## Objetivo
Retornar o sistema ao estado pré-F9.1 em caso de falha ou necessidade de reversão.

## Passos Automáticos (Script Recomendado)
```bash
./scripts/rollback_f9_1.sh
```

## Passos Manuais (Fallback)
1. **Parar Nginx**:
   ```bash
   docker-compose -f docker-compose.nginx.yml down
   ```

2. **Remover Volume Let's Encrypt**:
   ```bash
   docker volume rm techno-os-backend_letsencrypt
   ```

3. **Restaurar nginx.conf**:
   ```bash
   git checkout HEAD~1 -- nginx/nginx.conf
   ```

4. **Limpar Certs do Host**:
   ```bash
   sudo rm -rf /etc/letsencrypt/live/staging.techno-os.com/
   ```

## Validação Pós-Rollback
- [ ] HTTPS desativado
- [ ] HTTP funciona diretamente (porta 80)
- [ ] Backend acessível via localhost:8000
- [ ] Observabilidade intacta (F8.8)

## Notas
- Rollback é reversível: F9.1 pode ser re-executada após correções.
- Backup: Volume letsencrypt é removido; recriar certs se necessário.