# 🏗️ CONSOLE ARCHITECTURE — Contexto Real

**Objetivo:** Documentar fatos reais sobre como o console funciona (web/CLI/deploy/contexto)  
**Data:** 4 janeiro 2026  
**Status:** TEMPLATE PRONTO PARA PREENCHIMENTO

---

## 📍 Contexto de Execução

### 1️⃣ Tipo de Console (Escolher 1)

- [x] **Web App** (roda em browser) ✅ CONFIRMADO
  - Framework: Next.js 16.1.1 + React 19.2.3
  - Acesso: via URL (ex: https://console.example.com)
  - Storage disponível: localStorage, sessionStorage, cookies (HttpOnly viável em Next.js)

- [ ] **CLI / Terminal**
  - Linguagem: [?]
  - Execução: Comando local (ex: `console-cli command`)
  - Storage: Arquivo local, env vars, credential manager

- [ ] **Desktop App**
  - Framework: [?]
  - Plataforma: Windows/Mac/Linux/All
  - Storage: File system, secure keystore

- [ ] **Outro:**
  - Especificar: [ ]

---

## 🚀 Como é Executado Hoje

### URL / Comando / Ponto de Entrada

```
Tipo de acesso: HTTP Web (browser)
URL/Comando: npm run dev (local) | next start (production)
Exemplo: http://localhost:3000 (dev) | https://console.example.com (prod)
```

### Ambiente Local

```
Pasta raiz: d:\Projects\techno-os-console
Command para rodar (dev): npm run dev
Command para rodar (prod): npm run build && npm run start
Port (se aplicável): 3000 (padrão Next.js)
```

### Variáveis de Ambiente

```
Quais env vars controlam o comportamento?
  • NEXT_PUBLIC_API_BASE_URL = [ TO BE DEFINED ]
  • NEXT_PUBLIC_ENABLE_F2_3 = false (default, será configurado em v0.2)
  • API_KEY (F2.1) = [ Não encontrado no código hoje — ver F2.1_INVENTORY ]
  • NODE_ENV = development | production
```

---

## 🌐 Como é Implantado (Deploy)

### Infraestrutura Atual

```
Plataforma de deploy: [ ESCOLHER ]
  [ ] Vercel (Next.js serverless) ← CANDIDATO (melhor fit para Next.js)
  [x] Docker (container) ✅ CONFIRMADO (Dockerfile presente)
  [ ] Manual (scp, rsync, etc.)
  [ ] CI/CD (GitHub Actions, GitLab CI, etc.)
  [ ] Outro: [ ]

Evidence:
  • Dockerfile presente (53 linhas, multi-stage Alpine)
  • Node.js 20 Alpine base
  • Production-ready build pipeline
```

### Pipeline de Deploy

```
Build command: npm run build
Exemplo output de build: Next.js Turbopack
  → Build time: 11.6s deterministic ✓
  → Output: .next/ directory (optimized)

Test command: [ não configurado em v0.1 ]
Deploy command: 
  1. docker build -t console:v0.2 .
  2. docker push console:v0.2 (ou equivalente)
  3. kubectl/compose/manual deploy

Deploy location: [ TO BE DEFINED - staging/prod URL ]
```

### Infraestrutura Alvo

```
Server/Host: [ TO BE DEFINED ]
OS: Linux (Alpine em Docker)
Node.js version: 20 (Alpine)
Reverse proxy (nginx/Apache)?: [ TO BE CONFIRMED ]
```

---

## 🔗 Como Chama Backend

### Conexão de Rede

```
Backend roda onde?: [ TO BE DEFINED ]
  • URL base: https://api.techno-os.dev (assumed)
  • Porta: 443 (HTTPS assumed)

Como console chama backend?
  [x] HTTP direto (fetch/axios to backend API) ← ESPERADO para v0.2
  [ ] Proxy interno (http://localhost:3000/api → proxy → backend)
  [ ] GraphQL relay
  [ ] Outro: [ ]

Evidence:
  • lib/error-handling.ts presente (implementa ApiResponse com trace_id)
  • Pronto para integração fetch/axios v0.2
```

### Headers/Auth Padrão

```
Headers enviados por padrão?
  • Authorization: [ Será Bearer token (F2.3) ou X-API-Key (F2.1) em v0.2 ]
  • X-API-Key: [ Verificar em F2.1_INVENTORY ]
  • X-VERITTA-USER-ID: [ Mencionado no CONTRACT.md para F2.3 ]
  • User-Agent: next/16.1.1
  • Content-Type: application/json
  • Trace-ID: [ Será adicionado em v0.2 para observabilidade ]

Config de baseURL (em código):
  • Arquivo: [ app/ ou lib/ (a definir em PHASE 1) ]
  • Variável: NEXT_PUBLIC_API_BASE_URL (env var, será criada)
  • Valor (dev): http://localhost:8000 (assumido backend local)
  • Valor (prod): https://api.techno-os.dev (assumed)
```

---

## 🔐 Contexto de Segurança

### Storage Disponível (para tokens)

#### HttpOnly Cookies
```
Viável? [x] SIM ✅ CONFIRMADO
Por quê?: Next.js é server-side capable; httpOnly cookies são padrão enterprise
Exemplo de uso: res.setHeader('Set-Cookie', 'access_token=...;HttpOnly;Secure;SameSite=Strict')
```

#### localStorage / sessionStorage
```
Viável? [x] SIM (como fallback)
Risco XSS?: [ ALTO / MÉDIO / BAIXO ]
Mitigação XSS (CSP/sanitização)?: [ PRESENTE / AUSENTE / A IMPLEMENTAR ]
Nota: sessionStorage pode ser usado para metadata (auth_method, expiry) se HttpOnly não viável
```

#### Cookies Normais (sem HttpOnly)
```
Viável? [ ] NÃO RECOMENDADO
Diferença vs HttpOnly?: Acessível via JS (risco se XSS)
```

#### File System (se CLI/Desktop)
```
Viável? [ ] NÃO (Web app, não CLI/desktop)
```

### Política de CORS

```
Domínio console: localhost:3000 (dev) | https://console.techno-os.dev (prod, assumed)
Domínio backend: localhost:8000 (dev) | https://api.techno-os.dev (prod, assumed)
CORS habilitado?: [ SIM / NÃO ] ← TO BE CONFIRMED WITH BACKEND
Allowed origins: [ console.techno-os.dev ]
Allowed methods: [ GET, POST, PUT, DELETE, OPTIONS ]
```

### CSP Headers

```
Content-Security-Policy ativa?: [ NÃO (v0.1 não tem CSP, será adicionado em v0.2) ]
Valor futuro: [ script-src 'strict-dynamic' ; object-src 'none' ; ... ]
Permite inline scripts?: [ NÃO (v0.2 será strict) ]
Permite unsafe-eval?: [ NÃO ]
```

---

## 🎯 Implicações para v0.2

### Para SECURITY_DESIGN_v0.2.md

Com base nas respostas acima, o SECURITY_DESIGN será:

```
✅ Web app + HttpOnly viável:
   → Usar HttpOnly cookies (melhor prática)
   → Fallback: AES-encrypted sessionStorage se HttpOnly indisponível
   → CSP strict: script-src 'strict-dynamic' (previne inline XSS)
   
Recomendação:
   Access token → HttpOnly cookie (browser não lê via JS)
   Refresh token → localStorage (long-lived, necessário para refresh request)
   Metadata → sessionStorage (expiry time, auth method)
```

### Para DEPLOYMENT_STRATEGY_v0.2.md

Com base no deploy atual:

```
✅ Docker + Alpine:
   Feature flag via env var (NEXT_PUBLIC_ENABLE_F2_3)
   Rollback via docker rollout revert (rápido)
   Health check: GET /api/health (verificar F2.3 status)
   
Timeline:
   Build: ~15-30s (docker build)
   Push: ~30s (docker push)
   Deploy: ~1-2 min (rolling update)
   Total rollback: ~3-5 min (meta atingível)
```

---

## ✅ Checklist de Preenchimento

- [ ] Tipo de console identificado (web/CLI/desktop)
- [ ] URL/comando de execução documentado
- [ ] Plataforma de deploy confirmada
- [ ] Backend base URL confirmada
- [ ] Método de autenticação atual documentado (F2.1)
- [ ] Storage viável para tokens identificado
- [ ] CORS/CSP status documentado

---

## 📊 Tabela de Contexto

| Aspecto | Valor | Evidência |
|---------|-------|-----------|
| Tipo | [ ] | [ ] |
| Framework | [ ] | [ ] |
| Deploy | [ ] | [ ] |
| Backend URL | [ ] | [ ] |
| Storage (token) | [ ] | [ ] |
| XSS Risk | [ ] | [ ] |
| CORS | [ ] | [ ] |

---

## 🚀 Próxima Ação

1. Preencher template acima com fatos reais
2. Confirmar com Tech Lead/Arquiteto
3. Registrar em docs/CONSOLE_ARCHITECTURE.md
4. Gate 1.2 marcado como ✅ OK

---

**Console Architecture Document**

Criado: 4 janeiro 2026  
Responsável: Tech Lead / Arquiteto  
Status: TEMPLATE PRONTO
