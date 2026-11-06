from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.triage.interpretation_schemas import (
    InterpretationProposal,
    TicketInterpretationResponse,
)
from app.triage.schemas import Impact, Urgency


def test_interpretation_schema_accepts_complete_and_partial_proposals() -> None:
    complete = InterpretationProposal.model_validate(
        {
            "service_candidate": "Serviço de endpoint",
            "asset_candidate": "Laptop do usuário",
            "impact": "ALTO",
            "urgency": "ALTA",
            "symptoms": ["Falha ao autenticar"],
            "impact_evidence": ["Afeta todos os usuários"],
            "urgency_evidence": ["Operação parada"],
            "missing_information": [],
            "uncertainties": [],
            "technical_summary": "Falha ampla de autenticação.",
        }
    )
    partial = InterpretationProposal.model_validate(
        {
            "service_candidate": None,
            "asset_candidate": None,
            "impact": None,
            "urgency": "BAIXA",
            "symptoms": [],
            "impact_evidence": [],
            "urgency_evidence": ["Sem prazo indicado"],
            "missing_information": ["Serviço afetado"],
            "uncertainties": ["Escopo do impacto não foi informado"],
            "technical_summary": None,
        }
    )

    assert complete.service_candidate == "Serviço de endpoint"
    assert complete.asset_candidate == "Laptop do usuário"
    assert complete.impact is Impact.ALTO
    assert complete.urgency is Urgency.ALTA
    assert complete.symptoms == ["Falha ao autenticar"]
    assert complete.impact_evidence == ["Afeta todos os usuários"]
    assert complete.urgency_evidence == ["Operação parada"]
    assert complete.missing_information == []
    assert complete.uncertainties == []
    assert complete.technical_summary == "Falha ampla de autenticação."
    assert partial.service_candidate is None
    assert partial.asset_candidate is None
    assert partial.impact is None
    assert partial.urgency is Urgency.BAIXA
    assert partial.symptoms == []
    assert partial.missing_information == ["Serviço afetado"]
    assert partial.uncertainties == ["Escopo do impacto não foi informado"]
    assert partial.technical_summary is None


def test_interpretation_schema_rejects_invalid_enums_and_extra_fields() -> None:
    valid_proposal = {
        "service_candidate": None,
        "asset_candidate": None,
        "impact": None,
        "urgency": None,
        "symptoms": [],
        "impact_evidence": [],
        "urgency_evidence": [],
        "missing_information": [],
        "uncertainties": [],
        "technical_summary": None,
    }

    for field, value in (("impact", "CRITICO"), ("urgency", "URGENTE")):
        with pytest.raises(ValidationError):
            InterpretationProposal.model_validate(
                {**valid_proposal, field: value}
            )

    for field, value in (
        ("ticket_id", str(uuid4())),
        ("priority", "P1"),
        ("target_team", "team-network"),
        ("confidence", 0.99),
    ):
        with pytest.raises(ValidationError):
            InterpretationProposal.model_validate(
                {**valid_proposal, field: value}
            )


def test_ticket_interpretation_response_adds_ticket_id_after_proposal() -> None:
    ticket_id = uuid4()
    response = TicketInterpretationResponse.model_validate(
        {
            "ticket_id": str(ticket_id),
            "service_candidate": None,
            "asset_candidate": None,
            "impact": "MEDIO",
            "urgency": "MEDIA",
            "symptoms": [],
            "impact_evidence": [],
            "urgency_evidence": [],
            "missing_information": [],
            "uncertainties": [],
            "technical_summary": None,
        }
    )

    assert response.ticket_id == ticket_id
    assert response.impact is Impact.MEDIO
    assert response.urgency is Urgency.MEDIA
