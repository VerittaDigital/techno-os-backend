"""
Canonical contract version v1 — Pydantic v2 models

Observações:
- Dados administrativos são advisory-only; proibido runtime: este contrato deve ser usado para transporte e validação estrutural apenas,
  não para decisões críticas de segurança, autorização ou similares em tempo de execução.
- Sem integrações externas.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ----- Enums literais -----
StatusOperacional = Literal[
    "A Forjar",
    "Operacional",
    "Em Atualização",
    "Indisponível",
    "Blindado",
    "UNKNOWN",
]

StatusPOC = Literal[
    "Ideação",
    "Prototipando",
    "Em piloto",
    "Piloto concluído",
    "Validado",
    "Arquivado",
    "UNKNOWN",
]

Nucleo = Literal[
    "Comercial",
    "Acadêmico",
    "Matéria-Vida",
    "Jurídico",
    "Criativo",
    "Tecnológico",
    "UNKNOWN",
]


# ----- Modelos -----
class Agent(BaseModel):
    """Representa um agente canônico.

    Nota: `agent_id` é gerado pelo sistema por padrão. Dados administrativos (p.ex. `status_operacional`) são
    apenas advisory — evite decisões críticas em runtime baseadas exclusivamente nestes campos.
    """

    agent_id: UUID = Field(default_factory=uuid4, description="UUID gerado pelo sistema")
    agent_name: Optional[str] = None
    external_id: Optional[str] = None
    external_source: Optional[Literal["notion"]] = None
    nucleo: Nucleo = "UNKNOWN"
    status_operacional: StatusOperacional = "UNKNOWN"
    status_poc: StatusPOC = "UNKNOWN"
    maturidade: Optional[int] = Field(default=None, ge=0, le=100)
    prontidao_producao: Optional[int] = Field(default=None, ge=0, le=100)
    arcontes_ids: List[str] = Field(default_factory=list)
    source: Literal["CANONICAL_V1"] = Field("CANONICAL_V1")

    model_config = {"extra": "forbid"}


class Arconte(BaseModel):
    """Representa um arconte canônico.

    Campos administrativos são advisory-only.
    """

    arconte_id: UUID = Field(default_factory=uuid4, description="UUID gerado pelo sistema")
    arconte_name: Optional[str] = None
    camada_vcof: Optional[str] = None
    status_operacional: StatusOperacional = "UNKNOWN"
    agentes_ids: List[str] = Field(default_factory=list)
    source: Literal["CANONICAL_V1"] = Field("CANONICAL_V1")

    model_config = {"extra": "forbid"}


class AdminSignal(BaseModel):
    """Sinal administrativo para um `agent` ou `arconte`.

    **Aviso**: Este modelo contém metadados administrativos que são *advisory-only* e não devem ser usados
    como fonte única para decisões de segurança ou autorização em tempo de execução.

    Observação: o campo `collected_at` deve ser timezone-aware em UTC; entradas sem `tzinfo` serão
    interpretadas como UTC e convertidas para timezone-aware UTC.

    NOTE:
    Naive datetimes are interpreted as UTC by design.
    This is an explicit, audited decision.
    """

    entity_type: Literal["agent", "arconte"]
    entity_id: str
    fields: Dict[str, Any]
    collected_at: datetime
    contract_version: Literal["canonical_v1"] = Field("canonical_v1")

    @field_validator("collected_at")
    def _collected_at_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    model_config = {"extra": "forbid"}


__all__ = [
    "StatusOperacional",
    "StatusPOC",
    "Nucleo",
    "Agent",
    "Arconte",
    "AdminSignal",
]
