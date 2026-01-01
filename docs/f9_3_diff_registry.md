# 📊 REGISTRO DE DIFF — F9.3 (Antes vs. Depois)

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.3 — Alerting Governado  
**Autor**: Copilot Executor  

## Estado Antes (Pós-F9.2)
- **Alert Rules**: Apenas F8.5 (BackendDown, HighLatencyP95, HighRequestVolume)
- **Alerting**: Básico, sem detecção de scrape failing
- **Database**: Sem alerta (SQLite sem métrica)

## Estado Depois (Pós-F9.3)
- **Alert Rules**: Adicionados APIDown e PrometheusScrapeFailing (F9.3)
- **Alerting**: Governado, mínimo, acionável (2 alertas críticos)
- **Database**: Alerta não implementado (limitação técnica declarada)

## Arquivos Modificados
- `alert.rules.yml`: Adicionadas 2 novas rules com comentários e labels

## Arquivos Criados
- `docs/f9_3_checklist.md`
- `docs/f9_3_silencing.md`
- `scripts/rollback_f9_3.sh`

## Validação
Diff auditado: Alerting mínimo adicionado sem quebrar F8.5.