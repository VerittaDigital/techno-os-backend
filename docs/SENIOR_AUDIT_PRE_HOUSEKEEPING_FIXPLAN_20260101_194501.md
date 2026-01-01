# SENIOR AUDIT PRE-HOUSEKEEPING FIXPLAN

**Timestamp:** 20260101_194501  
**Disclaimer:** Foco em resolução conservadora; LGPD-by-design (sem exposição de conteúdo sensível). Em caso de dúvida: “Classificação incerta — requer decisão humana.”

## Estado Canônico Atual (TAG vs HEAD)
- Branch: work/F9_5_2_edge_stack
- HEAD: 1cd08c48b0b080209cf8556364091bbbd0df36c7 (F9.6.0: Enhance evidence policy with enterprise-grade details)
- Tag v0.1.0-f9.6.0: 34225de (F9.6.0 Post-GO Hardening Release)
- Diff --name-status: M docs/evidence_policy.md
- Status: ?? docs/SENIOR_AUDIT_PRE_HOUSEKEEPING_20260101_194047.md ?? scripts/f9_6_0_post_go_hardening.sh

**DECISÃO HUMANA NECESSÁRIA (escolher uma):**
(A) “O ponto canônico de limpeza deve ser a TAG v0.1.0-f9.6.0 e vamos criar branch a partir dela, ignorando o HEAD atual.”
(B) “O HEAD atual contém correções legítimas e deve virar o novo canônico: criar nova tag v0.1.0-f9.6.0+hotfix (ou v0.1.1) após commit governado.”
(C) “Reverter docs/evidence_policy.md do HEAD para ficar idêntico à TAG (sem criar nova tag).”

## Lista de Logs Soltos + Proposta .gitignore
**Contagem:** 50+ arquivos *.log fora de artifacts/.

**Lista (apenas nomes, sem conteúdo):** [Mesma da auditoria anterior: ci_gate_*.log, contract_*.log, smoke_https_*.log, pytest-warnings*.log, etc.]

**Proposta .gitignore (mínimo, sem executar ainda — aguardar [GITIGNORE AUTHORIZED]):**
```
# Evidence Policy — logs soltos
*.log
**/*.log
pytest-warnings*.log
ci_gate_*.log
contract_*.log
smoke_https_*.log
```

**Plano para fase destrutiva (não executar agora):** Criar artifacts/workspace_cleanup_<timestamp>/, mover logs soltos para lá, gerar manifesto + SHA256.

## Status actions_fingerprint.lock
**Referências encontradas:** Muitas em docs/archive/ (ex.: lock de ações governadas, fingerprinting para CI/CD, testes de drift). Função: lock de registry de ações, paralelo a profiles_fingerprint.lock.

**Classificação:** A (Canônico Git) — tem função clara em governança/drift detection.

**Pergunta de decisão humana:** “Devemos preservar este arquivo (A — canônico) até F9.6.1, ou isolá-lo em artifacts na limpeza?”

## Status certs/ (Metadados Apenas)
**Lista de arquivos:** certs/cert.pem, certs/key.pem, certs/nginx-selfsigned.crt, certs/nginx-selfsigned.key

**Metadados file:** PEM certificate (cert.pem, nginx-selfsigned.crt), ASCII text (key.pem, nginx-selfsigned.key)

**Classificação:** D — Sensível (presença de .key/.pem indica chaves privadas/certificados).

**Perguntas obrigatórias de decisão humana:**
“Esses certificados/chaves são apenas para DEV/LOCAL ou têm relação com produção?”
“Podemos remover do repo e manter apenas placeholders + docs?”
“Deseja mover o conteúdo real para armazenamento seguro fora do repo e manter no repo apenas: certs/README.md (instruções), placeholders (ex.: .pem.example)?”

## Checklist do que Falta para Ficar “APTO”
- [ ] Ponto canônico escolhido (A/B/C)
- [ ] Logs protegidos por .gitignore (após autorização)
- [ ] Decisão para certs/ (remover/placeholders)
- [ ] Decisão para actions_fingerprint.lock (preservar/isolamento)

## Veredicto Final
NÃO APTO (decisões humanas pendentes para canônico, certs/ e lock).