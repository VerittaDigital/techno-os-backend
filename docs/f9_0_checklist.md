# 📋 CHECKLIST F9 — PRODUCTION READINESS (STAGING)

**Data**: 2026-01-01  
**Versão**: v1.0  
**Fase**: F9.0 — Gate de Governança  
**Autor**: Copilot Executor (Hermes Spectrum)  
**Referência Runbook**: scripts/f8_8_obs_contract.sh (F8.8 CI-friendly)  

## 1. Infraestrutura (Responsável: DevOps)
- [ ] Docker Compose staging funcional (backend + observabilidade)
- [ ] External networks configuradas (techno_observability)
- [ ] Volumes efêmeros para testes (sem persistência)
- [ ] Health checks automáticos (/health endpoint)

## 2. Segurança (Responsável: Security)
- [ ] API keys validadas (fail-closed)
- [ ] Rate limiting ativo (100 req/min default)
- [ ] Audit logs append-only (JSONL)
- [ ] Sem secrets em plaintext (exceto .env controlado)

## 3. Observabilidade (Responsável: Observabilidade)
- [ ] Prometheus scrape ativo (5s interval)
- [ ] Grafana dashboards provisionados (5 painéis)
- [ ] Alerting rules carregadas (3 regras F8.5)
- [ ] Runbook F8.8 executável (SEAL OK em staging)

## 4. Rollback (Responsável: DevOps)
- [ ] Git commits limpos (working tree clean)
- [ ] Backups timestamped disponíveis
- [ ] Recovery procedures documentadas (ex.: F8.6.1)
- [ ] Fail-closed traps ativos

## Validação
Checklist 100% completo: Todos itens marcados como [x].  
Peer review: Aprovado por equipe técnica.