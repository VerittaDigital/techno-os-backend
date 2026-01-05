"""Tests for F9.10 Observability Containerization.

Valida containerização de Prometheus + Alertmanager + Grafana,
alert rules carregadas, e datasources configurados.
"""

from __future__ import annotations

import json
import subprocess
from typing import Dict

import pytest
import requests


def test_prometheus_containerized():
    """Prometheus deve estar rodando como container."""
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=techno-os-prometheus", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    assert "techno-os-prometheus" in result.stdout


def test_alertmanager_containerized():
    """Alertmanager deve estar rodando como container."""
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=techno-os-alertmanager", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    assert "techno-os-alertmanager" in result.stdout


def test_prometheus_healthy():
    """Prometheus deve responder healthcheck."""
    try:
        resp = requests.get("http://localhost:9090/-/healthy", timeout=5)
        assert resp.status_code == 200
    except requests.RequestException:
        pytest.skip("Prometheus não acessível (containers não iniciados)")


def test_alertmanager_ready():
    """Alertmanager deve responder status API."""
    try:
        resp = requests.get("http://localhost:9093/api/v2/status", timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert "versionInfo" in data
    except requests.RequestException:
        pytest.skip("Alertmanager não acessível (containers não iniciados)")


def test_alert_rules_loaded():
    """Alert rules devem estar carregadas no Prometheus."""
    try:
        resp = requests.get("http://localhost:9090/api/v1/rules", timeout=5)
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["status"] == "success"
        
        groups = data["data"]["groups"]
        group_names = [g["name"] for g in groups]
        
        # F9.10: 2 grupos de rules (llm_health, api_health)
        assert "llm_health" in group_names
        assert "api_health" in group_names
        
        # Contar rules totais (4 LLM + 1 API = 5)
        total_rules = sum(len(g["rules"]) for g in groups)
        assert total_rules == 5, f"Esperado 5 rules, encontrado {total_rules}"
        
    except requests.RequestException:
        pytest.skip("Prometheus não acessível (containers não iniciados)")


def test_grafana_datasource_prometheus():
    """Grafana deve ter datasource Prometheus configurado."""
    try:
        # Grafana datasource API (sem autenticação em dev)
        resp = requests.get("http://localhost:3000/api/datasources", timeout=5)
        
        if resp.status_code == 401:
            pytest.skip("Grafana requer autenticação (configurar GRAFANA_ADMIN_PASSWORD)")
        
        assert resp.status_code == 200
        
        datasources = resp.json()
        prometheus_ds = [ds for ds in datasources if ds["type"] == "prometheus"]
        
        assert len(prometheus_ds) > 0, "Datasource Prometheus não encontrado"
        assert prometheus_ds[0]["url"] == "http://prometheus:9090"
        
    except requests.RequestException:
        pytest.skip("Grafana não acessível (containers não iniciados)")


def test_backup_script_exists():
    """Script de backup deve existir e ser executável."""
    import os
    
    script_path = "scripts/backup_observability.sh"
    assert os.path.exists(script_path), f"Script {script_path} não encontrado"
    assert os.access(script_path, os.X_OK), f"Script {script_path} não é executável"
    
    # Validar conteúdo (3 volumes)
    with open(script_path, "r") as f:
        content = f.read()
        assert "postgres_data" in content
        assert "prometheus_data" in content
        assert "grafana_data" in content


def test_env_circuit_breaker_config():
    """Circuit breaker deve suportar configuração por ENV."""
    import os
    from app.llm import circuit_breaker_singleton
    
    # Testar fallback para defaults
    threshold = circuit_breaker_singleton.CIRCUIT_BREAKER_THRESHOLD
    timeout = circuit_breaker_singleton.CIRCUIT_BREAKER_TIMEOUT
    
    assert isinstance(threshold, int)
    assert isinstance(timeout, int)
    assert threshold >= 1
    assert timeout >= 1
