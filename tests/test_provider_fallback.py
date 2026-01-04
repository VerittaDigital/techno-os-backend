"""Testes para provider fallback (RISK-8)."""

from unittest.mock import Mock, patch

import pytest

from app.llm.redundancy import ProviderFallback


def test_fallback_on_primary_failure():
    """Fallback de openai para anthropic em caso de falha."""
    fallback = ProviderFallback()

    with patch("app.llm.redundancy.get_circuit_breaker") as mock_cb, \
         patch("app.llm.redundancy.retry_with_backoff") as mock_retry, \
         patch("app.llm.redundancy.create_llm_client") as mock_create:
        
        # Mock circuit breakers (ambos CLOSED)
        cb = Mock(state="CLOSED")
        mock_cb.return_value = cb
        
        # Mock client
        mock_client = Mock()
        mock_create.return_value = mock_client
        
        # Mock retry: primeiro falha, segundo sucesso
        mock_retry.side_effect = [
            RuntimeError("PROVIDER_ERROR"),  # openai falha
            {"text": "success", "usage": {}, "model": "claude", "latency_ms": 10}  # anthropic ok
        ]
        
        # Mock circuit breaker call para passar o resultado direto
        cb.call.side_effect = lambda func: func()

        result = fallback.try_providers(
            prompt="test",
            model_map={"openai": "gpt-4", "anthropic": "claude-3-opus"},
            temperature=0.7,
            max_tokens=100
        )

        assert result["text"] == "success"
        assert "anthropic" in fallback.providers_attempted


def test_all_providers_fail():
    """Todos providers falham → RuntimeError ALL_PROVIDERS_FAILED."""
    fallback = ProviderFallback()

    with patch("app.llm.redundancy.get_circuit_breaker") as mock_cb, \
         patch("app.llm.redundancy.retry_with_backoff") as mock_retry, \
         patch("app.llm.redundancy.create_llm_client") as mock_create:
        
        # Mock circuit breaker (CLOSED)
        cb = Mock(state="CLOSED")
        mock_cb.return_value = cb
        
        # Mock client
        mock_client = Mock()
        mock_create.return_value = mock_client
        
        # Mock retry: ambos falhando
        mock_retry.side_effect = RuntimeError("PROVIDER_ERROR")
        
        # Mock circuit breaker call para passar o resultado direto
        cb.call.side_effect = lambda func: func()

        with pytest.raises(RuntimeError, match="ALL_PROVIDERS_FAILED"):
            fallback.try_providers(
                prompt="test",
                model_map={"openai": "gpt-4", "anthropic": "claude-3-opus"},
                temperature=0.7,
                max_tokens=100
            )

        assert len(fallback.providers_attempted) == 2


def test_skips_open_circuits():
    """Fallback pula providers com circuit OPEN."""
    fallback = ProviderFallback()

    with patch("app.llm.redundancy.get_circuit_breaker") as mock_cb, \
         patch("app.llm.redundancy.retry_with_backoff") as mock_retry, \
         patch("app.llm.redundancy.create_llm_client") as mock_create:
        
        # Mock circuit breakers: primeiro OPEN, segundo CLOSED
        cb_openai = Mock(state="OPEN")
        cb_anthropic = Mock(state="CLOSED")
        
        mock_cb.side_effect = lambda p: cb_openai if p == "openai" else cb_anthropic
        
        # Mock client
        mock_client = Mock()
        mock_create.return_value = mock_client
        
        # Mock retry: anthropic sucesso
        mock_retry.return_value = {"text": "success", "usage": {}, "model": "claude", "latency_ms": 10}
        
        # Mock circuit breaker call
        cb_anthropic.call.side_effect = lambda func: func()

        result = fallback.try_providers(
            prompt="test",
            model_map={"openai": "gpt-4", "anthropic": "claude-3-opus"},
            temperature=0.7,
            max_tokens=100
        )

        assert result["text"] == "success"
        # Anthropic deve ter sido chamado
        assert cb_anthropic.call.call_count == 1
        # OpenAI não deve ter sido chamado (circuit OPEN)
        assert cb_openai.call.call_count == 0


