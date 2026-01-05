# SEAL — F9.9-B (Gate Unblocked / VPS Sync)

Data: 2026-01-05
Escopo selado: Correção de blocker de gate (403 "Action not allowed in profile" / G8) causado por desync de versão na VPS.

1) Estado anterior (BLOCKER)
- /process action=llm_generate retornava 403 Forbidden
- Mensagem: "Action not allowed in profile"
- reason_codes: G8_UNKNOWN_FIELDS_PRESENT (bloqueio a nível de gate)

2) Correção executada (procedimento)
- Atualização do código na VPS: git pull --ff-only
- Rebuild/redeploy do serviço api via docker-compose build + up -d
- Remoção de container antigo/orfão (se aplicável) e subida limpa do api

3) Evidências
- artifacts/backend_llm_seal_v2/vps_health_after.json
- artifacts/backend_llm_seal_v2/vps_container_git_head.txt
- artifacts/backend_llm_seal_v2/local_git_head.txt
- artifacts/backend_llm_seal_v2/vps_action_matrix_excerpt.txt
- artifacts/backend_llm_seal_v2/probe_minimal_http_final.txt
- artifacts/backend_llm_seal_v2/metrics_llm_post_probe.txt
- artifacts/backend_llm_seal_v2/docker_logs_last_10m_tail.txt

4) Resultado
- Gate agora PERMITE llm_generate (403 removido).
- Request mínimo retorna HTTP 200/2xx e entra no executor.
- Falha remanescente observada: status FAILED com reason_codes=["EXECUTOR_EXCEPTION"] (não é gate). Esta falha NÃO está selada como "cutover funcional".

5) Itens explicitamente NÃO selados (pendente)
- OpenAI Cutover Funcional (SUCCESS do executor sem EXECUTOR_EXCEPTION)
- Preferências F9.9-A
- Console F10

Veredicto: SEALED (somente Gate Unblocked / VPS Sync).
