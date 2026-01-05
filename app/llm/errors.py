"""LLM-specific exceptions (V-COF governed, fail-closed).

Exceções para componentes LLM do Techno OS:
- ConfigurationError: ENV inválidas, providers não configurados
- ProviderError: falhas de comunicação com provider externo
- PolicyViolation: request bloqueado por governança
- TimeoutError: (built-in) timeout de rede
"""

from __future__ import annotations


class ConfigurationError(Exception):
    """Erro de configuração LLM (ENV, allowlists, api_keys)."""

    pass


class ProviderError(Exception):
    """Erro de comunicação com provider externo (5xx, rede, etc)."""

    pass


class PolicyViolation(Exception):
    """Violação de política de governança (allowlist, modelo, timeout)."""

    pass
