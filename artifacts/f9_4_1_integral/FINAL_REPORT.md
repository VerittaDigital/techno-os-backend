# F9.4.1 — INTEGRAL TEST REPORT

## HEAD
30ba49ea1a0c7dd711e9a737463968f75a9ac46c

## PYTEST
........................................................................ [ 19%]
.........................s..s........................................... [ 38%]
.....................s.s..ss............................................ [ 57%]
........................................................................ [ 77%]
........................................................................ [ 96%]
..ss.s.s.s...s                                                           [100%]
=============================== warnings summary ===============================
tests/test_agentic_pipeline_tracing.py::TestAgenticPipelineSemanticInvariance::test_pipeline_result_identical_with_without_tracing
tests/test_agentic_pipeline_tracing.py::TestAgenticPipelineSemanticInvariance::test_pipeline_blocked_result_identical_with_without_tracing
tests/test_executor_tracing.py::TestExecutorSemanticInvariance::test_llm_executor_result_identical_with_without_tracing
tests/test_executor_tracing.py::TestExecutorSemanticInvariance::test_noop_executor_result_identical_with_without_tracing
  /mnt/d/Projects/techno-os-backend/app/tracing.py:59: DeprecationWarning: Call to deprecated method __init__. (Since v1.35, the Jaeger supports OTLP natively. Please use the OTLP exporter instead. Support for this exporter will end July 2023.) -- Deprecated since version 1.16.0.
    jaeger_exporter = JaegerExporter(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/test_agentic_pipeline_tracing.py:36: Tracing dependencies not available
SKIPPED [1] tests/test_agentic_pipeline_tracing.py:145: Tracing dependencies not available
SKIPPED [1] tests/test_executor_tracing.py:42: Tracing dependencies not available
SKIPPED [1] tests/test_executor_tracing.py:99: Tracing dependencies not available
SKIPPED [1] tests/test_executor_tracing.py:203: Tracing dependencies not available
SKIPPED [1] tests/test_executor_tracing.py:233: Tracing dependencies not available
SKIPPED [1] tests/test_tracing.py:25: Tracing dependencies not available
SKIPPED [1] tests/test_tracing.py:43: Tracing dependencies not available
SKIPPED [1] tests/test_tracing.py:70: Tracing dependencies not available
SKIPPED [1] tests/test_tracing.py:98: Tracing dependencies not available
SKIPPED [1] tests/test_tracing_integration.py:29: Tracing dependencies not available
SKIPPED [1] tests/test_tracing_integration.py:123: Tracing dependencies not available
362 passed, 12 skipped, 4 warnings in 10.73s

## FLAKE8 CRITICAL
0

## MYPY COUNT
73

## SMOKE HTTPS
🚀 Iniciando Smoke Tests HTTPS (BASE_URL: https://localhost)...
Precheck: Conectividade https://localhost/health
✅ Precheck OK
Teste 1: /health via HTTPS
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0100    15  100    15    0     0   1187      0 --:--:-- --:--:-- --:--:--  1250
{"status":"ok"}✅ /health OK
Teste 2: Endpoint raiz sem auth
HTTP/2 401 
server: nginx/1.29.4
date: Thu, 01 Jan 2026 15:26:21 GMT
content-type: text/html
content-length: 179
www-authenticate: Basic realm="Techno OS API"
strict-transport-security: max-age=31536000; includeSubDomains
x-frame-options: SAMEORIGIN
x-content-type-options: nosniff

✅ Endpoint protegido (401/403 esperado)
Teste 3: Endpoint raiz com auth
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0100    15  100    15    0     0    925      0 --:--:-- --:--:-- --:--:--   937
{"status":"ok"}✅ Auth OK
Teste 4: Grafana HTTPS e login
✅ Grafana requer login (redirect/401)
🎉 Smoke Tests HTTPS PASS (todos testes OK)
Logs salvos em: smoke_https_20260101_122621.log

## CONTRACT OBS
🔍 Iniciando Contract Tests Observabilidade (BASE_URL: https://localhost)...
Precheck: Conectividade https://localhost/health
✅ Precheck OK
Teste 1: Prometheus targets UP
✅ Targets essenciais UP
Teste 2: Prometheus rules OK
✅ Rules carregadas sem erro
Teste 3: Alerting rules presentes
✅ Alerting rules presentes (5)
Teste 4: Grafana datasource
✅ Grafana datasource acessível (requer auth)
🎉 Contract Tests Observabilidade PASS
Logs salvos em: contract_obs_20260101_122638.log

## CONTRACT SEC
🔒 Iniciando Contract Tests Segurança (BASE_URL: https://localhost)...
Precheck: Conectividade https://localhost/health
✅ Precheck OK
Teste 1: HTTP redireciona para HTTPS
✅ HTTP redireciona para HTTPS
Teste 2: Backend via proxy
✅ Backend acessível via proxy
Teste 3: /metrics acesso controlado
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0100  1904  100  1904    0     0   127k      0 --:--:-- --:--:-- --:--:--  132k
✅ /metrics acessível via proxy
Teste 4: Endpoints sensíveis protegidos
✅ Endpoints protegidos (contrato F9.2)
🎉 Contract Tests Segurança PASS
Logs salvos em: contract_sec_20260101_122658.log

## ARTIFACTS
total 48
drwxrwxrwx 1 vinicius vinicius  4096 Jan  1  2026 .
drwxrwxrwx 1 vinicius vinicius  4096 Jan  1 12:21 ..
-rwxrwxrwx 1 vinicius vinicius  5491 Jan  1  2026 FINAL_REPORT.md
-rwxrwxrwx 1 vinicius vinicius     0 Jan  1 12:27 bandit_presence.txt
-rwxrwxrwx 1 vinicius vinicius   493 Jan  1 12:26 contract_obs.txt
-rwxrwxrwx 1 vinicius vinicius   822 Jan  1 12:26 contract_sec.txt
-rwxrwxrwx 1 vinicius vinicius     2 Jan  1 12:24 flake8_critical.txt
-rwxrwxrwx 1 vinicius vinicius     0 Jan  1 12:25 flake8_tests_f401.txt
-rwxrwxrwx 1 vinicius vinicius    41 Jan  1 12:21 git_head.txt
-rwxrwxrwx 1 vinicius vinicius   788 Jan  1 12:21 git_log_10.txt
-rwxrwxrwx 1 vinicius vinicius    54 Jan  1 12:22 git_status_porcelain.txt
-rwxrwxrwx 1 vinicius vinicius     3 Jan  1 12:25 mypy_error_count.txt
-rwxrwxrwx 1 vinicius vinicius 14906 Jan  1 12:25 mypy_full.txt
-rwxrwxrwx 1 vinicius vinicius   737 Jan  1 12:23 pip_freeze_relevant.txt
-rwxrwxrwx 1 vinicius vinicius    14 Jan  1 12:27 pytest_cov_available.txt
-rwxrwxrwx 1 vinicius vinicius  2564 Jan  1 12:24 pytest_full.txt
-rwxrwxrwx 1 vinicius vinicius    15 Jan  1 12:23 python_version.txt
-rwxrwxrwx 1 vinicius vinicius   729 Jan  1 12:26 scripts_ls.txt
-rwxrwxrwx 1 vinicius vinicius  1413 Jan  1 12:26 smoke_https.txt
