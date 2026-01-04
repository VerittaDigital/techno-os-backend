"""Gate Engine - Canonical action detection and body parsing.

This module provides:
- action_detector: Canonical action detection from HTTP requests
- body_parser: Deterministic body parsing by HTTP method

Part of FASE 11 - Gate Engine Consolidation.
"""

from app.gate_canonical.action_detector import detect_action, normalize_path
from app.gate_canonical.body_parser import parse_body_by_method

__all__ = [
    "detect_action",
    "normalize_path",
    "parse_body_by_method",
]
