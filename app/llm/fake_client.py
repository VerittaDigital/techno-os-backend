from __future__ import annotations

from hashlib import sha256
from typing import Dict

from .client import LLMClient


class FakeLLMClient(LLMClient):
    def __init__(self, *, simulate_timeout: bool = False):
        self.simulate_timeout = simulate_timeout

    def generate(self, *, prompt: str, model: str, temperature: float, max_tokens: int, timeout_s: float) -> Dict:
        if self.simulate_timeout:
            # Simulate provider timeout as a provider error to ensure pipeline
            # treats the execution as FAILED (fail-closed). Tests trigger this.
            raise RuntimeError("SIMULATED_TIMEOUT")

        digest = sha256(prompt.encode("utf-8")).hexdigest()[:8]
        text = f"FAKE::{digest}"
        usage = {"prompt": 0, "completion": 1, "total": 1}
        return {"text": text, "usage": usage, "model": model, "latency_ms": 1}
