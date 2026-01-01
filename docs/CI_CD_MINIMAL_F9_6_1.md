# CI/CD Minimal F9.6.1

## Objetivo do CI/CD Minimal
Implementar pipeline de CI governado e minimalista para TECHNO-OS Backend, focado em validação precoce sem deploy automático. O pipeline executa apenas o gate mínimo (scripts/ci_gate.sh), falha em regressões, e coleta evidências pesadas como artifacts do GitHub Actions (fora do repositório Git).

## O que o Workflow Executa
- **Gate Mínimo:** scripts/ci_gate.sh (healthcheck via curl, sem iniciar serviços pesados).
- **Ambiente:** ENV=ci exportado.
- **Evidências:** Logs, HEAD commit, timestamp salvos em ci_artifacts/${{ github.run_id }}.
- **Triggers:** Push e PR para branches main e stage/*.
- **Fail-Closed:** Job falha se gate retornar !=0; artifacts sempre uploadados.

## Onde Ficam Evidências
- **Canônicas:** docs/ (auditorias, políticas).
- **Pesadas:** GitHub Actions artifacts (ci_artifacts_${{ github.run_id }}), não commitadas no Git. Baixe via GitHub UI após run.

## Como Rodar o Gate Localmente
1. Certifique-se de que o backend está rodando (ex.: docker-compose up).
2. Execute: `bash scripts/ci_gate.sh`
3. Logs salvos em artifacts/f9_5/ci_gate_<timestamp>.log.

## Regras de Governança
- **V-COF:** Human-in-the-loop; nenhum deploy automático.
- **Evidence Policy:** Artifacts/ ignorado; docs/ canônico.
- **LGPD-by-Design:** Não expor PII, certs, secrets. Máscara variáveis sensíveis.
- **Fail-Closed:** Abort em incompatibilidades (ex.: gate pesado).

## Limitações Conhecidas
- Docker em CI: Disponível, mas gate atual é minimal (curl-based).
- Timeout: 15 min por job.
- Concurrency: Runs paralelos cancelados em PRs.