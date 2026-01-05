# 📧 BACKEND COMMUNICATION PLAN — v0.2

**Objetivo:** Abrir canal formal com backend para confirmar OAuth2 provider  
**Data:** 4 janeiro 2026  
**Status:** TEMPLATE PRONTO PARA PREENCHIMENTO

---

## 📋 Informações do Proprietário Backend

### Identificação

```
Nome Completo: [DEV SENIOR Backend — Equipe Backend]
Email: [A CONFIRMAR COM PM]
Slack Handle: [A CONFIRMAR COM PM]
Telefone (emergência): [A CONFIRMAR COM PM]
Timezone: [A CONFIRMAR — Provavelmente UTC-3 (Brasil)]

Nota: PM deve enviar este template ao Backend e preencher resposta
```

### Papéis/Responsabilidades

- [x] Design e implementação OAuth2 provider (F2.3)
- [x] Confirmação de endpoints (authorize, token, refresh_token, logout)
- [x] Confirmação de campos esperados (schema de resposta)
- [x] Timeline/disponibilidade (para v0.2 roadmap)
- [x] Suporte técnico durante integração (PHASE 1-5)

---

## 💬 Canal de Comunicação Primário

### Escolher: ( Slack / GitHub Issue / Email / Meeting / Outro )

```
Tipo: [A CONFIRMAR COM BACKEND]
  [x] Slack (recomendado para rapidez)
  [ ] Email (formal, rastreável)
  [ ] GitHub Issue (versionado)
  [ ] Meeting sync (semanal)
  [ ] Outro: [ ]

Detalhes:
  • Se Slack: [#backend-integration ou @backend-lead]
  • Se GitHub: [link para issue template]
  • Se Email: [backend-team@company.com]
  • Se Meeting: [segunda-feira 14:00 UTC-3]
```

### SLA de Resposta

```
✅ Tempo esperado para primeira resposta: 24 horas
✅ Escalação (se não responder em SLA): PM → Engineering Lead → CTO
```

---

## 📝 Template de Confirmação

### Usar este template para ENVIAR AO BACKEND:

```
Assunto: v0.2 OAuth2 Integration - Provider Confirmation Needed

Olá [NOME],

Estamos iniciando a integração OAuth2 no Console v0.2 e precisamos de 
confirmação formal sobre o provider que será usado.

Favor responder os itens abaixo para que possamos prosseguir com confiança:

---

1. TIPO DE FLUXO
   • Qual é o tipo de fluxo OAuth2/OIDC?
     [ ] Authorization Code
     [ ] Implicit
     [ ] Client Credentials
     [ ] Device Flow
     [ ] Custom
   • Se custom, descreva:

2. ENDPOINTS
   • URL do endpoint de authorize: [ ]
   • URL do endpoint de token: [ ]
   • URL do endpoint de refresh (se existir): [ ]
   • URL do endpoint de logout (se existir): [ ]
   • Base URL ou domínio: [ ]

3. CAMPOS DE RESPOSTA ESPERADOS
   • access_token (obrigatório): [ ]
   • expires_in (obrigatório): [ ]
   • refresh_token (se existir): [ ]
   • id_token (se OIDC): [ ]
   • Outros campos: [ ]

4. CONSTRAINTS & REQUIREMENTS
   • Redirect URI(s) esperada(s): [ ]
   • Scopes obrigatórios: [ ]
   • PKCE obrigatório?: [ ] SIM / [ ] NÃO
   • Headers customizados?: [ ]
   • Autenticação de request (client_id/secret)?: [ ]

5. DISPONIBILIDADE
   • Provider está pronto agora?: [ ] SIM / [ ] NÃO / [ ] PARCIALMENTE
   • Se não: data esperada de disponibilidade: [ ]
   • Existe mock/staging provider para testes?: [ ] SIM / [ ] NÃO

6. DOCUMENTAÇÃO
   • URL da doc oficial: [ ]
   • Exemplos de uso: [ ]
   • Contato técnico para dúvidas: [ ]

---

Por favor responda até [DATA/HORA] para que possamos manter o cronograma.

Obrigado,
[NOME DO EXECUTOR]
```

---

## ✅ Checklist de Execução

### Antes de enviar:

- [ ] Dono backend identificado e contatado informalmente
- [ ] Template adaptado com placeholders preenchidos
- [ ] Email/mensagem revisada
- [ ] Data/hora de resposta confirmada no SLA

### Depois de enviar:

- [ ] Template enviado via [CANAL]
- [ ] Data/hora de envio registrada: [ ]
- [ ] Resposta recebida?: [ ] SIM / [ ] NÃO
- [ ] Data/hora de resposta: [ ]
- [ ] Resposta registrada em: docs/BACKEND_OAUTH2_CONFIRMATION.md

---

## 📌 Status de Comunicação

| Evento | Data/Hora | Status | Notas |
|--------|-----------|--------|-------|
| Plan criado | 4 jan 2026 | ✅ | Template pronto |
| Dono identificado | [ ] | ⏳ | Aguardando |
| Template enviado | [ ] | ⏳ | Aguardando |
| Resposta recebida | [ ] | ⏳ | Aguardando |
| Confirmação registrada | [ ] | ⏳ | Aguardando |

---

## 🚀 Próxima Ação

1. **Identificar:** Nome/contato do proprietário backend
2. **Personalizar:** Template com contatos reais
3. **Enviar:** Via canal escolhido
4. **Aguardar:** Resposta do backend (SLA definido)
5. **Registrar:** Respostas em docs/BACKEND_OAUTH2_CONFIRMATION.md

---

**Backend Communication Plan**

Criado: 4 janeiro 2026  
Responsável: Product Manager  
Status: TEMPLATE PRONTO
