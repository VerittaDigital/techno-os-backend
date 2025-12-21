"""Pure normalization helpers (stdlib only).

All functions are deterministic and have no external dependencies.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set


def normalize_text(v: Any) -> Optional[str]:
    """Normalize text-like values.

    - If ``v`` is ``None`` -> ``None``
    - If ``v`` is ``str`` -> ``v.strip()``; if result is empty -> ``None``
    - Otherwise: ``str(v).strip()``; if result is empty -> ``None``

    Returns normalized string or ``None`` when input is absent/empty after trimming.
    """
    if v is None:
        return None

    if isinstance(v, str):
        s = v.strip()
        return s if s != "" else None

    s = str(v).strip()
    return s if s != "" else None


def normalize_score(v: Any) -> Optional[int]:
    """Normalize a score into an integer in range [0, 100].

    Rules:
    - ``None`` or empty string ``""`` -> ``None``
    - If ``v`` is ``int`` or ``float`` -> ``int(v)`` (booleans are treated as non-numeric and ignored)
    - If ``v`` is numeric string -> parsed to int (floats in strings are accepted and converted via ``float`` -> ``int``)
    - Non-numeric values -> ``None``
    - If resulting integer is < 0 or > 100 -> ``None`` (no clamping)
    """
    if v is None or v == "":
        return None

    # Explicitly ignore booleans
    if isinstance(v, bool):
        return None

    # Numeric types
    if isinstance(v, (int, float)):
        try:
            val = int(v)
        except Exception:
            return None
        if val < 0 or val > 100:
            return None
        return val

    # Strings: try to parse as int, then float
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return None
        try:
            val = int(s)
        except ValueError:
            try:
                f = float(s)
            except ValueError:
                return None
            try:
                val = int(f)
            except Exception:
                return None
        if val < 0 or val > 100:
            return None
        return val

    # Fallback: attempt int conversion
    try:
        val = int(v)
    except Exception:
        return None
    if val < 0 or val > 100:
        return None
    return val


def normalize_literal_enum(v: Any, allowed: Iterable[str], default: str = "UNKNOWN") -> str:
    """Normalize values that must match one of a set of literal strings.

    Behavior:
    - If ``v`` is ``None`` or empty string ``""`` -> returns ``default``.
    - First attempts an exact (case-sensitive) match against ``allowed``.
    - If no exact match, attempts a relaxed match by stripping and collapsing duplicate spaces in the
      input (e.g. ``"  Piloto   concluído "`` -> ``"Piloto concluído"``) and compares again.
    - If still no match -> returns ``default``.

    ``allowed`` can be any iterable of strings (a ``set`` is recommended for O(1) lookups).
    """
    if v is None or v == "":
        return default

    allowed_set: Set[str] = set(allowed)

    # Direct exact match (case-sensitive)
    if isinstance(v, str) and v in allowed_set:
        return v

    # Relax: remove duplicate spaces and strip
    candidate = " ".join(str(v).split()).strip()
    if candidate in allowed_set:
        return candidate

    return default


def safe_list(v: Any) -> List[Any]:
    """Return a safe list representation of ``v``.

    - ``None`` -> ``[]``
    - ``list``, ``tuple``, ``set`` -> ``list(v)``
    - otherwise -> ``[v]``
    """
    if v is None:
        return []

    if isinstance(v, (list, tuple, set)):
        return list(v)

    return [v]


__all__ = [
    "normalize_text",
    "normalize_score",
    "normalize_literal_enum",
    "safe_list",
]
