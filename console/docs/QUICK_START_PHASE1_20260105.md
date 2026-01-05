# 🎬 PHASE 1 EXECUTION — QUICK START GUIDE

**Status:** 🚀 **GO FOR EXECUTION** (5 Jan 2026, 11:15)

---

## ⚡ RESUMO EXECUTIVO (2 min read)

**O que fazer agora:**
```
PRÉ-CHECK (30 min):
  1. Criar 4 docs obrigatórios (AUTHORITY_MATRIX, GATE_1_STATUS, MOCK_OAUTH2_SPEC, CSP_VIABILITY)
  2. Obter assinaturas (Tech Lead, Security, PM)

IMPLEMENTAR (3-4 dias):
  1. Feature flag (3.1)
  2. Security baseline — HttpOnly + CSP (3.2)
  3. Mock OAuth2 E2E (3.3)
  4. Logging sanitizado (3.4)
  5. Métricas doc (3.5)

TESTAR (1 dia):
  1. T1–T5 conforme TEST_MATRIX
  2. Todos testes passam? → Pronto para seal

SEAL (2 horas):
  1. PR com código + docs + evidências
  2. Veredito: D1–D6 = OK?
  3. SIM → "APTO para PHASE 2" ✅
```

**Timeline:** ~4-5 dias úteis  
**Final esperado:** ~9 janeiro 2026

---

## 📋 PRÉ-CHECK (INICIAR AGORA)

### Doc 1: AUTHORITY_MATRIX_PHASE1.md
```
Quem decide A1 (mock hosting)?        Tech Lead
Quem decide A2 (HttpOnly emitter)?    Tech Lead + Security (quando necessário)
Quem decide A3 (CSP criteria)?        Security + Tech Lead
Quem assina Gate 1 status?            PM ou Tech Lead
```
**Ação:** Criar doc em docs/ + obter assinaturas

### Doc 2: GATE_1_STATUS_20260105.md
```
Status: OK | AWAITING + AUTORIZADO MOCK | PARTIAL
Assinado por: [Tech Lead/PM nome]
```
**Ação:** Criar doc + assinatura

### Doc 3: MOCK_OAUTH2_SPEC.md
```
A1) Opção A (server local) OU Opção B (rotas internas)?
A2) QUEM emite Set-Cookie? (route handler / middleware / API route?)
A2) QUANDO emite? (após POST /token? na /callback?)
A2) Como logout limpa? (Max-Age=0? overwrite?)

E2E diagrama:
  User → /authorize → /token → Set-Cookie HttpOnly → logout → delete
```
**Ação:** Tech Lead escolhe + documenta (10 min)

### Doc 4: CSP_VIABILITY_CHECK.md
```
Varredura grep: encontrou N handlers inline ou scripts?
A3) Limite de exceções: 0? 1? quantas?
Assinado por: Security + Tech Lead
```
**Ação:** Varredura + decisão aprovada (10 min)

✅ **Resultado:** PRÉ-CHECK completo → Pronto para 3.1

---

## 🔨 IMPLEMENTAÇÃO (3-4 dias)

### 3.1 Feature Flag (1 dia)
- [ ] Implementar em código
- [ ] Default OFF
- [ ] Teste D1: Flag ON/OFF funciona

### 3.2 Security Baseline (1 dia)
- [ ] HttpOnly conforme A2
- [ ] CSP conforme A3
- [ ] Logs sanitizados
- [ ] Testes D2, D3, D5: ✅

### 3.3 Mock OAuth2 (1 dia)
- [ ] /authorize endpoint
- [ ] /token endpoint
- [ ] /logout endpoint
- [ ] E2E funciona
- [ ] Teste D4: ✅

### 3.4 Logging (4 horas)
- [ ] trace_id por request
- [ ] auth_mode="F2.3"
- [ ] Sem segredos
- [ ] Teste D5: ✅

### 3.5 Métricas (2 horas)
- [ ] METRICS_DEFINITION_v0.2.md
- [ ] Success + adoption metrics
- [ ] Teste D6: ✅

---

## ✅ TESTES (1 dia)

```
T1: Flag OFF                    ✅ OAuth2 indisponível
T2: Flag ON + mock ok           ✅ Login funciona + HttpOnly
T3: Mock fail                   ✅ Erro controlado
T4: Logout                      ✅ Cookie limpo
T5: CSP                         ✅ App carrega sem quebra
```

**Se teste falhar:** Corrigir imediatamente (bloqueador)

---

## 📦 SEAL (2 horas)

```
✅ Código pronto (branch + PR)
✅ 6 docs obrigatórios completos
✅ Testes T1–T5 passam
✅ D1–D6 validados

Veredito final:
  D1–D6 todos OK? 
    ✅ SIM → "APTO para PHASE 2"
    ❌ NÃO → BLOQUEIO + corrigir
```

---

## 🚨 FAIL-CLOSED

Se qualquer PRÉ-CHECK falhar:
→ ABORTAR (criar BLOCKER doc + notificar PM/Tech Lead)

Se qualquer DoD falhar:
→ ABORTAR PHASE 2 (corrigir PHASE 1)

Se qualquer teste falhar:
→ Corrigir imediatamente (não prosseguir)

---

## 📅 CRONOGRAMA

```
5 Jan (hoje):
  09:00–09:30: PRÉ-CHECK (4 docs + assinaturas)
  10:00+:     3.1 feature flag

6–8 Jan:
  3.2–3.5 implementação
  T1–T5 testes paralelos

9 Jan:
  ✅ SEAL
  ✅ Veredito PHASE 1 GATE
  ✅ "APTO para PHASE 2"

Próximo:
  PHASE 2 kick-off (10 Jan)
```

---

## 🎯 LINKS REFERÊNCIA

- Prompt completo: [PROMPT PHASE 1 REV. A1–A4](../PROMPT_PHASE1_REV_A1_A4.txt)
- Parecer técnico: [PARECER_EXECUTABILIDADE_FINAL](PARECER_EXECUTABILIDADE_FINAL_REV_A1_A4_20260105.md)
- Autorização: [AUTORIZATION_AND_KICKOFF](AUTORIZATION_AND_KICKOFF_PHASE1_20260105.md)
- Documentos PRÉ-PHASE: [docs/](.)

---

## 🚀 STATUS

```
✅ Autorizado
✅ Prompt pronto
✅ Governança clara
✅ Timeline realista

GO FOR EXECUTION
```

Executor: Comece com PRÉ-CHECK (30 min). Depois, implementação.

