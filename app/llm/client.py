from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def generate(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout_s: float,
    ) -> dict:
        """Generate text from a model.

        Returns a dict with keys: text, usage, model, latency_ms
        May raise TimeoutError or RuntimeError("PROVIDER_ERROR").
        """
        raise NotImplementedError()
