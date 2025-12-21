"""Field governance definitions for canonical contracts.

This module contains lightweight, deterministic rules describing who may author a
field, its allowed read/write direction, and its criticality level with respect
to runtime usage. It intentionally has no external dependencies (stdlib only).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, Optional, Set


class Author(Enum):
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"


class Direction(Enum):
    READ_ONLY = "READ_ONLY"
    WRITE_ONLY = "WRITE_ONLY"
    READ_WRITE = "READ_WRITE"


class Criticality(Enum):
    CANONICAL_CORE = "CANONICAL_CORE"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    PROHIBITED_RUNTIME = "PROHIBITED_RUNTIME"


@dataclass(frozen=True)
class FieldRule:
    """Immutable rule describing governance for a single field.

    - field: canonical field name
    - author: who owns/authoritatively sets this field (HUMAN or SYSTEM)
    - direction: allowed directionality for the field
    - criticality: whether the field is core, advisory, or prohibited at runtime
    - notes: human-facing short explanation / source (ex.: Notion property)
    """

    field: str
    author: Author
    direction: Direction
    criticality: Criticality
    notes: str


# ----- Minimal rules for Agent (canonical_v1) -----
AGENT_MINIMAL_RULES: Dict[str, FieldRule] = {
    "agent_id": FieldRule(
        "agent_id",
        Author.SYSTEM,
        Direction.WRITE_ONLY,
        Criticality.CANONICAL_CORE,
        "UUID gerado pelo sistema",
    ),
    "agent_name": FieldRule(
        "agent_name",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion property "Agente"',
    ),
    "nucleo": FieldRule(
        "nucleo",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion "Núcleo"',
    ),
    "status_operacional": FieldRule(
        "status_operacional",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion "Status Operacional"',
    ),
    "status_poc": FieldRule(
        "status_poc",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion "Status POC"',
    ),
    "maturidade": FieldRule(
        "maturidade",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion "Maturidade do Agente (0–100)"',
    ),
    "prontidao_producao": FieldRule(
        "prontidao_producao",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion "Prontidão para Produção (0–100)"',
    ),
    "arcontes_ids": FieldRule(
        "arcontes_ids",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion "Interação com Arcontes"',
    ),
    "source": FieldRule(
        "source",
        Author.SYSTEM,
        Direction.WRITE_ONLY,
        Criticality.CANONICAL_CORE,
        "Fonte canônica",
    ),
    "external_id": FieldRule(
        "external_id",
        Author.SYSTEM,
        Direction.WRITE_ONLY,
        Criticality.PROHIBITED_RUNTIME,
        "External integration identifier — administrative; not allowed in runtime or for decisions",
    ),
    "external_source": FieldRule(
        "external_source",
        Author.SYSTEM,
        Direction.WRITE_ONLY,
        Criticality.PROHIBITED_RUNTIME,
        "External source name — administrative; not allowed in runtime or for decisions",
    ),
}


# ----- Minimal rules for Arconte (canonical_v1) -----
ARCONTE_MINIMAL_RULES: Dict[str, FieldRule] = {
    "arconte_id": FieldRule(
        "arconte_id",
        Author.SYSTEM,
        Direction.WRITE_ONLY,
        Criticality.CANONICAL_CORE,
        "UUID gerado pelo sistema",
    ),
    "arconte_name": FieldRule(
        "arconte_name",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion "Nome"',
    ),
    "camada_vcof": FieldRule(
        "camada_vcof",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion "Camada do V-COF"',
    ),
    "status_operacional": FieldRule(
        "status_operacional",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        'Notion "Status Operacional"',
    ),
    "agentes_ids": FieldRule(
        "agentes_ids",
        Author.HUMAN,
        Direction.READ_WRITE,
        Criticality.ADVISORY_ONLY,
        "relations",
    ),
    "source": FieldRule(
        "source",
        Author.SYSTEM,
        Direction.WRITE_ONLY,
        Criticality.CANONICAL_CORE,
        "Fonte canônica",
    ),
}


# Explicitly prohibited fields (Notion-derived or human text fields)
PROHIBITED_FIELDS: Set[str] = {
    "% Conclusão (Checklist)",
    "%SEAL",
    "Gate Operacional do Agente",
    "Gate SEAL — Governança",

    # Human-authored documents / sensitive metadata (examples)
    "SOP Principal",
    "Riscos e Salvaguardas",
    "Critérios de Aceite",
    "Descrição Operacional",
    "Função Primária",
    "KPIs",
    "Hipótese",
    "Prompt Base",
}

# When True, unknown fields are denied by default (fail-closed)
DENY_UNKNOWN_FIELDS: bool = True

# Patterns that should be considered prohibited at runtime (case-insensitive substring match)
_PROHIBITED_PATTERNS: Set[str] = {
    "rollup",
    "rollups",
    "formula",
    "file",
    "arquivo",
    "attachment",
}


def _matches_prohibited_pattern(field: str) -> bool:
    if not field:
        return False
    name = field.lower()
    return any(p in name for p in _PROHIBITED_PATTERNS)


def get_rule(field: str) -> Optional[FieldRule]:
    """Return the FieldRule for a canonical field or a PROHIBITED_RUNTIME entry when appropriate.

    Matching is exact on the canonical field name. Prohibited patterns and the explicit
    prohibited set will be converted into a `FieldRule` with criticality
    ``Criticality.PROHIBITED_RUNTIME``.
    """
    if field in AGENT_MINIMAL_RULES:
        return AGENT_MINIMAL_RULES[field]

    if field in ARCONTE_MINIMAL_RULES:
        return ARCONTE_MINIMAL_RULES[field]

    if field in PROHIBITED_FIELDS or _matches_prohibited_pattern(field):
        return FieldRule(
            field,
            Author.SYSTEM,
            Direction.WRITE_ONLY,
            Criticality.PROHIBITED_RUNTIME,
            "Proibido em runtime (campo do Notion ou tipo humano/rollup/formula/file)",
        )

    return None


def is_runtime_allowed(field: str) -> bool:
    """Return True when the given field is allowed to be used at runtime.

    Fields explicitly marked as PROHIBITED_RUNTIME (or matching prohibited patterns)
    return False. Unknown fields are denied by default when `DENY_UNKNOWN_FIELDS` is True.
    """
    rule = get_rule(field)
    if rule is None:
        # Fail-closed policy: unknown fields are not allowed at runtime
        return False
    return rule.criticality != Criticality.PROHIBITED_RUNTIME


def explain_field(field: str) -> str:
    """Return a short human-readable explanation for a field or "unknown field".

    Format: "<field>: author=<AUTHOR>, direction=<DIRECTION>, criticality=<CRITICALITY>. Notes: <notes>"
    """
    rule = get_rule(field)
    if rule is None:
        return "unknown field"

    return (
        f"{rule.field}: author={rule.author.name}, direction={rule.direction.name}, "
        f"criticality={rule.criticality.name}. Notes: {rule.notes}"
    )


__all__ = [
    "Author",
    "Direction",
    "Criticality",
    "FieldRule",
    "AGENT_MINIMAL_RULES",
    "ARCONTE_MINIMAL_RULES",
    "PROHIBITED_FIELDS",
    "get_rule",
    "is_runtime_allowed",
    "explain_field",
]
