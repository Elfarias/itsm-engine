from uuid import UUID

import psycopg

from app.tickets.schemas import TicketStatus
from app.triage.repository import (
    TicketSnapshot,
    append_evaluation_event,
    load_active_catalog,
    lock_ticket,
    save_evaluation,
)
from app.triage.rules import evaluate_facts
from app.triage.schemas import (
    CatalogConfigurationError,
    TriageFacts,
    TriageConflict,
    TriageResult,
    TriageStateError,
)


def evaluate_ticket(
    connection_string: str,
    ticket_id: UUID,
    facts: TriageFacts,
    expected_revision: int,
) -> TriageResult:
    with psycopg.connect(connection_string) as connection:
        ticket = lock_ticket(connection, ticket_id)
        if ticket is None:
            raise LookupError(f"Ticket not found: {ticket_id}")

        if ticket.status is TicketStatus.EM_TRIAGEM:
            if ticket.facts != facts:
                if ticket.facts_revision != expected_revision:
                    raise TriageConflict(
                        f"Expected revision {expected_revision}, "
                        f"found {ticket.facts_revision}"
                    )
                raise TriageStateError(
                    "A ticket in EM_TRIAGEM only accepts an identical retry"
                )
            return _result_from_snapshot(ticket)

        if ticket.status not in (
            TicketStatus.NOVO,
            TicketStatus.PENDENTE_INFORMACAO,
        ):
            raise TriageStateError(
                f"Ticket cannot be evaluated from status {ticket.status.value}"
            )

        catalog = load_active_catalog(connection)
        if (
            ticket.status is TicketStatus.PENDENTE_INFORMACAO
            and ticket.facts == facts
            and ticket.catalog_version == catalog.version_id
        ):
            return _result_from_snapshot(ticket)

        if ticket.facts_revision != expected_revision:
            raise TriageConflict(
                f"Expected revision {expected_revision}, "
                f"found {ticket.facts_revision}"
            )

        decision = evaluate_facts(facts, catalog)
        next_revision = ticket.facts_revision + 1
        save_evaluation(connection, ticket.id, decision, next_revision)
        append_evaluation_event(connection, ticket.id, ticket.status, decision)
        result = TriageResult(
            ticket_id=ticket.id,
            status=decision.status,
            facts=decision.facts,
            priority=decision.priority,
            target_team=decision.target_team,
            catalog_version=decision.catalog_version,
            facts_revision=next_revision,
        )

    return result


def _result_from_snapshot(ticket: TicketSnapshot) -> TriageResult:
    if ticket.catalog_version is None:
        raise CatalogConfigurationError(
            f"Ticket {ticket.id} has no persisted catalog version"
        )

    return TriageResult(
        ticket_id=ticket.id,
        status=ticket.status,
        facts=ticket.facts,
        priority=ticket.priority,
        target_team=ticket.target_team,
        catalog_version=ticket.catalog_version,
        facts_revision=ticket.facts_revision,
    )
