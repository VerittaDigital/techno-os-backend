# 🔧 MOCK OAUTH2 SPECIFICATION — PHASE 1

**Data Criação:** 5 janeiro 2026  
**Propósito:** Definir exatamente como o mock OAuth2 será implementado (A1 + A2)  
**Status:** ⏳ AGUARDANDO DECISÕES A1 + A2

---

## 🎯 DECISÃO A1: MOCK HOSTING MODEL

### Opção A: Server Local Separado

```
Modelo: Servidor Node.js/Express separado (ex.: localhost:3001)
Infraestrutura: Docker container separado (docker-compose)
Integração: Console faz HTTP fetch para localhost:3001/oauth endpoints
Vantagem: Separação clara, mais realista
Desvantagem: Infra extra, gerenciamento docker-compose
```

### Opção B: Rotas Internas no Console

```
Modelo: Endpoints como Next.js API routes (ex.: /api/mock-oauth/*)
Infraestrutura: Sem infra extra (usa console existente)
Integração: Console chama rotas locais do próprio app
Vantagem: Simples, sem infra, isolável por feature flag
Desvantagem: Menos realista (endpoint local vs remoto)
```

---

### A1 DECISÃO REGISTRADA

```
☐ Opção A (server local separado) foi escolhida
   Justificativa técnica: 
   ___________________________________________________________________________
   ___________________________________________________________________________

☐ Opção B (rotas internas no console) foi escolhida
   Justificativa técnica: 
   ___________________________________________________________________________
   ___________________________________________________________________________

Decidido por: Tech Lead ________________________ 
Data: ______________________
```

---

## 🔐 DECISÃO A2: HTTPONLY COOKIE EMITTER

### Componentes Disponíveis

```
1) Route Handler:
   Ex.: app/routes/oauth/callback.ts
   Implementa: OAuth code → token exchange → Set-Cookie
   Set-Cookie emitido aqui.

2) Middleware:
   Ex.: middleware.ts ou app/middleware.ts
   Implementa: Intercepta requests, valida cookie, etc.
   Set-Cookie emitido em qual rota? (deve ser específica)

3) API Route:
   Ex.: app/api/auth/callback.ts ou app/api/oauth/token.ts
   Implementa: POST endpoint que executa token exchange
   Set-Cookie emitido neste endpoint.
```

### Definição do Fluxo (A2)

```
QUEM emite Set-Cookie?
   [ ] Route Handler: _________________________________________________________
   [ ] Middleware: ____________________________________________________________
   [ ] API Route: _____________________________________________________________
   (escolher UM; indicar arquivo/componente exato)

EM QUAL PONTO do fluxo?
   [ ] Após POST /mock/oauth/token (retorna Set-Cookie na response)
   [ ] Na /mock/oauth/callback (após code exchange)
   [ ] Outro: _________________________________________________________________
   (ser específico: qual request gatilha Set-Cookie?)

COMO LOGOUT LIMPA COOKIE?
   [ ] Set-Cookie com Max-Age=0 (cookie expira imediatamente)
   [ ] Set-Cookie overwrite com novo valor vazio
   [ ] Outro: _________________________________________________________________
   (ser específico: qual rota? POST /mock/oauth/logout?)
```

### A2 DECISÃO REGISTRADA

```
Componente responsável: 
   [ ] Route Handler | [ ] Middleware | [ ] API Route
   Arquivo/localização exata: _________________________________________________

Ponto do fluxo:
   [ ] POST /mock/oauth/token
   [ ] /mock/oauth/callback
   [ ] Outro: _________________________________________________________________

Logout cleanup:
   [ ] Max-Age=0
   [ ] Overwrite empty
   [ ] Outro: _________________________________________________________________

Decidido por: Tech Lead ________________________ + Security ________________________
Data: ______________________
```

---

## 📊 MOCK OAUTH2 ENDPOINTS (GENÉRICOS)

### Endpoint 1: GET /mock/oauth/authorize

```
Propósito: Initiate OAuth2 flow (user clicks "Login with OAuth2")
Entrada: ?client_id=console&redirect_uri=http://localhost:3000/callback&state=...
Saída: Redirect to redirect_uri?code=MOCK_CODE&state=...
Schema (genérico OAuth2):
{
  "code": "MOCK_CODE_12345",
  "state": "[valor state recebido]"
}
```

### Endpoint 2: POST /mock/oauth/token

```
Propósito: Exchange code for access_token (backend do console chama aqui)
Entrada: 
{
  "grant_type": "authorization_code",
  "code": "MOCK_CODE_12345",
  "redirect_uri": "http://localhost:3000/callback",
  "client_id": "console"
}
Saída (A2 emite Set-Cookie aqui):
{
  "access_token": "mock_access_token_XXXXX",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "mock_refresh_token_XXXXX" (opcional: só se necessário para E2E)
}
HTTP Response headers:
  Set-Cookie: session=<encoded_session>; HttpOnly; Path=/; SameSite=Strict
```

### Endpoint 3: POST /mock/oauth/logout

```
Propósito: Logout (clear session)
Entrada: 
{
  "token": "mock_access_token_XXXXX"
}
Saída:
{
  "success": true
}
HTTP Response headers (A2 clean aqui):
  Set-Cookie: session=; Max-Age=0; Path=/; (expira cookie)
```

### Endpoint 4: POST /mock/oauth/refresh (OPCIONAL)

```
Propósito: Refresh access_token (apenas se necessário para E2E PHASE 1)
Status: [ ] NECESSÁRIO | [ ] NÃO NECESSÁRIO
Se NÃO necessário, documentar aqui: Por quê? ___________________________________

Se necessário:
Entrada:
{
  "grant_type": "refresh_token",
  "refresh_token": "mock_refresh_token_XXXXX"
}
Saída:
{
  "access_token": "mock_access_token_NEW_XXXXX",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## 🔄 E2E DIAGRAMA (TEXTUAL)

### Fluxo Completo (do usuário até logout)

```
START: Usuario na console
  ↓
[Feature flag NEXT_PUBLIC_ENABLE_F2_3 = true]
  ↓
User clica "Login com OAuth2"
  ↓
Frontend: GET /mock/oauth/authorize?client_id=...&redirect_uri=...&state=...
  ↓
Mock responde: redirect -> http://localhost:3000/callback?code=MOCK_CODE&state=...
  ↓
Frontend/Backend: POST /mock/oauth/token { code, redirect_uri, client_id }
  ↓
[A2: Aqui Set-Cookie HttpOnly é emitido pela response]
  ↓
Mock responde: { access_token, expires_in, refresh_token? }
  ↓
Console armazena access_token (em cookie HttpOnly — já foi setado acima)
  ↓
User está logado! (session ativa)
  ↓
User clica "Logout"
  ↓
Frontend: POST /mock/oauth/logout { token: access_token }
  ↓
[A2: Aqui cookie é deletado via Max-Age=0 ou overwrite]
  ↓
Mock responde: { success: true }
  ↓
User logout completo
  ↓
END
```

---

## ✅ VALIDAÇÃO E2E

```
Verificar que diagrama acima é viável conforme:
  [ ] A1 opção escolhida (server separado? rotas internas?)
  [ ] A2 componente (route handler? API route? middleware?)
  [ ] A2 ponto fluxo (após /token? /callback?)
  [ ] A2 logout cleanup (Max-Age=0? overwrite?)

Se algum ponto não alinhar: registrar bloqueio e escalar.
```

---

## 🚀 PRÓXIMO PASSO

Uma vez que A1 + A2 estejam definidas:

1. ✅ Preencher seção "A1 DECISÃO REGISTRADA" acima
2. ✅ Preencher seção "A2 DECISÃO REGISTRADA" acima
3. ✅ Validar que E2E DIAGRAMA está alinhado com A1 + A2
4. ✅ Descer para seção 3.3 (implementação)

---

**Status desta spec:** ⏳ BLOQUEADA (aguardando A1 + A2 decisões)

Não implementar mock sem que AMBOS A1 e A2 estejam preenchidos com decisões explícitas.
