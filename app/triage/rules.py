from app.tickets.schemas import TicketStatus
from app.triage.schemas import (
    CatalogSnapshot,
    EvaluationDecision,
    Impact,
    InvalidTriageFacts,
    Priority,
    TriageFacts,
    Urgency,
)

_PRIORITIES = {
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


def calculate_priority(impact: Impact, urgency: Urgency) -> Priority:
    return _PRIORITIES[(impact, urgency)]


def evaluate_facts(
    facts: TriageFacts,
    catalog: CatalogSnapshot,
) -> EvaluationDecision:
    if facts.service_id is not None and facts.service_id not in catalog.services:
        raise InvalidTriageFacts(f"Unknown service: {facts.service_id}")

    asset_service = None
    if facts.asset_id is not None:
        asset_service = catalog.asset_services.get(facts.asset_id)
        if asset_service is None:
            raise InvalidTriageFacts(f"Unknown asset: {facts.asset_id}")

    if (
        facts.service_id is not None
        and asset_service is not None
        and asset_service != facts.service_id
    ):
        return _pending_decision(facts, catalog)

    if facts.service_id is None or facts.impact is None or facts.urgency is None:
        return _pending_decision(facts, catalog)

    target_team = catalog.service_teams.get(facts.service_id)
    if target_team is None:
        return _pending_decision(facts, catalog)

    return EvaluationDecision(
        status=TicketStatus.EM_TRIAGEM,
        facts=facts,
        priority=calculate_priority(facts.impact, facts.urgency),
        target_team=target_team,
        catalog_version=catalog.version_id,
    )


def _pending_decision(
    facts: TriageFacts,
    catalog: CatalogSnapshot,
) -> EvaluationDecision:
    return EvaluationDecision(
        status=TicketStatus.PENDENTE_INFORMACAO,
        facts=facts,
        catalog_version=catalog.version_id,
    )
