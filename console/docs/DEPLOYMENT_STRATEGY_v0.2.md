# 🚀 DEPLOYMENT STRATEGY — v0.2

**Objetivo:** Documentar como será realizado o deploy + feature flag para v0.2  
**Data:** 4 janeiro 2026  
**Status:** TEMPLATE PRONTO PARA PREENCHIMENTO

---

## 📍 Contexto

**Base:** docs/CONSOLE_ARCHITECTURE.md (preenchido com contexto real)

Antes de preencer este documento, confirmar:
- [ ] CONSOLE_ARCHITECTURE.md foi preenchido
- [ ] Tipo de console é conhecido (web/CLI/docker)
- [ ] Processo de deploy atual é conhecido

---

## 🎯 Feature Flag System

### Design da Flag

```
Nome da flag: NEXT_PUBLIC_ENABLE_F2_3
  (ou: [ PREENCHER SE DIFERENTE ])

Tipo de flag:
  [ ] Environment variable (env var)
  [ ] Runtime endpoint (GET /api/health?check_f2_3=true)
  [ ] Feature flag service (LaunchDarkly, Unleash, etc.)
  [ ] Custom (descrever):

Default value: FALSE
  (F2.3 desabilitado por padrão, seguro)

Como é lida (em código):
  • Arquivo: [ PREENCHER ]
  • Linha: [ PREENCHER ]
  • Snippet:
    ```
    const isF2_3Enabled = process.env.NEXT_PUBLIC_ENABLE_F2_3 === 'true';
    ```

Cache/TTL (se runtime):
  • TTL: [ 5 min / 1 min / none ]
  • Invalidação: [ manual / automatic ]

Teste de toggle (local):
  1. export NEXT_PUBLIC_ENABLE_F2_3=false
  2. npm run dev
  3. Verificar: F2.3 está desabilitado? [ ]
  4. export NEXT_PUBLIC_ENABLE_F2_3=true
  5. Reload
  6. Verificar: F2.3 está habilitado? [ ]
```

---

## 🏗️ Processo de Deploy Atual

### Build

```
✅ Build command: npm run build
✅ Build time: 11.6s (deterministic, Turbopack)
✅ Output: .next/ (Next.js standalone)
✅ Artifacts:
   • Console image: 342 MB (non-compressed)
   • Compressed: 85.7 MB
   • Alpine multi-stage: Sim (3 stages)
```

### Deploy Target

```
✅ Plataforma: Docker + Docker Compose (confirmado em CONSOLE_ARCHITECTURE)
  ✅ [x] Docker + Docker Compose (local/dev)
  ✅ [x] Docker (production — stack adicional necessária)
  ☐ Kubernetes (futuro)

Deployment Flow (ATUAL):
  1. npm run build → .next/ artifacts
  2. docker build -t console:v0.2 . → 85.7 MB image
  3. docker-compose up -d console → running on port 3000
  4. Health check: GET http://localhost:3000/health
  5. Rollback: docker-compose up -d console:v0.1 (previous tag)

Deploy Time:
  • Build: 11.6s
  • Docker build: ~30s
  • Docker push: ~30s (local) / ~1-2 min (registry)
  • Deployment: ~1 min
  • Total: ~3 min (under 5 min SLA)
```

### Health Check

```
✅ Endpoint: GET /api/health (existente em lib/error-handling.ts)
✅ Response:
   {
     "status": "APPROVED" | "BLOCKED" | "NEUTRAL",
     "ts_utc": "2026-01-04T23:55:00Z",
     "trace_id": "uuid-xxx",
     "f2_3_enabled": true|false  ← NEW in v0.2
   }

✅ Timeout: 5s
✅ Retries: 3
✅ Success: status === "APPROVED" AND f2_3_enabled exists
```

---

## 🎯 Estratégia de Canary

### Fase 1: Canary 1% (Day 1-2)

```
Público alvo: 1% de usuários
Duração: 48 horas

Como fazer:
  Opção A (env var por deployment):
    • Deploy 2 versions: console-v0.1 (99%) + console-v0.2 (1%)
    • Load balancer distribui 1% para v0.2
  
  Opção B (feature flag no código):
    • Deploy única versão (v0.2)
    • Flag NEXT_PUBLIC_ENABLE_F2_3 = false (default)
    • Ativar para 1% via feature flag service

Monitoramento:
  • Error rate: [ baseline ]
  • Response time: [ baseline ]
  • Support tickets: [ monitor ]
  • XSS alerts: [ monitor ]

Success criteria:
  • Error rate < 2%
  • No escalated tickets
  • No security incidents
  • Canary passes? [ ] SIM / [ ] NÃO
  
Failure criteria (ROLLBACK):
  • Error rate > 5% → ROLLBACK IMEDIATAMENTE
  • 3+ escalated tickets → ROLLBACK
  • Security incident → ROLLBACK IMEDIATAMENTE
```

### Fase 2: Expand 10% (Day 3-4, if Phase 1 OK)

```
Público: 10% de usuários
Mesmos critérios de sucesso/falha
```

### Fase 3: Expand 50% (Day 5-6, if Phase 2 OK)

```
Público: 50% de usuários
Mesmos critérios de sucesso/falha
```

### Fase 4: Full Deploy 100% (Day 7, if Phase 3 OK)

```
Público: 100% de usuários
Fim do canary
v0.2 em produção full
```

---

## 🔙 Rollback Procedure

### Estratégia de Rollback

```
Goal: < 5 min from detection to full rollback

Opção A (Revert deploy):
  1. Detectar problema: [ hora ]
  2. Decisão de rollback: [ hora ]
  3. Executar: git revert / docker pull old-version
  4. Redeploy: [ como? ]
  5. Health check: [ OK? ]
  6. Total time: [ ] min

Opção B (Feature flag toggle):
  1. Detectar problema
  2. Set NEXT_PUBLIC_ENABLE_F2_3=false
  3. Deploy (apenas flag, não código)
  4. Health check
  5. Total time: < 2 min

Qual será usado?: [ ESCOLHER A OU B ]
```

### Teste de Rollback (Staging)

```
Procedimento:
  1. Deploy v0.2 em staging
  2. Verificar: F2.3 funciona? [ ]
  3. Executar rollback procedure
  4. Verificar: v0.1 restaurado? [ ]
  5. Time: [ ] min
  6. Status: [ ] PASS / [ ] FAIL

Comprovação:
  • Output do rollback: [ PASTE ]
  • Health check status: [ PASTE ]
  • Time de conclusão: [ ] min
  • Sucesso?: [ ] SIM / [ ] NÃO

Se falho:
  • Root cause: [ ANÁLISE ]
  • Ajuste necessário: [ DESCREVER ]
  • Re-teste: [ AGENDAR ]
```

---

## 📊 Checklist de Prontidão

### Pré-Deploy

- [ ] Feature flag definido e funcionando localmente (on/off)
- [ ] Build compila sem erros (npm run build)
- [ ] Deploy procedure documentado (passos exatos)
- [ ] Rollback procedure documentado (passos exatos)
- [ ] Rollback testado em staging (comprovado < 5 min)
- [ ] Health check endpoint funcional
- [ ] Monitoring/alerts configurado (error rate, tickets, XSS)

### Deploy

- [ ] Feature flag default = FALSE
- [ ] Todos os testes passam (unit/integration/E2E)
- [ ] Security review aprovado
- [ ] Release checklist concluído
- [ ] Team alinhado no procedimento

---

## 🚀 Próxima Ação

1. Preencher template acima com fatos reais
2. Confirmar com DevOps/Platform Engineer
3. Testar rollback em staging (e registrar output)
4. Registrar documento: docs/DEPLOYMENT_STRATEGY_v0.2.md
5. Gate 1.4 marcado como ✅ OK

---

**Deployment Strategy Document**

Criado: 4 janeiro 2026  
Responsável: DevOps / Platform Engineer  
Status: TEMPLATE PRONTO
