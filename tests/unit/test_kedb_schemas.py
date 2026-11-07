import uuid
import pytest
from pydantic import ValidationError

from app.triage.kedb_schemas import KedbLookupResult, KedbLookupStatus, KedbMatch
from app.triage.interpretation_schemas import TicketInterpretationResponse
from app.triage.schemas import Impact, Urgency


def test_kedb_match_schema_accepts_valid_payload() -> None:
    match = KedbMatch(
        error_id="ERR-001",
        title="Falha de conexão VPN",
        summary="Timeout ao autenticar no gateway VPN corporativo.",
        match_reasons=["service: VPN Corporativa"],
        workaround="Reiniciar o cliente VPN e limpar o cache de DNS.",
    )
    assert match.error_id == "ERR-001"
    assert match.title == "Falha de conexão VPN"
    assert match.summary == "Timeout ao autenticar no gateway VPN corporativo."
    assert match.match_reasons == ["service: VPN Corporativa"]
    assert match.workaround == "Reiniciar o cliente VPN e limpar o cache de DNS."


def test_kedb_match_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        KedbMatch(
            error_id="ERR-001",
            title="Erro",
            summary="Resumo",
            match_reasons=["service"],
            workaround="Workaround",
            extra_field="invalid",  # type: ignore[call-arg]
        )


def test_kedb_lookup_result_accepts_available_and_unavailable() -> None:
    available = KedbLookupResult(
        status=KedbLookupStatus.AVAILABLE,
        matches=[
            KedbMatch(
                error_id="ERR-001",
                title="Erro",
                summary="Resumo",
                match_reasons=["service"],
                workaround="Solução",
            )
        ],
    )
    assert available.status == KedbLookupStatus.AVAILABLE
    assert len(available.matches) == 1

    unavailable = KedbLookupResult(
        status=KedbLookupStatus.UNAVAILABLE,
        matches=[],
    )
    assert unavailable.status == KedbLookupStatus.UNAVAILABLE
    assert unavailable.matches == []


def test_ticket_interpretation_response_with_kedb() -> None:
    response = TicketInterpretationResponse(
        ticket_id=uuid.uuid4(),
        service_candidate="VPN",
        asset_candidate=None,
        impact=Impact.ALTO,
        urgency=Urgency.ALTA,
        symptoms=["sem conexao"],
        impact_evidence=["impacto geral"],
        urgency_evidence=["urgente"],
        missing_information=[],
        uncertainties=[],
        technical_summary="Problema de VPN.",
        kedb=KedbLookupResult(
            status=KedbLookupStatus.AVAILABLE,
            matches=[],
        ),
    )
    assert response.kedb is not None
    assert response.kedb.status == KedbLookupStatus.AVAILABLE
    assert response.kedb.matches == []
