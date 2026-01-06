# LLM INTEGRATION GUIDE — Techno OS

Guia para integrar **GPT, Claude, Gemini, Grok e DeepSeek** ao Techno OS Backend.

---

## 📋 PROVIDERS SUPORTADOS

| Provider | Client Class | Modelos | SDK Dependency |
|----------|-------------|---------|----------------|
| **OpenAI GPT** | `OpenAIClient` | gpt-4, gpt-3.5-turbo | `openai` |
| **Anthropic Claude** | `AnthropicClient` | claude-3-opus, claude-3-sonnet | `anthropic` |
| **Google Gemini** | `GeminiClient` | gemini-pro, gemini-1.5-pro | `google-generativeai` |
| **xAI Grok** | `GrokClient` | grok-beta | `openai` (API compatible) |
| **DeepSeek** | `DeepSeekClient` | deepseek-chat, deepseek-coder | `openai` (API compatible) |

---

## 🚀 CONFIGURAÇÃO RÁPIDA

### 1️⃣ Instalar dependências

```bash
# OpenAI (GPT, Grok, DeepSeek)
pip install openai

# Anthropic (Claude)
pip install anthropic

# Google (Gemini)
pip install google-generativeai
```

### 2️⃣ Configurar variáveis de ambiente

Adicionar ao `.env`:

```env
# Provider escolhido (openai, anthropic, gemini, grok, deepseek)
LLM_PROVIDER=openai

# API Keys (usar apenas a do provider escolhido)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
XAI_API_KEY=xai-...
DEEPSEEK_API_KEY=sk-...

# Modelo padrão (depende do provider)
LLM_MODEL=gpt-4  # ou claude-3-opus-20240229, gemini-pro, etc
LLM_TIMEOUT_S=10.0
```

### 3️⃣ Criar factory de clients

```python
# app/llm/factory.py
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
```

### 4️⃣ Usar no executor

```python
# app/executors/llm_executor_v1.py (atualizar __init__)

from app.llm.factory import create_llm_client

class LLMExecutorV1(Executor):
    def __init__(self, *, client: LLMClient | None = None):
        # ...
        # Usar factory se client não injetado
        self._client = client if client is not None else create_llm_client()
```

---

## 📖 EXEMPLOS DE USO

### OpenAI GPT-4

```python
from app.llm import OpenAIClient

client = OpenAIClient(api_key="sk-...")

result = client.generate(
    prompt="Explique o V-COF em 3 linhas",
    model="gpt-4",
    temperature=0.7,
    max_tokens=150,
    timeout_s=10.0,
)

print(result["text"])
# Output: V-COF é um framework de governança...
```

### Anthropic Claude

```python
from app.llm import AnthropicClient

client = AnthropicClient(api_key="sk-ant-...")

result = client.generate(
    prompt="Liste 3 princípios do Techno OS",
    model="claude-3-opus-20240229",
    temperature=0.7,
    max_tokens=200,
    timeout_s=10.0,
)

print(result["text"])
```

### Google Gemini

```python
from app.llm import GeminiClient

client = GeminiClient(api_key="AIza...")

result = client.generate(
    prompt="Descreva fail-closed em governança",
    model="gemini-pro",
    temperature=0.7,
    max_tokens=150,
    timeout_s=10.0,
)

print(result["text"])
```

---

## 🔒 GOVERNANÇA V-COF

Todos os clients implementam:

✅ **Fail-closed**: Erro → RuntimeError("PROVIDER_ERROR")  
✅ **Timeout**: Configurável por chamada  
✅ **Privacy**: Prompts não são logados  
✅ **Rate limiting**: Respeitado via policies  
✅ **Normalização**: Interface uniforme independente do provider

---

## 🧪 TESTES

```python
# tests/test_llm_clients.py
from app.llm import OpenAIClient, AnthropicClient, GeminiClient

def test_openai_integration():
    client = OpenAIClient(api_key="test-key")
    # Mock ou integration test
    pass

def test_anthropic_timeout():
    client = AnthropicClient(api_key="test-key")
    # Simular timeout
    pass
```

---

## 🚨 TROUBLESHOOTING

### Erro: `MISSING_DEPENDENCY`
```bash
pip install openai anthropic google-generativeai
```

### Erro: `Missing OPENAI_API_KEY`
```bash
export OPENAI_API_KEY=sk-...
# ou adicionar ao .env
```

### Erro: `PROVIDER_ERROR`
- Verificar API key válida
- Verificar quota do provider
- Checar status do provider (status.openai.com, etc)

---

## 📚 PRÓXIMOS PASSOS

1. ✅ Adicionar `llm/factory.py`
2. ✅ Atualizar `requirements.txt` com dependências opcionais
3. ✅ Criar testes de integração
4. ⚠️ Configurar rate limiting por provider
5. ⚠️ Implementar fallback entre providers
6. ⚠️ Adicionar métricas de latência por provider

---

**Governança:** V-COF · Fail-Closed · Human-in-the-Loop  
**Última atualização:** F9.8 (2026-01-03)
