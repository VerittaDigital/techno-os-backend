# 🔒 CSP VIABILITY CHECK — PHASE 1

**Data Criação:** 5 janeiro 2026  
**Propósito:** Validar se Content Security Policy (CSP) strict é viável + definir A3 criteria  
**Status:** ⏳ AGUARDANDO VARREDURA + ASSINATURA

---

## 🔎 EVIDÊNCIA OBJETIVA: VARREDURA POR PADRÕES INLINE

### Comando de Varredura (execute antes de preencher)

```bash
# Encontrar <script> tags inline no app/
grep -r "<script" app/ --include="*.jsx" --include="*.tsx" --include="*.ts" --include="*.js"

# Encontrar inline handlers (onClick=, onLoad=, etc)
grep -rE "on(Click|Change|Load|Submit|Error|Blur|Focus)=" app/ --include="*.jsx" --include="*.tsx"

# Encontrar unsafe-inline em arquivos (se houver CSP atual)
grep -r "unsafe-inline" app/ --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx"

# Contar matches
grep -r "<script" app/ --include="*.jsx" --include="*.tsx" | wc -l
```

### Resultados da Varredura

```
Comando executado (copie output exato aqui):
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________

Resumo:
  [ ] <script> inline tags encontradas: ___________ (número)
  [ ] inline handlers (onClick=, onLoad=, etc) encontradas: ___________ (número)
  [ ] unsafe-inline mencões: ___________ (número)

Data da varredura: ____________________
Executado por: _________________________ (nome)
```

---

## 📊 ANÁLISE

### CSP Strict Viável?

```
Conclusão da varredura:
  [ ] NÃO há padrões inline detectados → CSP STRICT viável agora
  [ ] HÁ padrões inline → CSP STRICT não é viável; usar CSP MÍNIMA
```

---

### Cenário 1: CSP STRICT VIÁVEL

```
Se NÃO há inline scripts detectados:

Recomendação:
  Implementar CSP strict nesta sprint (PHASE 1):
  
  Content-Security-Policy: 
    default-src 'self';
    script-src 'self';
    style-src 'self';
    img-src 'self' data: https:;
    font-src 'self';
    connect-src 'self' <BACKEND_API>;
    frame-ancestors 'none';
    base-uri 'self';
    form-action 'self';

Validação:
  [ ] Implementar CSP acima
  [ ] Testar que app carrega sem erros (T5)
  [ ] Logs não mostram CSP violations

Resultado: ✅ CSP STRICT
```

---

### Cenário 2: CSP STRICT NÃO VIÁVEL

```
Se HÁ padrões inline detectados:

A3 CRITERIA: Definir limite explícito de exceções

Opção (A): ZERO EXCEÇÕES (refactor inline handlers agora)
  Ação: Converter TODOS os handlers inline para event listeners
  Tempo: [estimativa]
  Viável? [ ] SIM | [ ] NÃO
  
  Se SIM:
    Implementar refactor + CSP strict (mesmo que acima)
    Resultado: ✅ CSP STRICT (depois de refactor)
  
  Se NÃO:
    Documentar bloqueio + escalar

Opção (B): MÁXIMO 1 EXCEÇÃO (permitir 1 padrão específico)
  Qual padrão? (ex.: "apenas 1 <script> no index.html") _____________________
  
  CSP com 1 exceção (exemplo):
    Content-Security-Policy:
      default-src 'self';
      script-src 'self' 'nonce-RANDOM' (nonce só para <script> específico);
      ... (resto igual strict)
  
  Viável? [ ] SIM | [ ] NÃO

Opção (C): MÁXIMO N EXCEÇÕES (permitir N padrões)
  Quantas? _________
  Quais? (lista) __________________________________________________________________
  
  CSP com N exceções (exemplo):
    ... (definir policy mínima viável)
  
  Viável? [ ] SIM | [ ] NÃO

Opção (D): CSP PERMISSIVA NESTA SPRINT (refactor em PHASE FUTURA)
  Justificativa: ________________________________________________________________
  
  CSP permissiva (menos restritiva, mas melhor que zero):
    Content-Security-Policy:
      default-src 'self';
      script-src 'self' 'unsafe-inline';  (permitir inline temporariamente)
      style-src 'self' 'unsafe-inline';
      ... (resto)
  
  Plano para refactor: ____________________________________________________________
  PHASE designado: _________________
  
  Viável? [ ] SIM | [ ] NÃO
```

---

## 🎯 DECISÃO A3: CSP CRITERIA APROVADO

### Critério Escolhido

```
☐ Opção A: ZERO EXCEÇÕES (refactor inline handlers agora)
   Refactor tempo estimado: _____________________________
   Viável agora? [ ] SIM | [ ] NÃO

☐ Opção B: MÁXIMO 1 EXCEÇÃO
   Pattern específico: _________________________________________________________
   Viável agora? [ ] SIM | [ ] NÃO

☐ Opção C: MÁXIMO N EXCEÇÕES
   Número de exceções: _________
   Patterns específicos: ________________________________________________________
   Viável agora? [ ] SIM | [ ] NÃO

☐ Opção D: CSP PERMISSIVA (refactor PHASE X)
   PHASE designado para refactor: _____________________________________________
   Viável agora? [ ] SIM | [ ] NÃO

Justificativa da escolha:
_______________________________________________________________________________
_______________________________________________________________________________
```

---

## ✅ VALIDAÇÃO IMPLEMENTAÇÃO

```
Depois de implementar CSP conforme criterion acima:

[ ] CSP header está em next.config.js (ou middleware.ts)
[ ] Policy genérica testada em dev (npm run dev)
[ ] Nenhum erro CSP no console do browser (DevTools)
[ ] App carrega sem quebra visual/funcional
[ ] T5 testa (CSP aplicado sem quebra)

Se qualquer validação falhar:
  → Corrigir conforme criterion aprovado
  → Se não conseguir: escalar
```

---

## 📋 ASSINATURAS

### Security Lead

```
☐ Security: _________________________ (nome)
  Data: ___________________________
  A3 Criteria aprovado: SIM / NÃO
  
  Se NÃO, motivo:
  ___________________________________________________________________________
  
  Assinatura/confirmação: ___________________________________
```

### Tech Lead

```
☐ Tech Lead: _________________________ (nome)
  Data: ___________________________
  A3 Criteria tecnicamente viável: SIM / NÃO
  
  Se NÃO, motivo:
  ___________________________________________________________________________
  
  Assinatura/confirmação: ___________________________________
```

---

## 🚀 PRÓXIMO PASSO

Uma vez que A3 CRITERIA esteja aprovado por AMBOS Security + Tech Lead:

1. ✅ Descer para seção 3.2 (implementação Security Baseline)
2. ✅ Implementar CSP exatamente conforme criterion aprovado
3. ✅ Testar T5 (CSP aplicado sem quebra)

---

**Status desta check:** ⏳ BLOQUEADA (aguardando varredura + assinatura)

Não implementar CSP sem que A3 CRITERIA esteja aprovado por Security + Tech Lead.
