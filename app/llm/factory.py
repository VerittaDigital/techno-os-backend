"""LLM Client Factory (V-COF governed, fail-closed).

F9.9-B: Factory endurecida com allowlists obrigatórias e fail-closed.
"""

import os
from typing import Optional

from .client import LLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .gemini_client import GeminiClient
from .grok_client import GrokClient
from .deepseek_client import DeepSeekClient
from .fake_client import FakeLLMClient
from .errors import ConfigurationError


def create_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout_s: float = 30.0,
) -> LLMClient:
    """
    Factory para criar LLM client baseado em provider (fail-closed).
    
    F9.9-B: Implementa allowlist obrigatória de providers via ENV.
    Se VERITTA_LLM_ALLOWED_PROVIDERS não configurado: ConfigurationError.
    Se provider não estiver na allowlist: ConfigurationError.
    
    Args:
        provider: "openai", "anthropic", "gemini", "grok", "deepseek", "fake"
        api_key: API key do provider ou None (usa env)
        timeout_s: Timeout padrão (default 30s conforme F9.9-B)
        
    Returns:
        LLMClient instance
        
    Raises:
        ConfigurationError: ENV ausente, provider bloqueado, api_key ausente
    """
    # F9.9-B: Validar allowlist obrigatória (fail-closed)
    allowed_providers_raw = os.getenv("VERITTA_LLM_ALLOWED_PROVIDERS")
    if not allowed_providers_raw:
        raise ConfigurationError("VERITTA_LLM_ALLOWED_PROVIDERS not configured (fail-closed)")
    
    allowed_providers = [p.strip().lower() for p in allowed_providers_raw.split(",") if p.strip()]
    if not allowed_providers:
        raise ConfigurationError("VERITTA_LLM_ALLOWED_PROVIDERS is empty (fail-closed)")
    
    # Detectar provider via env se não fornecido
    provider = provider or os.getenv("LLM_PROVIDER", "fake")
    provider = provider.lower()
    
    # Validar provider contra allowlist (fail-closed)
    if provider not in allowed_providers:
        raise ConfigurationError(
            f"Provider '{provider}' not in allowlist {allowed_providers} (fail-closed)"
        )
    
    # Fake client para desenvolvimento/testes
    if provider == "fake":
        return FakeLLMClient()
    
    # Resolver API key por provider
    if api_key is None:
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "grok": "XAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        env_var = key_map.get(provider)
        if not env_var:
            raise ConfigurationError(f"Unknown LLM provider: {provider}")
        
        api_key = os.getenv(env_var)
        if not api_key:
            raise ConfigurationError(f"Missing {env_var} for provider {provider}")
    
    # Instanciar client
    clients = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "gemini": GeminiClient,
        "grok": GrokClient,
        "deepseek": DeepSeekClient,
    }
    
    client_class = clients.get(provider)
    if not client_class:
        raise ConfigurationError(f"Unknown LLM provider: {provider}")
    
    return client_class(api_key=api_key, default_timeout_s=timeout_s)
