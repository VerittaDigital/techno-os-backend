# F9.5.3 — OBS EDGE — PROMETHEUS FULL CONTRACT

## Objetivo
Adicionar Prometheus ao stack edge, acessível via /prometheus/ HTTPS, com contract_obs.sh compatível.

## Critérios GO
- https://localhost/health → 200
- https://localhost/grafana/ → 401
- https://localhost/prometheus/-/ready → 200
- Prometheus target techno-os-api UP
- contract_obs.sh PASS (EDGE-ready)
- ci_gate.sh PASS (BASE_URL=https://localhost)

## Endpoints Definitivos
- /health: API health
- /grafana/: Grafana sub-path (auth required)
- /prometheus/: Prometheus sub-path (no auth for contracts)

## Configs
- prometheus.yml: scrape api:8000 /metrics
- nginx.conf: proxy /prometheus/ → prometheus:9090
- contract_obs.sh: PROM_BASE_URL auto-detect (EDGE preferred)

## Troubleshooting
- 502 /prometheus/: check prometheus logs, rede (techno-network)
- target down: verify /metrics exposto, IP resolvendo
- contract fail: check PROM_BASE_URL fallback

## Rollback
git revert <hashes> --no-edit
docker compose -f docker-compose.yml -f docker-compose.edge.yml down --remove-orphans