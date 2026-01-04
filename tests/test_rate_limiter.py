"""Testes para rate limiter (RISK-5)."""

import time

import pytest

from app.llm.rate_limiter import RateLimiter


def test_enforces_rate_limit():
    """Rate limiter bloqueia chamadas além do limite."""
    limiter = RateLimiter()
    limiter.LIMITS["test_provider"] = 2  # 2 req/min = 1 req a cada 30s

    start = time.perf_counter()
    
    # 1ª requisição: instantânea
    limiter.acquire("test_provider")
    elapsed1 = time.perf_counter() - start
    assert elapsed1 < 0.1  # Quase instantâneo

    # 2ª requisição: instantânea (bucket tem 2 tokens iniciais)
    limiter.acquire("test_provider")
    elapsed2 = time.perf_counter() - start
    assert elapsed2 < 0.1

    # 3ª requisição: deve bloquear ~30s
    limiter.acquire("test_provider")
    elapsed3 = time.perf_counter() - start
    assert 25 < elapsed3 < 35, f"esperado ~30s, obteve {elapsed3}s"


def test_allows_within_limit():
    """Rate limiter não bloqueia chamadas dentro do limite."""
    limiter = RateLimiter()
    limiter.LIMITS["fast_provider"] = 120  # 120 req/min = 2 req/s

    start = time.perf_counter()
    
    # 5 requisições rápidas dentro do limite
    for _ in range(5):
        limiter.acquire("fast_provider")
    
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0  # Deve completar em <5s (todas dentro do bucket)


def test_independent_providers():
    """Rate limiters de providers diferentes são independentes."""
    limiter = RateLimiter()
    limiter.LIMITS["provider_a"] = 2  # 2 req/min
    limiter.LIMITS["provider_b"] = 60  # 60 req/min

    # Esgotar tokens de provider_a
    limiter.acquire("provider_a")
    limiter.acquire("provider_a")

    # provider_b ainda deve ter tokens disponíveis
    start = time.perf_counter()
    limiter.acquire("provider_b")
    elapsed = time.perf_counter() - start
    assert elapsed < 0.1  # Instantâneo
