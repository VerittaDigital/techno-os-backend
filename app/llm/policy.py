from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Policy:
    ALLOWED_MODELS: ClassVar[list[str]] = ["gpt-4", "gpt-3.5-turbo"]
    TEMPERATURE: ClassVar[float] = 0.0
    MAX_PROMPT_CHARS: ClassVar[int] = 10000
    MAX_TOKENS_TOTAL: ClassVar[int] = 4096
    TIMEOUT_S: ClassVar[float] = 30.0  # F9.9-C: Alinhado com hardening (10.0 → 30.0)

    @classmethod
    def validate(cls, *, prompt: str, model: str, max_tokens: int, timeout_s: float) -> None:
        if not isinstance(prompt, str) or not prompt:
            raise ValueError("POLICY_VIOLATION")
        if len(prompt) > cls.MAX_PROMPT_CHARS:
            raise ValueError("POLICY_VIOLATION")
        if model not in cls.ALLOWED_MODELS:
            raise ValueError("POLICY_VIOLATION")
        if not isinstance(max_tokens, int) or max_tokens <= 0 or max_tokens > cls.MAX_TOKENS_TOTAL:
            raise ValueError("POLICY_VIOLATION")
        if timeout_s <= 0 or timeout_s > cls.TIMEOUT_S:
            raise ValueError("POLICY_VIOLATION")
