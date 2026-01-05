# PROMPT DE EXECUÇÃO — v0.2 (FINAL COM AJUSTE) — FAIL-CLOSED

**Papel:** Executor Dev Sênior (Copilot)  
**Supervisão:** Arquiteto Técnico (V-COF Hermes Spectrum)  
**Data:** 4 de janeiro de 2026  
**Status:** ✅ APTO PARA EXECUÇÃO (com ajuste cosmético aplicado)

**Escopo FIXO e permitido:** habilitar OAuth2 + suporte dual-mode F2.3/F2.1 no Console,
com gates e mitigação de riscos (XSS/token storage, rollout/rollback, matriz de testes),
CONFORME Parecer Samurai v0.2 e Parecer DevOps Copilot (APTO COM RESSALVAS).

**Proibições:** não criar produto, não criar UX extensa, não criar "métricas de produto", não criar comunicação externa,
não prometer timeline/datas, não inventar endpoints/campos/headers/infra.

---

## 0) REGRAS ABSOLUTAS (GOVERNANÇA)

R1. Não alterar escopo funcional: OAuth2 + (se aplicável) dual-mode (F2.3 preferido + fallback F2.1).
R2. Não adicionar funcionalidades: qualquer item que não seja gate/segurança/rollback/flag/testes necessários é proibido.
R3. Não antecipar fases futuras: sem "deprecation date", sem "comms plan", sem "SLOs públicos"; somente o mínimo para executar com segurança.
R4. Não remover salvaguardas: gates, evidências, fail-closed, rollback testável, logging sanitizado.
R5. FAIL-CLOSED: qualquer ausência de evidência crítica → ABORTAR com BLOQUEIO documentado.

**Definição de EVIDÊNCIA (obrigatória):**
- Código no repo (console/backend), logs de execução, outputs de comando, ou confirmação escrita do backend (issue/email/slack transcrito em doc).
- Sem evidência => BLOQUEIO. Proibido inferir.

---

## 1) PRÉ-PHASE (READINESS) — RESOLVER 5 BLOQUEIOS CRÍTICOS ANTES DE CODAR

IMPORTANTE: O Parecer DevOps Copilot identificou 5 bloqueios externos que impedem começar código.
Esta PRÉ-PHASE cria os docs mínimos para resolver os bloqueios SEM ampliar escopo.

### 1.0 Criar checklist mestre de prontidão (NÃO opcional)
- Criar: docs/PRE_PHASE_READINESS.md
- Conteúdo: checklist dos 5 bloqueios, status (MISSING/OK), e links para docs correspondentes.
FAIL-CLOSED:
- Se o checklist não existir, não iniciar implementação.

### 1.1 BLOQUEIO 1 — Confirmar OAuth2 Provider com Backend (CRÍTICO)
- Criar: docs/BACKEND_COMMUNICATION_PLAN.md
  • dono backend (nome/contato)
  • canal (issue/slack/email)
  • template de perguntas/confirmação
- Obter confirmação escrita do backend e registrar em:
  • docs/BACKEND_OAUTH2_CONFIRMATION.md
    - tipo do fluxo (OAuth2/OIDC e qual grant)
    - endpoints reais (authorize/token/refresh/logout se houver)
    - campos mínimos de resposta (access_token, expires_in, refresh_token se houver)
    - constraints (redirect_uri, scopes, PKCE, etc. se existir)
    - status de disponibilidade (pronto/agendado) — sem prometer datas se não confirmadas

FAIL-CLOSED:
- Se não houver confirmação escrita com endpoints reais: ABORTAR (não implementar OAuth2 "no escuro").

### 1.2 BLOQUEIO 2 — Confirmar CONTEXTO do Console (Web/CLI/Deploy) (CRÍTICO)
- Criar: docs/CONSOLE_ARCHITECTURE.md contendo SOMENTE fatos:
  • o console é Next.js web em browser? (SIM/NÃO + evidência)
  • como é executado hoje (comando) e como é implantado (Vercel/Docker/manual/CI)
  • onde ele roda (browser/servidor/desktop)
  • como ele chama o backend (HTTP direto? proxy? baseURL por env?)

FAIL-CLOSED:
- Sem confirmação do contexto, SECURITY_DESIGN vira especulativo ⇒ ABORTAR antes de codar auth.

### 1.3 BLOQUEIO 3 — Evidência de F2.1 funcional no Console (para dual-mode) (CRÍTICO)
- Ação: rodar inventário local (evidência por código) para identificar auth existente:
  • buscar headers "X-API-Key" ou equivalente
  • buscar env vars "*_API_KEY", "*_BETA_*", etc.
- Criar: docs/F2.1_INVENTORY.md com:
  • onde no código é enviado (arquivo/linha)
  • quais endpoints usam
  • como é provisionado (env, secret store)
  • prova de execução (log sanitizado ou teste)
- Se NÃO existir evidência de F2.1 no console:
  • Criar: docs/SCOPE_DECISION_v0.2.md declarando:
    - "Dual-mode SKIPPED (sem fallback real)"
    - v0.2 se reduz a OAuth2-only (F2.3) — isso NÃO é novo escopo; é coerência fail-closed.

FAIL-CLOSED:
- Proibido implementar "fallback" para um método que não existe.

### 1.4 BLOQUEIO 4 — Rollback testável (infra real) (CRÍTICO)
- Mapear o processo real de deploy do console (a partir do docs/CONSOLE_ARCHITECTURE.md).
- Criar:
  • docs/DEPLOYMENT_STRATEGY_v0.2.md (mínimo operacional)
  • docs/ROLLBACK_PROCEDURE_v0.2.md (passos testáveis)
- Exigência: o rollback deve ser ENSAIADO (em staging ou ambiente equivalente) e evidenciado por output/log.

FAIL-CLOSED:
- Se não houver ambiente/procedimento testável: ABORTAR antes de qualquer rollout/canary.

### 1.5 BLOQUEIO 5 — Canal formal de comunicação com backend (infra de coordenação) (CRÍTICO)
- Resolve-se junto com 1.1 via BACKEND_COMMUNICATION_PLAN.md.

FAIL-CLOSED:
- Sem dono/canal, o bloqueio 1 não é solucionável => execução trava.

### GATE PARA INICIAR IMPLEMENTAÇÃO (2.x):
```
- [ ] docs/PRE_PHASE_READINESS.md existe e todos os 5 bloqueios estão em status OK
- [ ] docs/BACKEND_OAUTH2_CONFIRMATION.md completo (endpoints reais)
- [ ] docs/CONSOLE_ARCHITECTURE.md completo (contexto confirmado)
- [ ] docs/F2.1_INVENTORY.md OU docs/SCOPE_DECISION_v0.2.md (dual-mode decidido)
- [ ] docs/DEPLOYMENT_STRATEGY_v0.2.md + docs/ROLLBACK_PROCEDURE_v0.2.md com ensaio registrado

Se qualquer item falhar: STOP.
```

---

## 2) IMPLEMENTAÇÃO (APÓS GATE) — SOMENTE O NECESSÁRIO, ORDEM FIXA

### 2.0 Regras de implementação
- Todas as URLs/endpoints/flows devem vir do BACKEND_OAUTH2_CONFIRMATION.md.
- Storage de token deve seguir SECURITY_DESIGN (a ser produzido agora com base no contexto real).
- Logging sanitizado: nunca tokens/segredos/PII.

### 2.1 Implementar Runtime Feature Flag (mínimo para canary/rollback)
- Implementar flag conforme DEPLOYMENT_STRATEGY_v0.2.md (SEM inventar).
- Default: FALSE.
- Evidência: prova de toggle (on/off) e efeito observável (sem secrets).

FAIL-CLOSED:
- Se flag não for revertível rapidamente (procedimento): STOP (não avançar para OAuth2).

### 2.2 Implementar SECURITY_DESIGN_v0.2.md (antes de OAuth2)
- Criar docs/SECURITY_DESIGN_v0.2.md usando o contexto confirmado:
  • token storage viável e seguro para aquele contexto (browser vs não-browser)
  • mitigação XSS/CSP (se browser)
  • política de logs
- Só depois codar auth.

### 2.3 Implementar OAuth2/OIDC (mínimo viável e seguro)
- Codar o fluxo conforme confirmação do backend:
  • authorize → token → refresh (se existir) → logout (se existir)
- Não criar UI extensa: apenas o mínimo necessário para autenticar e continuar fluxo do console.
- Erros devem seguir política fail-closed (401/403/429/5xx/timeout/schema mismatch).

**Mock Provider (local/staging):**
  • Use endpoints from BACKEND_OAUTH2_CONFIRMATION.md
  • Replace domain with localhost:PORT (or equivalent)
  • Return canned responses matching confirmed schema

- Evidências:
  • outputs de teste/local run (sanitizados)
  • confirmação de que tokens não aparecem em logs

FAIL-CLOSED:
- Se storage seguro não for possível no contexto: STOP e registrar bloqueio.

### 2.4 Implementar Dual-Mode (CONDICIONAL, SOMENTE SE F2.1 EXISTE)
- Condição:
  • docs/F2.1_INVENTORY.md confirma F2.1 real e funcional.
- Se condição OK:
  • Implementar selector:
    - se flag F2.3 ON e credencial válida → F2.3
    - senão → F2.1 (apenas onde aplicável)
    - se nenhum → erro explícito "no valid auth"
- Se condição NÃO OK:
  • NÃO implementar dual-mode. Respeitar SCOPE_DECISION_v0.2.md.

FAIL-CLOSED:
- Proibido "assumir" fallback.

### 2.5 Testes — Matriz mínima obrigatória
- Criar/rodar testes conforme docs/TEST_MATRIX_v0.2.md.
- Evidência: output de execução dos testes.

FAIL-CLOSED:
- Se algum cenário falhar: não avançar para rollout.

---

## 3) ROLLOUT/CANARY/ROLLBACK — OPERACIONAL, SEM PROMESSAS NUMÉRICAS

- Executar canary exatamente conforme DEPLOYMENT_STRATEGY_v0.2.md (sem inventar percentuais/dias).
- Rollback deve ser executado como ensaio (se ainda não foi) e depois ficar pronto para uso real.
- Critérios de rollback devem ser definidos no doc (podem ser simples: "erro acima do baseline", "incidente de segurança", etc.).

FAIL-CLOSED:
- Qualquer incidente de segurança => rollback imediato.

---

## 4) FECHAMENTO (SEAL) — PACOTE DE EVIDÊNCIAS OBRIGATÓRIO

### A) Docs criados/atualizados:
- docs/PRE_PHASE_READINESS.md
- docs/BACKEND_COMMUNICATION_PLAN.md
- docs/BACKEND_OAUTH2_CONFIRMATION.md
- docs/CONSOLE_ARCHITECTURE.md
- docs/SECURITY_DESIGN_v0.2.md
- docs/DEPLOYMENT_STRATEGY_v0.2.md
- docs/ROLLBACK_PROCEDURE_v0.2.md
- docs/TEST_MATRIX_v0.2.md
- docs/F2.1_INVENTORY.md OU docs/SCOPE_DECISION_v0.2.md

### B) Evidências:
- logs sanitizados de execução OAuth2 (sem segredos)
- output dos testes da matriz
- prova do toggle da feature flag
- prova do rollback ensaiado

### C) Veredito final:
- APTO somente se: gates OK + OAuth2 funcionando + (se aplicável) dual-mode validado + rollback testado.
- Senão: INAPTO + bloqueios explícitos.

---

## 📌 NOTA SOBRE ESTE DOCUMENTO

**Ajuste Aplicado (4 jan 2026):**
- Seção 2.3: Clarificação adicionada sobre Mock Provider (3 linhas)
  - Referência: "Use endpoints from BACKEND_OAUTH2_CONFIRMATION.md"
  - Operacional: "Replace domain with localhost:PORT"
  - Schema: "Return canned responses matching confirmed schema"

**Status Pré-Ajuste:** APTO (95% clareza)  
**Status Pós-Ajuste:** ✅ APTO (99%+ clareza)  
**Executor pode iniciar:** ✅ SIM (imediatamente)

---

**FIM DO PROMPT**
