# 🔙 ROLLBACK PROCEDURE — v0.2

**Objetivo:** Procedimento passo-a-passo para reverter v0.2 em caso de problema  
**Data:** 4 janeiro 2026  
**Status:** TEMPLATE PRONTO PARA PREENCHIMENTO

---

## 🎯 Critérios de Ativação de Rollback

### Rollback IMEDIATO (< 5 min decisão)

```
Qualquer um destes dispara rollback:

❌ CRITÉRIO 1: F2.3 error rate > 5%
   • Detecta: automaticamente via alerts OU manualmente via dashboard
   • Ação: ROLLBACK IMEDIATO
   
❌ CRITÉRIO 2: Security incident (XSS, token theft, etc.)
   • Detecta: CSP violation alert OU security team
   • Ação: ROLLBACK IMEDIATO
   
❌ CRITÉRIO 3: 3+ escalated support tickets
   • Detecta: support team escalation
   • Ação: ROLLBACK IMEDIATO
   
❌ CRITÉRIO 4: Service unavailable (5xx errors)
   • Detecta: uptime monitoring
   • Ação: ROLLBACK IMEDIATO
```

### Rollback CONSIDERADO (discussão)

```
⚠️ Error rate 2-5%
  → Discutir com team
  → Decidir: continue ou rollback?
  
⚠️ Performance degradação (latência +50%)
  → Investigar raiz
  → Decidir: continue ou rollback?
```

---

## 🔄 Procedimento de Rollback

### OPÇÃO A: Revert Deploy

#### Pré-requisitos
```
- [ ] Git history acessível
- [ ] Versão anterior em produção conhecida (tag/commit)
- [ ] Build da versão anterior testado anteriormente
```

#### Passos

```
PASSO 1: Confirmar Rollback (CEO/Tech Lead)
  ✅ Time: 1 min
  ✅ Comando de confirmação: "OK, ROLLBACK AGORA"
  ✅ Pessoa responsável: DevOps Lead (ativa procedure)

PASSO 2: Preparar Rollback
  ✅ Time: 2 min
  ✅ Commits a reverter: (Git não usado em Docker — revert to tag anterior)
    • v0.1 image tag: console:0.1.0 (latest stable in registry)
    • v0.2 image tag: console:0.2.0 (current — bad)
  ✅ Comando (Docker):
    docker pull console:0.1.0  # fetch from registry
    docker-compose down
    # Edit docker-compose.yml: image: console:0.1.0
    docker-compose up -d console

PASSO 3: Build Versão Anterior (se necessário)
  ☐ Time: 30-60 sec (npm run build)
  ☐ Nota: Não necessário se v0.1 image já está em registry
  ☐ Fallback: npm run build && docker build -t console:0.1.0-verify .

PASSO 4: Deploy Versão Anterior
  ✅ Time: 1-2 min (Docker compose + startup)
  ✅ Plataforma: Docker + Docker Compose (confirmado)
  
  Procedimento REAL:
    1. docker-compose pull console:0.1.0
    2. docker-compose down console
    3. sed -i 's/console:0.2.0/console:0.1.0/g' docker-compose.yml
    4. docker-compose up -d console
    5. sleep 30 && docker logs console | tail -50
    6. curl http://localhost:3000/api/health

PASSO 5: Health Check
  ✅ Time: 30 sec
  • Endpoint: [ PREENCHER ]
    GET /api/health
  • Resposta esperada:
    {
      "status": "ok",
      "f2_3_enabled": false
    }
  • Resultado: [ ] PASS / [ ] FAIL
  • Se FAIL: → ESCALAR (não é simples)

PASSO 6: Notificação
  • Time: 5 min
  • Notificar: [ LISTAR STAKEHOLDERS ]
    • Product Manager
    • Engineering Lead
    • Support Team
    • Customers (se aplicável)
  • Template:
    "F2.3 has been temporarily disabled due to [REASON].
     We are investigating and will re-enable when ready.
     Timeline: within 24 hours."

TOTAL TIME: 5-10 min (meta: < 5 min)
```

---

### OPÇÃO B: Feature Flag Toggle (Mais Rápido)

#### Pré-requisitos
```
- [ ] Feature flag system em produção (env var ou feature flag service)
- [ ] Procedimento de toggle documentado
```

#### Passos

```
PASSO 1: Confirmar Rollback (Tech Lead / On-call)
  • Time: 1 min
  • Decisão: SIM/NÃO

PASSO 2: Desabilitar F2.3
  • Time: 1 min
  • Comando (se env var):
    heroku config:set NEXT_PUBLIC_ENABLE_F2_3=false
    ou
    export NEXT_PUBLIC_ENABLE_F2_3=false && redeploy
    
  • Ou (se feature flag service):
    Vercel Dashboard → Environment Variables
    Vercel CLI → vercel env add NEXT_PUBLIC_ENABLE_F2_3 false --prod
    
  • Ou (se runtime endpoint):
    PATCH /admin/feature-flags/f2_3_enabled false

PASSO 3: Reload/Deploy
  • Time: 30-60 sec
  • Se lazy-loaded: apenas reload (browser)
  • Se build-time: rebuild + deploy (1-2 min)
  • Comando: [ PREENCHER ]

PASSO 4: Health Check
  • Time: 30 sec
  • Endpoint: [ PREENCHER ]
  • Verificar: F2.3 desabilitado? [ ]
  • Resultado: [ ] PASS / [ ] FAIL

PASSO 5: Notificação
  • Time: 5 min
  • Notificar stakeholders
  • Template (same as Option A)

TOTAL TIME: 3-5 min (meta: < 5 min)
```

---

### OPÇÃO C: Database/State Rollback (Se Aplicável)

```
Se rollback envolve dados migrados:

PASSO 1: Backup check (pré-requisito)
  • Backup da state anterior existe? [ ]
  • Backup testado anteriormente? [ ]

PASSO 2: Restore
  • Comando: [ PREENCHER ]
  • Time: [ ] min
  
PASSO 3: Verification
  • Data antes/depois do rollback: [ ]
  • Inconsistências? [ ]
```

---

## 📋 Qual Opção Usar?

```
Se problema = código deficiente:
  → Use OPÇÃO B (Feature Flag Toggle) — mais rápido

Se problema = infraestrutura/deploy:
  → Use OPÇÃO A (Revert Deploy) — mais confiável

Se problema = data corruption:
  → Use OPÇÃO C — mais cuidadoso (pode levar 1h)

Recomendação padrão:
  → OPÇÃO B (< 5 min) + OPÇÃO A em standby
```

---

## 🧪 Teste de Rollback

### Setup Staging

```
Ambiente: staging (igual a produção)
Deploy v0.2 (com OAuth2 + F2.3): [ ]
Verificar: funciona? [ ]
```

### Executar Rollback

```
Escolher OPÇÃO (A ou B): [ ESCOLHER ]
Executar passos do procedimento
Registrar tempo por passo: [ TEMPOS ]
Resultado final: [ ] PASS / [ ] FAIL
```

### Documentação do Teste

```
Quando testado: [ DATA/HORA ]
Por quem: [ NOME ]
Opção testada: [ A / B / C ]
Tempo total: [ ] min
Comandos exatos usados:
  [ PASTE AQUI ]
Output de sucesso:
  [ PASTE AQUI ]
Problemas encontrados:
  [ LISTAR ]
Ajustes necessários:
  [ DESCREVER ]
```

---

## 🚨 Escalação

### Se Rollback Falhar

```
PASSO 1: STOP (não piore)
  • Parar de tentar rollback
  • Isolar o sistema (se possível)

PASSO 2: Escalar
  • Contactar: [ ON-CALL ENGINEER ]
  • Contactar: [ ARQUITETO ]
  • Contactar: [ CTO / VP ENGINEERING ]

PASSO 3: Análise
  • Qual é o real problema? [ ]
  • Por que rollback falhou? [ ]
  • Qual é o plano B? [ ]

PASSO 4: Decisão
  • Tentar novamente (com ajuste)?
  • Manter v0.2 desabilitado (não rollback)?
  • Redeploy versão intermediária?
```

---

## 📊 Checklist Pré-Rollback

Antes de fazer rollback em produção:

- [ ] Critério de rollback foi acionado? (error rate > 5% ou security incident)
- [ ] Decisão confirmada por Tech Lead / On-call
- [ ] Procedimento (A/B/C) testado em staging anteriormente
- [ ] Backup/restore procedures preparadas
- [ ] Stakeholders notificados de standby
- [ ] On-call team pronto

---

## 📌 Post-Mortem

Após rollback, dentro de 24h:

```
PASSO 1: Análise de Raiz Causa
  • O que falhou? [ ]
  • Por quê? [ ]
  • Raiz causa: [ ]

PASSO 2: Lessons Learned
  • O que aprendemos? [ ]
  • Como prevenir? [ ]

PASSO 3: Corrigir
  • Fixes propostas: [ ]
  • Timeline para re-deploy? [ ]

PASSO 4: Documentação
  • Registrar em: docs/INCIDENT_POST_MORTEM_v0.2.md
```

---

## 🚀 Próxima Ação

1. Escolher OPÇÃO (A/B/C) baseado em deploy real
2. Preencher procedimento com comandos exatos
3. Testar em staging
4. Registrar tempo de execução
5. Documentar neste arquivo
6. Gate 1.4 marcado como ✅ OK (rollback comprovado)

---

**Rollback Procedure Document**

Criado: 4 janeiro 2026  
Responsável: DevOps / On-call Engineer  
Status: TEMPLATE PRONTO (aguardando teste em staging)
