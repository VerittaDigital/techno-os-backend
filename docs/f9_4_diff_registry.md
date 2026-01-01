# 📊 REGISTRO DE DIFF — F9.4 (Antes vs. Depois)

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.4 — Smoke & Contract Tests  
**Autor**: Copilot Executor  

## Estado Antes (Pós-F9.3)
- **Testes**: Validações manuais, sem scripts CI-friendly
- **Contratos**: Não validados automaticamente
- **Evidence**: Logs manuais, sem estrutura

## Estado Depois (Pós-F9.4)
- **Testes**: Scripts bash fail-closed, CI-friendly (smoke_https.sh, contract_obs.sh, contract_sec.sh)
- **Contratos**: Validados automaticamente (F8/F9 contracts)
- **Evidence**: Logs timestamped, exit codes, auditáveis

## Arquivos Criados
- `scripts/smoke_https.sh`: Smoke tests HTTPS e auth
- `scripts/contract_obs.sh`: Contract tests observabilidade
- `scripts/contract_sec.sh`: Contract tests segurança
- `docs/f9_4_checklist.md`: Mapeamento teste → requisito
- `docs/f9_4_rollback.md`: Procedimento de rollback (reporte)

## Validação
Diff auditado: Testes adicionados sem alterar funcionalidade.