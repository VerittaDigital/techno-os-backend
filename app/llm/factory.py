"""LLM Client Factory (V-COF governed)."""

import os
from typing import Optional

from .client import LLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .gemini_client import GeminiClient
from .grok_client import GrokClient
from .deepseek_client import DeepSeekClient
from .fake_client import FakeLLMClient


def create_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout_s: float = 10.0,
) -> LLMClient:
    """
    Factory para criar LLM client baseado em provider.
    
    Args:
        provider: "openai", "anthropic", "gemini", "grok", "deepseek" ou None (usa env)
        api_key: API key do provider ou None (usa env)
        timeout_s: Timeout padrão
        
    Returns:
        LLMClient instance (ou FakeLLMClient se não configurado)
        
    Raises:
        RuntimeError: Se provider inválido ou API key ausente
    """
    # Detectar provider via env se não fornecido
    provider = provider or os.getenv("LLM_PROVIDER", "fake")
    provider = provider.lower()
    
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
            raise RuntimeError(f"Unknown LLM provider: {provider}")
        
        api_key = os.getenv(env_var)
        if not api_key:
            raise RuntimeError(f"Missing {env_var} for provider {provider}")
    
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
        raise RuntimeError(f"Unknown LLM provider: {provider}")
    
    return client_class(api_key=api_key, default_timeout_s=timeout_s)
