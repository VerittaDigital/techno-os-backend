"""Export JSON schemas for canonical contracts (canonical_v1).

Provides a single public function `export_schema(output_path=...)` that:
- ensures the output directory exists
- collects JSON schemas for Agent, Arconte and AdminSignal (Pydantic v2)
- writes a single JSON file with header metadata and the schemas

This module can be executed as a script:

    python -m app.contracts.schema_export
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel

from app.contracts.canonical_v1 import Agent, Arconte, AdminSignal


DEFAULT_OUTPUT = "contracts_out/canonical_v1.schema.json"


def _model_schema(model: BaseModel) -> Dict[str, Any]:
    """Return the JSON schema dict for a Pydantic v2 model."""
    # Pydantic v2 provides model_json_schema() on models
    return model.model_json_schema()


def export_schema(output_path: str = DEFAULT_OUTPUT) -> Dict[str, Any]:
    """Export JSON schemas for canonical_v1 models and save to ``output_path``.

    Returns the final dict that was written (useful for testing).
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    schemas: Dict[str, Any] = {
        "Agent": _model_schema(Agent),
        "Arconte": _model_schema(Arconte),
        "AdminSignal": _model_schema(AdminSignal),
    }

    payload = {
        "contract_version": "canonical_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schemas": schemas,
    }

    # Write JSON file with readable formatting
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    return payload


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Export canonical_v1 JSON schemas")
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT})",
    )

    args = parser.parse_args()

    result = export_schema(args.output)
    print(f"Wrote schema file to: {args.output} (generated_at={result['generated_at']})")


if __name__ == "__main__":
    main()


__all__ = ["export_schema"]
