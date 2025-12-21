import pytest
from uuid import UUID
from datetime import datetime, timezone

from pydantic import ValidationError

from app.contracts.canonical_v1 import Agent, Arconte, AdminSignal


def test_agent_defaults_and_valid_values():
    a = Agent()
    assert isinstance(a.agent_id, UUID)
    assert a.nucleo == "UNKNOWN"
    assert a.status_operacional == "UNKNOWN"
    assert a.status_poc == "UNKNOWN"
    assert a.arcontes_ids == []
    assert a.source == "CANONICAL_V1"

    # with valid values
    a2 = Agent(
        agent_name="X",
        nucleo="Comercial",
        status_operacional="Operacional",
        status_poc="Ideação",
        maturidade=50,
        prontidao_producao=75,
        arcontes_ids=["a"],
    )
    assert a2.agent_name == "X"
    assert a2.nucleo == "Comercial"
    assert a2.maturidade == 50
    assert a2.prontidao_producao == 75


def test_agent_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Agent(extraneous_field="nope")


def test_arconte_and_adminsignal_minimal():
    ar = Arconte()
    assert isinstance(ar.arconte_id, UUID)
    assert ar.status_operacional == "UNKNOWN"
    assert ar.source == "CANONICAL_V1"

    sig = AdminSignal(entity_type="agent", entity_id="id", fields={"k": "v"}, collected_at=datetime.now(timezone.utc))
    assert sig.entity_type == "agent"
    assert sig.contract_version == "canonical_v1"


from datetime import datetime

def test_adminsignal_naive_datetime_converted_to_utc():
    naive = datetime(2025, 1, 1, 12, 0, 0)
    sig = AdminSignal(
        entity_type="agent",
        entity_id="x",
        fields={},
        collected_at=naive,
    )
    assert sig.collected_at.tzinfo is not None


def test_agent_external_fields_optional():
    a = Agent(external_id="notion_page_123", external_source="notion")
    assert a.external_id == "notion_page_123"
    assert a.external_source == "notion"
