from __future__ import annotations

from typing import Any, Dict

from .client import LLMClient


class OpenAIClient(LLMClient):
    def __init__(self, sdk_client: Any, *, default_timeout_s: float = 10.0):
        # Configuration via constructor only (injection)
        self._client = sdk_client
        self._default_timeout_s = default_timeout_s

    def generate(self, *, prompt: str, model: str, temperature: float, max_tokens: int, timeout_s: float) -> Dict:
        # Use provided timeout or default
        t = timeout_s or self._default_timeout_s
        try:
            # Thin wrapper: rely on injected SDK client interface
            # SDK should support a sync call like: create(prompt=..., model=..., timeout=...)
            resp = self._client.create(prompt=prompt, model=model, temperature=temperature, max_tokens=max_tokens, timeout=t)
            # Normalize response
            text = getattr(resp, "text", None) or resp.get("text")
            usage = getattr(resp, "usage", None) or resp.get("usage")
            return {"text": text, "usage": usage, "model": model, "latency_ms": getattr(resp, "latency_ms", 0)}
        except TimeoutError:
            raise TimeoutError()
        except Exception:
            raise RuntimeError("PROVIDER_ERROR")
