#!/usr/bin/env python3
"""Diagnose test failures for Sprint A."""

import subprocess
import json
import re
from collections import defaultdict
from pathlib import Path

def run_tests():
    """Run all tests and capture output."""
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "--json-report", "--json-report-file=test-report.json"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )
    return result.stdout, result.stderr

def parse_output(stdout):
    """Parse pytest output to find failures."""
    failures = []
    lines = stdout.split('\n')
    
    for line in lines:
        # Match FAILED pattern
        if 'FAILED' in line:
            # Extract test name and module
            match = re.search(r'(tests/\S+::\S+)\s+FAILED', line)
            if match:
                test_path = match.group(1)
                failures.append({
                    'test_path': test_path,
                    'line': line
                })
    
    return failures

def main():
    print("=" * 80)
    print("DIAGNÓSTICO GLOBAL DE TESTES - Sprint A")
    print("=" * 80)
    print()
    
    print("🔍 Executando pytest...")
    stdout, stderr = run_tests()
    
    # Display summary
    print("\n📊 RESUMO EXECUTIVO:")
    print("-" * 80)
    
    # Extract summary line
    for line in stdout.split('\n')[-20:]:
        if 'passed' in line or 'failed' in line or 'error' in line:
            print(line)
    
    print("\n📋 DETALHES COMPLETOS:")
    print("-" * 80)
    print(stdout)

if __name__ == "__main__":
    main()
