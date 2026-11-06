import pytest
from pydantic import ValidationError

from app.triage.schemas import Impact, TriageFacts, Urgency


def test_triage_facts_accept_allowed_values_and_optional_asset() -> None:
    facts = TriageFacts(
        service_id="service-endpoint",
        impact=Impact.ALTO,
        urgency=Urgency.ALTA,
    )

    assert facts.service_id == "service-endpoint"
    assert facts.asset_id is None
    assert facts.impact is Impact.ALTO
    assert facts.urgency is Urgency.ALTA


def test_triage_facts_reject_invalid_values_and_caller_assignments() -> None:
    for field, value in (("impact", "CRITICO"), ("urgency", "URGENTE")):
        with pytest.raises(ValidationError):
            TriageFacts.model_validate({field: value})

    for field, value in (("priority", "P1"), ("target_team", "team-network")):
        with pytest.raises(ValidationError):
            TriageFacts.model_validate({field: value})
