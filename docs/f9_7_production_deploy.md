# F9.7 Production Deploy — Controlled Production Deployment

**Data:** 2026-01-02  
**Fase:** F9.7 — Controlled Production Deployment  
**Objetivo:** Deploy controlado em produção com TLS, secrets e human-in-the-loop.

## Fase 2: Backup e Preparação

### Backup Executado
- Código: `git archive --format=tar.gz -o backup_f9_7_pre_deploy.tar.gz HEAD`
- Timestamp: 2026-01-02

### Secrets Gerados
- VERITTA_BETA_API_KEY: e65f9b01ce2fb0a41ffaea218d0c2d51123b8c8f7e565b33f28a537ec5b2fa78
- VERITTA_ADMIN_API_KEY: 1980ac82811b6ead894ccfa695a36c204813eedc6fbc27d4946fc6cf1389c79c
- VERITTA_PROFILES_FINGERPRINT: f92d5263e1dbe67375a7ade4210877d4f38a2bcf5b3f312039b60904e25e2299

### .env.prod Configurado
- Arquivo: .env.prod criado com secrets
- Audit log: /var/log/veritta/audit.log

## Próximos Passos
1. Configurar PostgreSQL no VPS
2. Transferir código e .env.prod via SCP
3. Configurar Nginx e Certbot para TLS
4. Executar docker-compose up -d
5. Validar com smoke tests

## Validação
- [ ] Secrets gerados e armazenados seguramente
- [ ] Backup criado
- [ ] .env.prod pronto para deploy