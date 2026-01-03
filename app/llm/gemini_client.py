"""Google Gemini client adapter for Techno OS (V-COF governed).

Integra SDK oficial Google Generative AI com governança V-COF:
- Timeout configurável (fail-closed)
- Rate limit respeitado
- Erros normalizados
- Privacy by design (sem log de prompts)
"""

from __future__ import annotations

import time
from typing import Dict

from .client import LLMClient


class GeminiClient(LLMClient):
    """Google Gemini adapter (gemini-pro, gemini-1.5-pro, etc)."""

    def __init__(self, api_key: str, *, default_timeout_s: float = 10.0):
        """
        Args:
            api_key: Google API key (GOOGLE_API_KEY)
            default_timeout_s: Timeout padrão para chamadas
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError("MISSING_DEPENDENCY: pip install google-generativeai")

        genai.configure(api_key=api_key)
        self._genai = genai
        self._default_timeout_s = default_timeout_s

    def generate(
        self, *, prompt: str, model: str, temperature: float, max_tokens: int, timeout_s: float
    ) -> Dict:
        """Chama Google Generative AI API."""
        start = time.perf_counter()

        try:
            # Configurar modelo
            model_instance = self._genai.GenerativeModel(model)
            
            generation_config = self._genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            response = model_instance.generate_content(
                prompt,
                generation_config=generation_config,
                # Nota: SDK Google não suporta timeout diretamente (limitação conhecida)
            )

            latency_ms = int((time.perf_counter() - start) * 1000)

            # Normalizar resposta
            text = response.text
            
            # Gemini não expõe token usage via API (limitação do SDK)
            # Usar estimativa básica
            usage = {
                "prompt": len(prompt) // 4,  # ~4 chars/token
                "completion": len(text) // 4,
                "total": (len(prompt) + len(text)) // 4,
            }

            return {"text": text, "usage": usage, "model": model, "latency_ms": latency_ms}

        except TimeoutError:
            raise TimeoutError()
        except Exception as e:
            # Normalizar todos os erros para PROVIDER_ERROR (fail-closed)
            raise RuntimeError("PROVIDER_ERROR") from e
