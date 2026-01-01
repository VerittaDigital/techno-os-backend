# 🔄 PROCEDIMENTO DE ROLLBACK F9.4

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.4 — Smoke & Contract Tests  
**Autor**: Copilot Executor  

## Rollback F9.4: Nenhuma Ação Técnica

Como F9.4 é fase de **prova e validação**, não há alterações funcionais a reverter.

### Se Testes Passarem
- Prosseguir para F9.5.

### Se Testes Falharem
- **ABORTAR F9.4** imediatamente.
- **REPORTAR falha** com evidence completa (logs dos scripts).
- **RETORNAR para F9.3** para investigação (não corrigir em F9.4).
- Nenhuma alteração de código ou config.

### Evidence Collection em Falha
```bash
# Coletar logs
find . -name "*.log" -newer scripts/smoke_https.sh | tar -czf evidence_f9_4_$(date +%Y%m%d_%H%M%S).tar.gz -
```

### Notas
- Rollback é conceptual: reporte e abort.
- Scripts permanecem para re-execução futura.