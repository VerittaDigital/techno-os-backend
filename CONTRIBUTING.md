# 🤝 Contributing to Techno OS Backend

Bem-vindo ao Techno OS Backend. Este guia orienta novos arquitetos e desenvolvedores sobre como contribuir seguindo governança V-COF (Veritta Code of Conduct Framework).

---

## 📋 Pré-requisitos

### Ambiente Local
- **Python:** 3.11+
- **PostgreSQL:** 15+
- **Docker + Docker Compose:** Para observability stack
- **Git:** Com convenções de commit (conventional commits)

### Configuração Inicial
```bash
# Clone o repositório
git clone https://github.com/VerittaDigital/techno-os-backend.git
cd techno-os-backend

# Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais locais

# Execute migrations
alembic upgrade head

# Execute testes
pytest
```

---

## 🏛️ Arquitetura e Convenções

### Separação de Responsabilidades
- **app/**: Código fonte da API (FastAPI)
- **tests/**: Testes automatizados (pytest)
- **docs/**: Documentação técnica e decisões arquiteturais
- **sessions/**: SEAL documents (histórico de sessões — **READ-ONLY**)
- **artifacts/**: Evidências de implementação (logs, configs)
- **planning/**: Roadmap e planejamento de fases

### Governança V-COF (Obrigatória)
1. **IA como instrumento** — Copilot auxilia, humano decide
2. **Human-in-the-loop** — Revisão obrigatória antes de deploy
3. **Evidence-based execution** — Coletar evidências em `artifacts/`
4. **Fail-closed enforcement** — Abortar se pré-condições falharem
5. **LGPD by design** — Não armazenar PII sem consentimento

**Leia:** [`.github/copilot-instructions.md`](.github/copilot-instructions.md) para detalhes completos.

---

## 🔀 Fluxo de Trabalho Git

### Convenções de Branch
- `main` — Produção (protegida, somente via PR)
- `stage/*` — Branches de desenvolvimento de fases
- `feature/*` — Novas funcionalidades
- `fix/*` — Correções de bugs
- `chore/*` — Tarefas de manutenção (docs, refactor)

### Conventional Commits (Obrigatório)
Formato: `<tipo>(<escopo>): <descrição curta>`

**Tipos:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Apenas documentação
- `chore`: Manutenção (refactor, cleanup)
- `test`: Testes
- `ci`: CI/CD
- `perf`: Performance
- `security`: Segurança

**Exemplos:**
```
feat(llm): add timeout and retry logic to LLM client
fix(api): handle empty response from LLM provider
docs(architecture): update ADR-003 with circuit breaker pattern
chore(workspace): reorganize SEAL documents to sessions/
security(auth): implement rate limiting on API endpoints
```

### Pull Requests
1. Crie branch a partir de `stage/*` ou `main`
2. Commits pequenos e focados (atomic commits)
3. Testes passando (`pytest`)
4. PR description clara (o quê, por quê, como validar)
5. Self-review antes de solicitar review
6. Aguardar aprovação de Tech Lead
7. Merge com `--no-ff` (preservar histórico)

---

## 📝 SEAL Documents (Governança)

### ⚠️ IMPORTANTE: SEAL Documents são READ-ONLY

SEALs (Session Evidence and Audit Logs) são registros imutáveis de sessões de trabalho.

**NUNCA edite um SEAL existente.**

Se precisar corrigir ou atualizar:
1. Crie novo SEAL com sufixo `-v1.1`, `-v1.2`, etc.
2. Referencie o SEAL original no novo documento
3. Documente o motivo da correção no novo SEAL

**Localização:** `/sessions/`  
**Formato:** `SEAL-[FASE]-[DESCRIÇÃO].md`

**Consulta de Estado Atual:**
1. Leia: `/sessions/consolidation/SEAL-SESSION-[DATA]-*.md` (último snapshot)
2. Leia: `/planning/ROADMAP.md` (próximas fases)
3. Leia: `/ARCHITECTURE.md` (visão geral)

---

## 🧪 Testes e Validação

### Executar Testes Localmente
```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/test_llm_client.py -v

# Testes de integração
pytest -m integration
```

### Antes de Commitar
```bash
# 1. Testes passando
pytest

# 2. Linting (se configurado)
flake8 app/

# 3. Type checking (se configurado)
mypy app/

# 4. Git status limpo
git status
```

---

## 📦 Artifacts e Evidências

### Política de Evidências
Ao implementar uma fase crítica, coletar evidências em `/artifacts/`:

```bash
# Criar diretório de evidências
mkdir -p artifacts/[fase]_[descrição]_$(date +%Y%m%d_%H%M%S)

# Coletar logs, configs, outputs
docker logs techno-grafana > artifacts/[fase]/grafana_logs.txt
curl -I https://api.example.com > artifacts/[fase]/health_check.txt

# Criar checksum
cd artifacts/[fase]
sha256sum *.txt *.log > checksums.sha256
```

**Retenção:** 90 dias (ver `artifacts/README.md`)

---

## 🚀 Deploy e Observability

### VPS Production
- **Host:** 72.61.219.157 (Ubuntu 24.04 LTS)
- **User:** `deploy` (SSH key only)
- **Stack:** Docker Compose (FastAPI + PostgreSQL + Prometheus + Grafana)

### Monitoramento
- **Prometheus:** https://prometheus.verittadigital.com (Basic Auth)
- **Grafana:** https://grafana.verittadigital.com (TLS)

### Disaster Recovery
Procedimentos de rollback: `/docs/operations/DISASTER_RECOVERY.md`

---

## 🐛 Reportar Bugs

1. Verificar se já existe issue no GitHub
2. Criar issue com template:
   - **Descrição:** O que aconteceu
   - **Esperado:** O que deveria acontecer
   - **Reprodução:** Passos para reproduzir
   - **Ambiente:** Local/staging/production
   - **Logs:** Anexar logs relevantes

---

## 💬 Comunicação e Dúvidas

### GitHub Copilot
Este projeto utiliza GitHub Copilot como assistente de desenvolvimento.

**Como interagir com Copilot:**
- Copilot segue governança V-COF (ver `.github/copilot-instructions.md`)
- Sempre revise código gerado antes de commitar
- Copilot **não decide sozinho** — human-in-the-loop obrigatório

### Canais de Comunicação
- **GitHub Issues:** Bugs e feature requests
- **GitHub Discussions:** Dúvidas e propostas
- **Pull Requests:** Code review e discussão técnica

---

## 📚 Recursos Adicionais

- **Arquitetura:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Roadmap:** [planning/ROADMAP.md](planning/ROADMAP.md)
- **Governança V-COF:** [.github/copilot-instructions.md](.github/copilot-instructions.md)
- **SEAL Sessions:** [sessions/](sessions/)
- **Documentação Técnica:** [docs/](docs/)

---

## ✅ Checklist do Novo Contribuidor

Antes do primeiro PR:
- [ ] Ambiente local configurado e testável
- [ ] Li ARCHITECTURE.md (entendo a arquitetura)
- [ ] Li `.github/copilot-instructions.md` (entendo governança V-COF)
- [ ] Li sessions/consolidation/SEAL-SESSION-*.md (entendo estado atual)
- [ ] Configurei Git com conventional commits
- [ ] Executei testes localmente (`pytest`)
- [ ] Entendo que SEALs são read-only
- [ ] Sei como criar artifacts/ e coletar evidências

**Bem-vindo ao time! 🚀**

---

**Documento criado:** 2026-01-03  
**Versão:** 1.0  
**Governança:** V-COF compliant
