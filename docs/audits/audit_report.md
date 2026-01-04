# AUDITORIA EXPLORATÓRIA DE WORKSPACE (PRÉ-HOUSEKEEPING GOVERNADO)

**Data da Análise:** Janeiro 1, 2026  
**Branch:** work/F9_5_2_edge_stack  
**Ferramentas Usadas:** list_dir, read_file, run_in_terminal (du -sh para tamanhos aproximados).  
**Disclaimer:** Em caso de dúvida, classificação como D — requer decisão humana. Foco em observação conservadora, sem ações.

## 1️⃣ INVENTÁRIO ESTRUTURAL

### 1.1 Lista dos diretórios e arquivos top-level do repositório
- Diretórios: .git/, .github/, .mypy_cache/, .pytest_cache/, .venv/, alembic/, app/, artifacts/, certs/, docs/, grafana/, nginx/, observability/, scripts/, tests/
- Arquivos: .dockerignore, .env, .env.example, .gitignore, Dockerfile, docker-compose.edge.yml, docker-compose.grafana.yml, docker-compose.metrics.yml, docker-compose.nginx.yml, docker-compose.yml, prometheus.yml, pytest.ini, requirements.txt, README.md, SEAL-F9.5.1.md, SEAL-F9.5.2.md, SEAL-F9.5.3.md, SEAL-F9.5.md, actions_fingerprint.lock, alembic.ini, alert.rules.yml, app.db, baseline_metrics.json, CONFORMIDADE_EXECUTION_SEMANTICS_V1.txt, EXECUTION_SEMANTICS_V1_NOTION_BACKEND.txt, FILE-INDEX.md
- Arquivos soltos (logs/scripts): ci_gate_*.log, contract_*.log, smoke_https_*.log, pytest-warnings*.log (múltiplos timestamps)

### 1.2 Destaque de itens não típicos de um backend versionado
- Caches: .mypy_cache/ (48M), .pytest_cache/ (44K) — outputs de lint/test.
- Outputs: app.db (36K) — database local.
- Logs espalhados: ci_gate_*.log, contract_*.log, smoke_https_*.log — parecem evidências de execuções.
- Arquivos de configuração temporária: .env (não versionado, mas presente).
- Artefatos históricos: SEAL-F9.*.md — selos de fases.

### 1.3 Sinalização de arquivos grandes fora de artifacts/
- .mypy_cache/: ~48M (cache de type-checking, grande).
- .venv/: ~158M (ambiente virtual, muito grande).
- app.db: ~36K (não grande, mas database local).
- Nenhum outro arquivo isolado grande detectado fora de artifacts/.

## 2️⃣ CLASSIFICAÇÃO POR TIPO (CRÍTICO)

### A — Canônico Git (deve permanecer versionado)
- docs/, scripts/, docker-compose*.yml, Dockerfile, requirements.txt, pytest.ini, alembic/, app/, tests/, .gitignore, README.md, .dockerignore, prometheus.yml, alert.rules.yml, baseline_metrics.json — configs, código, policies essenciais.
- Motivo: Definem o sistema; alinhados à Evidence Policy (canonical light evidence).

### B — Evidência Pesada / Regenerável (deve ficar fora do Git)
- artifacts/ (~676K) — logs, reports, checksums de execuções.
- Logs soltos: ci_gate_*.log, contract_*.log, smoke_https_*.log, pytest-warnings*.log — outputs de testes/contracts.
- Motivo: Regeneráveis via scripts; ignorados por .gitignore; pesados conforme policy.

### C — Temporário / Cache / Lixo Técnico (pode ser removido com segurança após registro)
- .mypy_cache/, .pytest_cache/ — caches de desenvolvimento.
- app.db — database local de dev/test.
- .env — configuração local (não versionada).
- actions_fingerprint.lock — possível lock de CI.
- Motivo: Não essenciais; regeneráveis; cobertos por .gitignore.

### D — Ambíguo / Risco de Exclusão (não tocar sem decisão humana)
- SEAL-F9.*.md — selos de fases; parecem históricos, mas podem ser evidência canônica.
- certs/ — certificados; verificar PII/LGPD.
- grafana/, nginx/, observability/ — sub-configs; confirmar se canônicos.
- Motivo: Potencial valor histórico/auditoria; dúvida sobre remoção.

## 3️⃣ FASES ANTERIORES

### 3.1 Artefatos de fases antigas
- Sim: f9_4_1/, f9_4_1_integral/, f9_5/, f9_5_1/, f9_5_2_edge/, f9_5_3_1_full_edge_gate/, f9_5_3_obs_edge/, f9_integral_pre_next/, archive/.

### 3.2 Localização
- Corretamente isolados em artifacts/.

### 3.3 Evidência histórica relevante
- Possivelmente sim: archive/ e f9_4_1* parecem históricos; não apagar sem arquivamento (ex.: CI artifacts externos).

## 4️⃣ ADERÊNCIA À GOVERNANÇA

### 4.1 Coerência com Evidence Policy
- Sim: artifacts/ ignorado; docs/ versionado; PII/redação mencionada (verificar logs por dados pessoais).

### 4.2 Cobertura do .gitignore
- Sim: artifacts/, *.log, caches (.mypy_cache/, .pytest_cache/), .venv/, app.db.

### 4.3 Risco de commit acidental
- Baixo: artifacts/ ignorado; logs soltos não estão em .gitignore (risco médio — podem ser committed se não atentos).

## 5️⃣ RISCOS E ALERTAS

### 5.1 Arquivos/diretórios que NÃO DEVEM ser removidos sem autorização
- docs/, scripts/, docker-compose*.yml, Dockerfile, app/, tests/, .gitignore, README.md — essenciais para repo.

### 5.2 Riscos de limpeza agressiva
- Apagar .mypy_cache/ pode quebrar lint local; app.db pode ter dados de teste.
- Logs soltos parecem lixo, mas são evidências — risco de perder rastreabilidade.

### 5.3 Quebra de rastreabilidade/auditoria
- Remover artifacts/ quebra auditoria de fases; selos SEAL-F9.* podem ser únicos.

## 6️⃣ PREPARAÇÃO PARA PRÓXIMA FASE

O workspace está apto para iniciar uma nova branch (ex.: stage/f9.6.1 ou stage/f9.7), desde que artifacts/ sejam preservados/arquivados externamente.

Existe algo que deveria ser resolvido: Resolver logs soltos (mover para artifacts/ ou ignorar explicitamente) e verificar PII em certs/logs para LGPD compliance.