import pytest

from app.tickets.schemas import TicketStatus
from app.triage.rules import calculate_priority, evaluate_facts
from app.triage.schemas import (
    CatalogSnapshot,
    Impact,
    Priority,
    TriageFacts,
    Urgency,
)


@pytest.fixture
def catalog() -> CatalogSnapshot:
    return CatalogSnapshot(
        version_id="catalog-v1",
        services=frozenset({"service-connectivity", "service-endpoint"}),
        asset_services={
            "asset-router-001": "service-connectivity",
            "asset-laptop-001": "service-endpoint",
        },
        service_teams={
            "service-connectivity": "team-network",
            "service-endpoint": "team-workplace",
        },
    )


def test_priority_matrix_covers_all_nine_combinations() -> None:
    expected = {
        (Impact.ALTO, Urgency.ALTA): Priority.P1,
        (Impact.ALTO, Urgency.MEDIA): Priority.P2,
        (Impact.ALTO, Urgency.BAIXA): Priority.P2,
        (Impact.MEDIO, Urgency.ALTA): Priority.P2,
        (Impact.MEDIO, Urgency.MEDIA): Priority.P3,
        (Impact.MEDIO, Urgency.BAIXA): Priority.P3,
        (Impact.BAIXO, Urgency.ALTA): Priority.P3,
        (Impact.BAIXO, Urgency.MEDIA): Priority.P4,
        (Impact.BAIXO, Urgency.BAIXA): Priority.P4,
    }

    for (impact, urgency), priority in expected.items():
        assert calculate_priority(impact, urgency) is priority


def test_complete_facts_calculate_priority_and_use_catalog_mapped_team(
    catalog: CatalogSnapshot,
) -> None:
    facts = TriageFacts(
        service_id="service-endpoint",
        impact=Impact.MEDIO,
        urgency=Urgency.ALTA,
    )

    decision = evaluate_facts(facts, catalog)

    assert decision.status is TicketStatus.EM_TRIAGEM
    assert decision.priority is Priority.P2
    assert decision.target_team == "team-workplace"
    assert decision.facts == facts


def test_missing_facts_or_team_mapping_produce_pending_without_assignment(
    catalog: CatalogSnapshot,
) -> None:
    incomplete_facts = TriageFacts(
        service_id="service-endpoint",
        impact=Impact.ALTO,
    )
    unmapped_catalog = catalog.model_copy(
        update={"service_teams": {"service-connectivity": "team-network"}}
    )
    complete_facts = TriageFacts(
        service_id="service-endpoint",
        impact=Impact.ALTO,
        urgency=Urgency.ALTA,
    )

    for facts, snapshot in (
        (incomplete_facts, catalog),
        (complete_facts, unmapped_catalog),
    ):
        decision = evaluate_facts(facts, snapshot)
        assert decision.status is TicketStatus.PENDENTE_INFORMACAO
        assert decision.priority is None
        assert decision.target_team is None
        assert decision.facts == facts


def test_asset_service_mismatch_produces_pending_without_assignment(
    catalog: CatalogSnapshot,
) -> None:
    facts = TriageFacts(
        service_id="service-endpoint",
        asset_id="asset-router-001",
        impact=Impact.ALTO,
        urgency=Urgency.ALTA,
    )

    decision = evaluate_facts(facts, catalog)

    assert decision.status is TicketStatus.PENDENTE_INFORMACAO
    assert decision.facts == facts
    assert decision.priority is None
    assert decision.target_team is None
