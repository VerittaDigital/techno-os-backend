# 🎯 PLANO DE EXECUÇÃO — F-CONSOLE-0.1 PHASE 2
## Implementação de Contrato & Integração Backend

**Parecer do Arquiteto Backend:** ✅ **APTO PARA EXECUÇÃO**  
**Data:** 4 de janeiro de 2026  
**Framework:** F-CONSOLE-0.1  
**Status:** PRONTO PARA INICIO  

---

## 📊 VISÃO GERAL DO PLANO

| Etapa | Nome | Bloqueador? | Duração Est. | Entregáveis |
|-------|------|-------------|--------------|------------|
| 1 | Inventário de Contrato | ❌ Não | 2-4h | `console-inventory.md` |
| 2 | OpenAPI Skeleton v0.1 | ❌ Não | 4-6h | `openapi/console-v0.1.yaml` |
| 3 | CONTRACT.md | ❌ Não | 1-2h | `docs/CONTRACT.md` |
| 4 | ERROR_POLICY.md | ❌ Não | 2-3h | `docs/ERROR_POLICY.md` |
| 5 | Hardening de Segredos | ⚠️ Crítico | 1-2h | `.env.example`, `AUTH_MIGRATION.md` |
| 6 | Build Reprodutível | ❌ Não | 1h | `scripts/build.sh`, CI validation |

**Tempo total estimado:** 11-18 horas (1.5-2 dias)

---

## 🔹 ETAPA 1 — INVENTÁRIO DE CONTRATO (Evidence-Based)

**Objetivo:** Mapear exatamente o que o console usa hoje, sem suposições.

### Tarefas

#### 1.1 — Verificar endpoints realmente chamados
```bash
# Comando para executar
cd d:\Projects\techno-os-console

# Buscar chamadas fetch/axios
grep -r "fetch\|axios" src/ app/ components/ 2>/dev/null | \
  grep -E "(process|preferences|health|metrics|audit|sessions)" | \
  tee /tmp/endpoint-calls.txt
```

**O que procurar:**
- `fetch('http://...` ou `fetch('/api/...`
- `axios.get/post/put` de endpoints backend
- URLs configuráveis via ENV

**Saída esperada:** ~5-10 chamadas diferentes (ou menos)

#### 1.2 — Para cada endpoint encontrado, extrair:
- [ ] Método HTTP (GET/POST/PUT/DELETE)
- [ ] Headers usados (Authorization, X-API-Key, Content-Type, etc.)
- [ ] Payload / Query params (exemplo real)
- [ ] Shape da resposta (campos observados)
- [ ] Códigos de status possíveis
- [ ] Último uso (data aproximada ou "desconhecido")

#### 1.3 — Classificar endpoints
```
LEGACY:      Última chamada > 30 dias atrás OU código comentado
ACTIVE:      Chamadas recentes e funcionais (últimos 7 dias)
DEPRECATED:  Backend retorna 410 Gone ou similar
```

#### 1.4 — Se backend indisponível
- Extrair shape de tipos TypeScript (interfaces em `lib/types.ts` ou similar)
- Extrair de mocks em testes
- Marcar cada campo como:
  - `[OBSERVADO]` — visto em resposta real
  - `[INFERIDO]` — extraído de código estático

### Critério de Aceitação

✅ Arquivo `docs/console-inventory.md` criado com:
- [ ] Todos os endpoints encontrados documentados
- [ ] Cada endpoint tem: método, headers, request, response
- [ ] Classificação (LEGACY/ACTIVE/DEPRECATED) feita
- [ ] Campos marcados como OBSERVADO ou INFERIDO
- [ ] Data do inventário incluída

### Timeline
**Início:** Imediato  
**Fim esperado:** +2-4 horas  
**Critério de bloqueio:** Nenhum; procede mesmo com conhecimento incompleto

---

## 🔹 ETAPA 2 — OPENAPI SKELETON v0.1 (Contrato Congelado)

**Objetivo:** Criar a fonte de verdade do Console.

### Tarefas

#### 2.1 — Criar estrutura base
```bash
mkdir -p d:\Projects\techno-os-console\openapi
touch d:\Projects\techno-os-console\openapi\console-v0.1.yaml
```

#### 2.2 — Preencher o OpenAPI com base no inventário (Etapa 1)

**Template obrigatório:**
```yaml
openapi: 3.0.3
info:
  title: Verittà Techno OS — Console API
  version: 0.1.0
  description: |
    Contrato congelado entre Console e Backend.
    Qualquer mudança exige bump de versão e PR dedicado.

servers:
  - url: '{API_BASE_URL}'
    variables:
      API_BASE_URL:
        default: http://localhost:8000

paths:
  # Um bloco para cada endpoint do inventário
  /health:
    get:
      operationId: getHealth
      responses:
        '200':
          description: Health check
          content:
            application/json:
              schema:
                type: object
                required: [status]
                properties:
                  status:
                    type: string
                    enum: [ok]

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
  
  schemas:
    # Schemas referenciados nos paths
    ErrorResponse:
      type: object
      required: [error, message, trace_id]
      properties:
        error:
          type: string
        message:
          type: string
        trace_id:
          type: string
        reason_codes:
          type: array
          items:
            type: string
        httpStatus:
          type: integer
```

**Regras:**
- ❌ Não inventar campos
- ❌ Não "embelezar" schema
- ✅ Skeleton > completude
- ✅ Reflete exatamente o inventário

#### 2.3 — Validar OpenAPI

**Pré-requisito:**
```bash
# Instalar validador (se não houver)
npm install -g @apidevtools/swagger-cli  # Necessário apenas uma vez
```

**Validação:**
```bash
# Validar
swagger-cli validate openapi/console-v0.1.yaml
```

Esperado: `✓ Valid`

FAIL-CLOSED:
- Se comando não encontrado: executar `npm install -g @apidevtools/swagger-cli` primeiro
- Se validação falhar: corrigir sintaxe YAML; se exigir inventar campo → ABORTAR

#### 2.4 — Documentar no README

Adicionar ao `README.md`:
```markdown
## API Contract

The console contract is frozen in `openapi/console-v0.1.yaml`.

**Any change to the contract requires:**
1. Bump version in info.version
2. PR with label `contract-change`
3. Approval from backend architect

**View the contract:**
- Online: [ReDoc preview]
- Local: `openapi/console-v0.1.yaml`
```

### Critério de Aceitação

✅ Arquivo `openapi/console-v0.1.yaml` criado com:
- [ ] OpenAPI 3.0.3 sintaxe válida
- [ ] Todos os endpoints do inventário documentados
- [ ] Schemas explícitos para request/response
- [ ] Security schemes definidas (Bearer + X-API-Key)
- [ ] Validação passa (`swagger-cli validate`)
- [ ] README.md atualizado com referência ao contrato

### Timeline
**Início:** Após Etapa 1  
**Fim esperado:** +4-6 horas  
**Critério de bloqueio:** Nenhum; procede com skeleton mínimo

---

## 🔹 ETAPA 3 — CONTRACT.md (Regra de Jogo)

**Objetivo:** Deixar explícito que o contrato manda no código.

### Tarefas

#### 3.1 — Criar arquivo
```bash
touch d:\Projects\techno-os-console\docs\CONTRACT.md
```

#### 3.2 — Preencher com estrutura

```markdown
# Console API Contract v0.1

**Versão atual:** v0.1.0  
**Data:** 2026-01-04  
**Fonte de verdade:** openapi/console-v0.1.yaml  
**Status:** ESTÁVEL  

## Endpoints Estáveis

[Um bloco para cada endpoint, copiado do OpenAPI]

### GET /health
- **Status:** STABLE
- **Auth:** Nenhuma
- **Response:** `{ "status": "ok" }`

### GET /api/v1/preferences
- **Status:** STABLE (F9.9-A)
- **Auth:** F2.3 (Bearer + X-VERITTA-USER-ID)
- **Response:** PreferencesResponse (ver OpenAPI)

### POST /process [LEGACY]
- **Status:** LEGACY (F2.1 only)
- **Auth:** X-API-Key
- **Deprecation:** Use novos endpoints quando disponíveis

## Headers Obrigatórios por Auth

### F2.3 Auth (PREFERIDO)
\`\`\`
Authorization: Bearer <token>
X-VERITTA-USER-ID: u_<8chars>
\`\`\`

### F2.1 Auth (LEGACY)
\`\`\`
X-API-Key: <beta_key>
\`\`\`

## Campos Garantidos de Resposta

Toda resposta de erro DEVE conter:
- error (string)
- message (string)
- trace_id (string)
- httpStatus (integer)

## Regra de Versionamento

**Qualquer mudança neste contrato exige:**
1. Bump de versão (v0.1 → v0.2)
2. PR dedicado com label contract-change
3. Aprovação do arquiteto backend
4. Atualização do OpenAPI
5. Atualização deste documento

**Mudanças permitidas SEM bump:**
- Adição de campos opcionais (nullable)
- Correção de typos em descrições
- Exemplos adicionais

**Mudanças que EXIGEM bump:**
- Remoção de campos
- Mudança de tipo de campo
- Novo endpoint
- Mudança de mecanismo auth

## Histórico de Versões

| Versão | Data | Mudanças |
|--------|------|----------|
| 0.1.0 | 2026-01-04 | Release inicial, 6 endpoints |
```

#### 3.3 — Adicionar ao README

```markdown
## Contract Rules

The API contract is versioned separately. See [docs/CONTRACT.md](docs/CONTRACT.md).

**Key rule:** Contract changes require explicit version bump and approval.
```

### Critério de Aceitação

✅ Arquivo `docs/CONTRACT.md` criado com:
- [ ] Título e metadados (versão, data, fonte de verdade)
- [ ] Todos os endpoints listados com status (STABLE/LEGACY/DEPRECATED)
- [ ] Auth headers documentadas (F2.1 vs F2.3)
- [ ] Regra de versionamento explícita
- [ ] Histórico de versões iniciado

### Timeline
**Início:** Paralelo com Etapa 2 (não bloqueado)  
**Fim esperado:** +1-2 horas  
**Critério de bloqueio:** Nenhum

---

## 🔹 ETAPA 4 — ERROR_POLICY.md (Fail-Closed)

**Objetivo:** Impedir comportamento silencioso ou ambíguo no frontend.

### Nota Importante sobre trace_id

Antes de começar, determinar estado do trace_id no backend:
- **Se TODOS os endpoints retornam trace_id:** exigir em ERROR_POLICY.md e código
- **Se ALGUNS retornam:** documentar como nullable/optional; implementar fallback (operation_id ou timestamp)
- **Se NENHUM retorna:** não exigir trace_id; usar mecanismo alternativo (operation_id, request_id, logging estruturado)
- **Marcar cada caso:** [OBSERVADO] onde trace_id existe; [INFERIDO] onde proposto como fallback

Regra: **Nunca exigir campo que não é devolvido pelo backend.** Se houver discrepância, marcar em console-inventory.md e documentar em ERROR_POLICY.md.

### Tarefas

#### 4.1 — Criar arquivo
```bash
touch d:\Projects\techno-os-console\docs\ERROR_POLICY.md
```

#### 4.2 — Preencher com políticas

```markdown
# Console Error Policy (Fail-Closed)

**Princípio:** Todo erro deve ser visível ao desenvolvedor E ao usuário final.

**Lema:** "Quando em dúvida, BLOQUEIA."

## Bloqueios Obrigatórios

### Configuração
- ❌ Sem API_BASE_URL → erro explícito no console
- ❌ API_BASE_URL inválida (não http/https) → bloquear inicialização

### Resposta da API
- ❌ Resposta vazia → BLOCKED (mostrar erro "Empty response")
- ❌ Timeout > 15s → BLOCKED (mostrar erro "Request timeout")
- ❌ Status desconhecido → BLOCKED
- ❌ Falha de parse JSON → BLOCKED (mostrar erro de parse)

### Campos Obrigatórios de Erro
Se resposta não contiver trace_id:
- ⚠️ Mostrar aviso: "trace_id missing (cannot debug)"

## Tratamento Explícito por Status

### 401 / 403 (Autenticação/Autorização)
\`\`\`typescript
if (response.status === 401 || response.status === 403) {
  showError({
    title: "Autenticação necessária",
    message: error.message || "Credenciais inválidas",
    traceId: error.trace_id,
    action: "Fazer login novamente"
  });
}
\`\`\`

### 5xx (Erro do Servidor)
\`\`\`typescript
if (response.status >= 500) {
  showError({
    title: "Erro no servidor",
    message: error.message || "Erro interno",
    traceId: error.trace_id,
    action: "Tente novamente em alguns instantes"
  });
}
\`\`\`

### Network Error / Timeout
\`\`\`typescript
catch (error) {
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    showError({
      title: "Erro de conexão",
      message: "Não foi possível conectar ao servidor",
      action: "Verifique sua conexão"
    });
  }
  if (error.name === 'AbortError') {
    showError({
      title: "Request timeout",
      message: "O servidor demorou muito a responder",
      action: "Tente novamente"
    });
  }
}
\`\`\`

## Debug Mode (NODE_ENV=development)

Em desenvolvimento:
- ✅ Logar todas as requests no console
- ✅ Logar trace_id de todas as respostas
- ✅ Mostrar payload completo em erros
- ✅ Permitir inspect de network requests

Em produção:
- ❌ Nunca logar dados sensíveis (tokens, passwords, PII)
- ✅ Logar trace_id para debugging remoto

## Validação de Implementação

Antes de deploy, validar:
- [ ] Todos os fetch/axios tem try/catch
- [ ] Todos os catch loggam error.trace_id
- [ ] Nenhum erro é silencioso (console.log de erros)
- [ ] Timeout de 15s implementado em AbortController
```

#### 4.3 — Implementar validação no código

Criar `lib/error-handling.ts`:
```typescript
// Exemplo de implementação
export interface ApiError {
  error: string;
  message: string;
  trace_id: string;
  reason_codes?: string[];
  httpStatus?: number;
}

export function normalizeError(error: any): ApiError {
  // Se trace_id está faltando, isso é um erro serious
  if (!error.trace_id) {
    console.warn('⚠️ trace_id missing from error response', error);
  }
  
  return {
    error: error.error || 'UNKNOWN_ERROR',
    message: error.message || 'Unknown error occurred',
    trace_id: error.trace_id || 'MISSING_TRACE_ID',
    httpStatus: error.httpStatus || 500
  };
}

export async function fetchWithTimeout(
  url: string, 
  options: RequestInit = {}
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000); // 15 segundos
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    return response;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timeout after 15 seconds');
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
```

### Critério de Aceitação

✅ Arquivo `docs/ERROR_POLICY.md` criado com:
- [ ] Princípio de fail-closed documentado
- [ ] Bloqueios obrigatórios listados
- [ ] Tratamento por status HTTP explícito (401, 5xx, network)
- [ ] Debug mode vs produção diferenciado
- [ ] Validação checklist incluída

✅ Código implementado:
- [ ] `lib/error-handling.ts` criado com funções de normalize
- [ ] `fetchWithTimeout` com AbortController implementado
- [ ] Todos os fetch/axios calls usam estas funções

### Timeline
**Início:** Paralelo com Etapa 3  
**Fim esperado:** +2-3 horas  
**Critério de bloqueio:** Nenhum (procede com template mínimo)

---

## 🔹 ETAPA 5 — HARDENING DE SEGREDOS (Crítico)

⚠️ **Esta é a etapa mais crítica.** Pode bloquear build se mal executada.

**Objetivo:** Remover risco crítico de segurança.

### Tarefas Pré-Execução

#### 5.1 — Validação de contexto (Scan de Segredos)

**Padrões a buscar:**
- Principais: `API_KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `APIKEY`, `AUTH_*`, `X-API-Key`, `Authorization:`
- Stack-específicos: `NEXT_PUBLIC_*` (Next.js), `REACT_APP_*` (React), variáveis similares
- Use regex case-insensitive + revisão manual para evitar false positives

```bash
# Verificar se X-API-Key ou segredos ainda existem
cd d:\Projects\techno-os-console

# Buscar por padrões comuns de segredo
grep -r "X-API-Key\|NEXT_PUBLIC_API_KEY\|VERITTA_BETA_API_KEY\|PASSWORD\|SECRET" . \
  --exclude-dir=node_modules \
  --exclude-dir=.next \
  --exclude-dir=.git \
  --exclude=*.md \
  2>/dev/null | tee /tmp/secret-scan.txt

# Revisar resultado sem vazar valores
cat /tmp/secret-scan.txt  # Registrar APENAS local (arquivo/linha), não valores
```

**Importante:** Registrar apenas LOCALIZAÇÃO do possível segredo, nunca colar o valor.

**Se encontrado alguma coisa:**
1. ✅ Verificar quais endpoints usam
2. ✅ Confirmar se podem migrar para F2.3 (Bearer token)
3. Decisão:
   - **SE SIM → prosseguir com remoção (Etapa 5.2-5.4)**
   - **SE NÃO → documentar uso legacy e MANTER (Etapa 5.5)**

#### 5.2 — Se aprovada a remoção: Criar `.env.example`

```bash
# Copiar do .env.gated.local
cp .env.gated.local .env.example

# OU criar do zero
cat > .env.example << 'EOF'
# API Configuration
API_BASE_URL=http://localhost:8000

# Authentication
# Use Bearer token (F2.3) instead of X-API-Key
# NEXT_PUBLIC_API_KEY=  # REMOVIDO: usar Bearer token em .env.local

# User Context (F2.3)
# NEXT_PUBLIC_USER_ID=u_12345678  # Optional, set if available

# Development
NODE_ENV=development
DEBUG=1
EOF
```

**Regras:**
- ❌ Nenhum segredo em .env.example
- ✅ Apenas chaves com valores de exemplo
- ✅ Comentários explicando cada variável

#### 5.3 — Validar que .env.example está no Git

```bash
# Verificar .gitignore
cat .gitignore | grep -E "^\.env"

# Esperado: .env (local) deve estar ignorado, .env.example não
```

#### 5.4 — Implementar validação no código (fail-closed)

Criar ou atualizar `lib/config.ts`:

```typescript
export function validateConfig() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 
                     process.env.API_BASE_URL ||
                     process.env.REACT_APP_API_BASE_URL;
  
  if (!apiBaseUrl) {
    throw new Error(
      '❌ FATAL: API_BASE_URL not configured. ' +
      'Create .env.local and set API_BASE_URL=http://localhost:8000'
    );
  }
  
  // Validar URL é http/https
  if (!apiBaseUrl.startsWith('http://') && !apiBaseUrl.startsWith('https://')) {
    throw new Error(
      '❌ FATAL: API_BASE_URL must start with http:// or https://. ' +
      `Got: ${apiBaseUrl}`
    );
  }
  
  // Validação em produção: nunca usar NEXT_PUBLIC_API_KEY
  if (process.env.NODE_ENV === 'production' && 
      process.env.NEXT_PUBLIC_API_KEY) {
    throw new Error(
      '❌ FATAL: NEXT_PUBLIC_API_KEY não deve estar em produção. ' +
      'Use Bearer token (F2.3) no backend.'
    );
  }
  
  return { apiBaseUrl };
}
```

Chamar em `pages/_app.tsx` ou `app/layout.tsx`:
```typescript
import { validateConfig } from '@/lib/config';

// Validate before rendering anything
validateConfig();
```

#### 5.5 — Criar `docs/AUTH_MIGRATION.md` (em qualquer caso)

```markdown
# Authentication Migration Guide

**Status:** In progress  
**Target:** F2.3 (Bearer token) for all new endpoints  
**Legacy:** F2.1 (X-API-Key) still active for specific endpoints  

## Endpoints by Auth Type

### F2.3 (Bearer + X-VERITTA-USER-ID) — PREFERRED
- ✅ GET /health
- ✅ GET /api/v1/preferences
- ✅ PUT /api/v1/preferences

### F2.1 (X-API-Key) — LEGACY
- ⚠️ POST /process (use for now, plan migration)
- ⚠️ GET /api/admin/* (admin endpoints, no timeline)

## How to Migrate

### Step 1: Obtain Bearer Token
1. Login via OAuth or credential exchange
2. Receive token from backend
3. Store in sessionStorage (temporary) or secure cookie

### Step 2: Update Headers
\`\`\`typescript
const headers = {
  'Authorization': \`Bearer \${token}\`,
  'X-VERITTA-USER-ID': 'u_abc12345',
  'Content-Type': 'application/json'
};
\`\`\`

### Step 3: Remove X-API-Key
\`\`\`typescript
// ❌ OLD
const headers = { 'X-API-Key': process.env.NEXT_PUBLIC_API_KEY };

// ✅ NEW
const headers = { 'Authorization': \`Bearer \${token}\` };
\`\`\`

## Timeline

- [x] Audit: Identify all X-API-Key usage
- [ ] Phase 1: Migrate GET /api/v1/preferences (2026-01-15)
- [ ] Phase 2: Migrate PUT /api/v1/preferences (2026-01-22)
- [ ] Phase 3: Plan /process migration (2026-02-01)
- [ ] Phase 4: Remove X-API-Key from production builds (2026-03-01)

## Fallback Strategy

If F2.3 not available:
- Use F2.1 (X-API-Key) temporarily
- Log warning in console
- Create issue to track migration
- Never ship to production with X-API-Key
```

### Critério de Aceitação

✅ Segurança validada:
- [ ] Grep search executado, resultado documentado
- [ ] Decisão de remover/manter registrada com justificativa
- [ ] Se remover: `.env.example` criado (SEM segredos)
- [ ] Se remover: validação em código implementada (fail-closed)
- [ ] `docs/AUTH_MIGRATION.md` criado em qualquer caso
- [ ] `.env.local` NÃO está no Git (.gitignore respeitado)

### Timeline
**Início:** Após Etapa 4 (pode ser paralelo)  
**Fim esperado:** +1-2 horas  
**⚠️ Critério de bloqueio:** SIM — Falhar se encontrar segredos em commits

---

## 🔹 ETAPA 6 — BUILD REPRODUTÍVEL

**Objetivo:** Evitar "funciona na minha máquina".

### Tarefas

#### 6.1 — Criar script de build com versionamento

```bash
# scripts/build.sh (ou .ps1 para Windows)
#!/bin/bash

set -e  # Exit on error

COMMIT_HASH=$(git rev-parse --short HEAD)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VERSION=$(jq -r '.version' package.json)

echo "🔨 Building console v${VERSION}-${COMMIT_HASH}"

# Validate config before build
npm run validate:config

# Build
npm run build

# Tag image
DOCKER_IMAGE="techno-os-console:v${VERSION}-${COMMIT_HASH}"
docker build -t ${DOCKER_IMAGE} .

echo "✅ Build complete: ${DOCKER_IMAGE}"
echo "📦 Commit: ${COMMIT_HASH}"
echo "📅 Date: ${BUILD_DATE}"
```

#### 6.2 — Adicionar validação em CI/CD

No `.github/workflows/build.yml` (ou equivalente):

```yaml
name: Build & Validate

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check for secrets
        run: |
          # ❌ FAIL se encontrar segredos no código
          if grep -r "NEXT_PUBLIC_API_KEY\|VERITTA_BETA" src/ app/; then
            echo "❌ FATAL: Secrets found in code"
            exit 1
          fi
      
      - name: Validate config
        run: npm run validate:config
      
      - name: Build
        run: npm run build
      
      - name: Check for hardcoded API_BASE_URL
        run: |
          # ❌ FAIL se encontrar URL hardcoded no bundle
          if grep -r "http://localhost:8000\|https://prod.example" .next/; then
            echo "❌ FATAL: Hardcoded API_BASE_URL found in bundle"
            exit 1
          fi
      
      - name: Docker build
        run: docker build -t techno-os-console:test .
      
      - name: Validate image
        run: |
          docker run --rm techno-os-console:test npm --version
```

#### 6.3 — Documentar procedimentos

Adicionar ao `BUILDING.md`:

```markdown
## Reproducible Builds

### Prerequisites
- Node.js v20+
- Docker
- Git (for commit hash)

### Build Locally

\`\`\`bash
# 1. Install dependencies
npm install --legacy-peer-deps

# 2. Run validation
npm run validate:config

# 3. Build
npm run build

# 4. Verify .next/standalone exists
ls -la .next/standalone/

# 5. Build Docker image
COMMIT=$(git rev-parse --short HEAD)
docker build -t techno-os-console:v0.1-${COMMIT} .

# 6. Verify image
docker run --rm techno-os-console:v0.1-${COMMIT} npm --version
\`\`\`

### CI/CD Requirements

The build MUST fail if:
- [ ] Secrets found in code (NEXT_PUBLIC_API_KEY, etc.)
- [ ] API_BASE_URL hardcoded in bundle
- [ ] NODE_ENV=production with debug flags

The build MUST produce:
- [ ] Deterministic .next/standalone/
- [ ] Docker image tagged with commit hash
- [ ] Build log with all validation passes
```

### Critério de Aceitação

✅ Build scripts criados:
- [ ] `scripts/build.sh` com versionamento de commit
- [ ] CI/CD workflow com validação de segredos
- [ ] Validação falha se segredos encontrados
- [ ] Validação falha se URL hardcoded no bundle

✅ Documentação atualizada:
- [ ] BUILDING.md com procedimentos de build
- [ ] Requisitos pré-build (Node, Docker, Git)
- [ ] Checklist de validação incluso

### Timeline
**Início:** Paralelo com Etapa 5  
**Fim esperado:** +1 hora  
**Critério de bloqueio:** Nenhum (procede sem CI se necessário)

---

## 📋 PRÉ-REQUISITOS (Antes de Iniciar Execução)

Verificar se TODAS as respostas são SIM. Se qualquer uma for NÃO, parar e reportar:

- [ ] Acesso ao repositório console (git clone + permissão escrita)?
- [ ] Stack do console identificável (Next.js, React, Node.js)?
- [ ] Backend API acessível OU documentação de endpoints disponível?
- [ ] Git + Node.js + npm instalados e funcionando?
- [ ] Permissão para criar branches, commits e PRs?

**Se qualquer item for NÃO: NÃO PROCEDER.** Reportar ao Arquiteto Técnico e aguardar resolução.

---

## 📋 CHECK FINAL (Auto-Avaliação)

Após completar Etapas 1-6, responder **SIM/NÃO** para cada pergunta:

- [ ] O console consegue ser desenvolvido sem backend rodando? (com mocks/tipos)
- [ ] O contrato está explícito e versionado? (OpenAPI + CONTRACT.md)
- [ ] Não há segredos no bundle? (validação em build + scan concluído)
- [ ] Erros são visíveis e rastreáveis? (ERROR_POLICY.md + implementação)
- [ ] Qualquer mudança futura exigirá decisão consciente? (versionamento explícito)

**Resultado esperado:** 5/5 SIM

**⚠️ Se qualquer resposta for NÃO, não proceder para integração até resolver.**
**⚠️ Se houver bloqueador não documentado, registrar em LINKAGE...md (seção discrepâncias).**

---

## 🎯 SEQUÊNCIA RECOMENDADA DE EXECUÇÃO

```
DIA 1 (4-6 horas):
├─ Etapa 1 (Inventário) ..................... 2-4h
└─ Etapa 2 (OpenAPI Skeleton) ............... 4-6h (pode iniciar ao 50% da Etapa 1)

DIA 2 (5-6 horas):
├─ Etapa 3 (CONTRACT.md) .................... 1-2h (paralelo com 4 e 5)
├─ Etapa 4 (ERROR_POLICY.md) ................ 2-3h (paralelo com 3 e 5)
├─ Etapa 5 (Hardening Segredos) ............ 1-2h (paralelo com 3 e 4, CRÍTICO)
└─ Etapa 6 (Build Reprodutível) ............ 1-1.5h (paralelo com 5)

CHECK FINAL:
└─ Auto-avaliação (ver acima) ............... 30min

TOTAL: ~11-18 horas (1.5-2.5 dias com 1 pessoa)
```

---

## 📊 MATRIZ DE RESPONSABILIDADES

| Etapa | Owner | Revisor | Bloqueador |
|-------|-------|---------|-----------|
| 1 (Inventário) | Dev Console | Arquiteto Backend | ❌ Não |
| 2 (OpenAPI) | Dev Console | Arquiteto Backend | ❌ Não |
| 3 (CONTRACT.md) | Dev Console | Arquiteto Backend | ❌ Não |
| 4 (ERROR_POLICY) | Dev Console | Líder Tech | ❌ Não |
| 5 (Hardening) | DevOps/Dev | Líder Security | ⚠️ SIM |
| 6 (Build) | DevOps/Dev | Líder Tech | ❌ Não |
| CHECK FINAL | Dev Console | Arquiteto Backend | ⚠️ SIM |

---

## 🚀 CRITÉRIOS DE SUCESSO GERAL

Projeto **SUCESSO** quando:

✅ Todos os 6 documentos criados:
- openapi/console-v0.1.yaml
- docs/console-inventory.md
- docs/CONTRACT.md
- docs/ERROR_POLICY.md
- docs/AUTH_MIGRATION.md
- scripts/build.sh

✅ Código implementado:
- lib/error-handling.ts
- lib/config.ts (validação)
- lib/fetch-with-timeout.ts

✅ Validações passando:
- swagger-cli validate openapi/console-v0.1.yaml ✅
- npm run build ✅
- npm run validate:config ✅
- docker build . ✅

✅ Check final respondendo SIM para todas as perguntas

✅ Nenhum segredo no bundle

**Quando tudo acima estiver feito: Console está APTO para integração com backend.**

---

## ⚠️ OBSERVAÇÕES CRÍTICAS

1. **Etapa 5 é crítica:** Se segredos forem encontrados, o build DEVE falhar
2. **Não pule a validação:** Use os scripts de CI/CD mesmo em desenvolvimento
3. **Documento é contrato:** O OpenAPI é a fonte de verdade, não o código
4. **Versionamento obrigatório:** Qualquer mudança no contrato = nova versão
5. **Fail-closed over silence:** Prefira bloquear a deixar passar silenciosamente

---

## 📞 ESCALAÇÃO

Se durante execução você encontrar:

- **Conflito de contrato:** Contactar Arquiteto Backend
- **Segredos em bundle:** Parar build, contactar Líder Security
- **Dúvida de auth (F2.1 vs F2.3):** Consultar docs/AUTH_MIGRATION.md
- **Erro de OpenAPI validation:** Usar swagger-editor.io para debug

---

**Versão:** 1.0  
**Data:** 4 de janeiro de 2026  
**Framework:** F-CONSOLE-0.1 Phase 2  
**Status:** ✅ PRONTO PARA EXECUÇÃO

**"Velocidade sem contrato gera retrabalho.  
Contrato sólido permite paralelização segura."** 🚀
