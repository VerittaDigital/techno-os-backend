"""Test to ensure contract modules don't pull in web dependencies (FastAPI).

This test imports the canonical contract modules and asserts that importing them
does not cause `fastapi` to appear in `sys.modules` and that no exception is raised
during import.
"""

import subprocess
import sys

import pytest


def test_contracts_do_not_import_fastapi():
    """Contracts should not depend on FastAPI (web framework isolation)."""
    # Run in isolated subprocess to avoid contamination from other tests
    code = """
import sys
# Import contract modules
from app.contracts import canonical_v1, normalize, field_governance
# Check if fastapi got loaded
if 'fastapi' in sys.modules:
    sys.exit(1)
sys.exit(0)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=".",
    )
    
    if result.returncode != 0:
        pytest.fail(
            f"fastapi was imported as transitive dependency of contracts.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
