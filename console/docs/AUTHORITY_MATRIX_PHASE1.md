# 📋 AUTHORITY MATRIX — PHASE 1 EXECUTION

**Data:** 5 janeiro 2026  
**Propósito:** Definir quem tem autoridade decisória em cada ponto crítico de PHASE 1  
**Status:** ⏳ AGUARDANDO ASSINATURAS

---

## 🎯 MATRIZ DE AUTORIDADES

### Decisão A1: Mock OAuth2 Hosting Model

**Ponto:** Escolher entre Opção A (server local separado) OU Opção B (rotas internas no console)

**Decisor:** Tech Lead  
**Responsabilidade:** 
- Avaliar arquitetura Next.js + Docker atual
- Escolher modelo viável
- Registrar justificativa técnica

**Assinatura/Confirmação:**
```
☐ Tech Lead: _________________ (nome)
  Data: _____________________
  Decisão: [ ] Opção A (server local) | [ ] Opção B (rotas internas)
  Justificativa: _____________________________________________________________
```

---

### Decisão A2: HttpOnly Cookie Emitter

**Ponto:** Definir QUEM emite Set-Cookie e EM QUAL PONTO do fluxo OAuth2

**Decisor:** Tech Lead (+ Security se houver restrições de compliance)  
**Responsabilidade:**
- Escolher componente: route handler OU middleware OU API route
- Definir ponto fluxo: "após POST /token" OU "na /callback" OU outro
- Definir logout cleanup: Max-Age=0 OU overwrite

**Assinatura/Confirmação:**
```
☐ Tech Lead: _________________ (nome)
  Data: _____________________
  Componente: [ ] Route handler | [ ] Middleware | [ ] API route
  Ponto fluxo: ______________________________________________________________
  Logout cleanup: ____________________________________________________________

☐ Security (se aplicável): _________________ (nome)
  Data: _____________________
  Aprovação: SIM / NÃO (se NÃO, registrar motivo):
  ___________________________________________________________________________
```

---

### Decisão A3: CSP (Content Security Policy) Criteria

**Ponto:** Definir limite explícito de exceções aceitáveis

**Decisor:** Security + Tech Lead  
**Responsabilidade:**
- Validar varredura grep por padrões inline
- Definir critério: "0 exceções" OU "máximo N exceções" OU "exceção específica X"
- Aprovar implementação conforme critério

**Assinatura/Confirmação:**
```
☐ Security: _________________ (nome)
  Data: _____________________
  Critério aprovado: ________________________________________________________
  (Ex.: "0 exceções" OU "máximo 2 exceções style-src" OU "exceção temporária X")

☐ Tech Lead: _________________ (nome)
  Data: _____________________
  Confirmação técnica: SIM / NÃO (se NÃO, registrar motivo):
  ___________________________________________________________________________
```

---

### Decisão Gate 1: OAuth2 Backend Status

**Ponto:** Assinar status de Gate 1 (OK | AWAITING + AUTORIZADO MOCK | PARTIAL)

**Decisor:** PM OU Tech Lead  
**Responsabilidade:**
- Verificar resposta backend (ou AWAITING status)
- Se AWAITING/PARTIAL: autorizar mock puro (escrito + assinado)
- Registrar fonte/evidência

**Assinatura/Confirmação:**
```
☐ PM: _________________ (nome)
  Data: _____________________
  Status Gate 1: [ ] OK | [ ] AWAITING | [ ] PARTIAL
  
  Se AWAITING/PARTIAL:
    Autorizado MOCK PURO? [ ] SIM | [ ] NÃO
    Justificativa: ___________________________________________________________
```

---

## 📋 REGRA GERAL

**Nenhuma decisão técnica crítica (A1, A2, A3, Gate 1) pode ser implementada sem:**
1. ✅ Decisor designado assinou OU confirmou
2. ✅ Registrado em PRÉ-CHECK documento correspondente
3. ✅ Data + nome explícito (não assumido)

---

## 📊 STATUS DE ASSINATURAS

| Decisão | Decisor | Status | Data | Assinatura |
|---------|---------|--------|------|-----------|
| A1: Mock Hosting | Tech Lead | ⏳ AGUARDANDO | --- | --- |
| A2: HttpOnly Emitter | Tech Lead + Security | ⏳ AGUARDANDO | --- | --- |
| A3: CSP Criteria | Security + Tech Lead | ⏳ AGUARDANDO | --- | --- |
| Gate 1: OAuth2 Status | PM / Tech Lead | ⏳ AGUARDANDO | --- | --- |

---

## 🚀 PRÓXIMO PASSO

Uma vez que TODAS as 4 decisões acima estejam assinadas/confirmadas:

1. ✅ Preencher GATE_1_STATUS_20260105.md
2. ✅ Preencher MOCK_OAUTH2_SPEC.md (A1 + A2)
3. ✅ Preencher CSP_VIABILITY_CHECK.md (A3)
4. ✅ Iniciar seção 3 (implementação)

---

**Status desta matriz:** ⏳ BLOQUEADA (aguardando assinaturas)

Não iniciar implementação até que TODAS as 4 decisões estejam assinadas.
