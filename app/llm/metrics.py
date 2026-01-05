"""LLM Observability Metrics (F9.9-B Prometheus integration).

Métricas Prometheus para LLM calls:
- llm_request_latency_seconds: Histogram de latência (p50, p95, p99)
- llm_tokens_total: Counter de tokens consumidos
- llm_errors_total: Counter de erros por tipo
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

# F9.9-B: Métricas LLM obrigatórias

# Latência de requests (histogram para percentis)
llm_request_latency_seconds = Histogram(
    "llm_request_latency_seconds",
    "LLM request latency in seconds",
    labelnames=["provider", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

# Tokens consumidos (counter acumulativo)
llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total LLM tokens consumed",
    labelnames=["provider", "model", "type"],  # type: prompt, completion
)

# Erros LLM (counter por tipo de erro)
llm_errors_total = Counter(
    "llm_errors_total",
    "Total LLM errors",
    labelnames=["provider", "error_type"],  # error_type: timeout, provider_error, etc
)
