from dataclasses import dataclass
from uuid import UUID, uuid4

from psycopg import Connection
from psycopg.types.json import Jsonb

from app.tickets.schemas import TicketStatus
from app.triage.schemas import (
    CatalogConfigurationError,
    CatalogSnapshot,
    EvaluationDecision,
    Impact,
    Priority,
    TriageFacts,
    Urgency,
)


@dataclass(frozen=True)
class TicketSnapshot:
    id: UUID
    status: TicketStatus
    facts: TriageFacts
    priority: Priority | None
    target_team: str | None
    catalog_version: str | None
    facts_revision: int


def lock_ticket(connection: Connection, ticket_id: UUID) -> TicketSnapshot | None:
    ticket = connection.execute(
        """
        SELECT id, status, service_id, asset_id, impact, urgency, priority,
               target_team, catalog_version, facts_revision
        FROM tickets
        WHERE id = %s
        FOR UPDATE
        """,
        (ticket_id,),
    ).fetchone()
    if ticket is None:
        return None

    return TicketSnapshot(
        id=ticket[0],
        status=TicketStatus(ticket[1]),
        facts=TriageFacts(
            service_id=ticket[2],
            asset_id=ticket[3],
            impact=Impact(ticket[4]) if ticket[4] is not None else None,
            urgency=Urgency(ticket[5]) if ticket[5] is not None else None,
        ),
        priority=Priority(ticket[6]) if ticket[6] is not None else None,
        target_team=ticket[7],
        catalog_version=ticket[8],
        facts_revision=ticket[9],
    )


def load_active_catalog(connection: Connection) -> CatalogSnapshot:
    active_version = connection.execute(
        """
        SELECT version_id
        FROM catalog_versions
        WHERE is_active
        """
    ).fetchone()
    if active_version is None:
        raise CatalogConfigurationError("No active catalog version")

    version_id = active_version[0]
    services = frozenset(
        row[0]
        for row in connection.execute(
            "SELECT service_id FROM cmdb_services WHERE version_id = %s",
            (version_id,),
        ).fetchall()
    )
    asset_services = dict(
        connection.execute(
            """
            SELECT asset_id, service_id
            FROM cmdb_assets
            WHERE version_id = %s
            """,
            (version_id,),
        ).fetchall()
    )
    service_teams = dict(
        connection.execute(
            """
            SELECT service_id, team_id
            FROM service_team_mappings
            WHERE version_id = %s
            """,
            (version_id,),
        ).fetchall()
    )

    return CatalogSnapshot(
        version_id=version_id,
        services=services,
        asset_services=asset_services,
        service_teams=service_teams,
    )


def save_evaluation(
    connection: Connection,
    ticket_id: UUID,
    decision: EvaluationDecision,
    next_revision: int,
) -> None:
    result = connection.execute(
        """
        UPDATE tickets
        SET service_id = %s,
            asset_id = %s,
            impact = %s,
            urgency = %s,
            priority = %s,
            target_team = %s,
            catalog_version = %s,
            status = %s,
            facts_revision = %s
        WHERE id = %s
        """,
        (
            decision.facts.service_id,
            decision.facts.asset_id,
            decision.facts.impact.value if decision.facts.impact else None,
            decision.facts.urgency.value if decision.facts.urgency else None,
            decision.priority.value if decision.priority else None,
            decision.target_team,
            decision.catalog_version,
            decision.status.value,
            next_revision,
            ticket_id,
        ),
    )
    if result.rowcount != 1:
        raise LookupError(f"Ticket not found: {ticket_id}")


def append_evaluation_event(
    connection: Connection,
    ticket_id: UUID,
    previous_status: TicketStatus,
    decision: EvaluationDecision,
) -> None:
    details = {
        "previous_status": previous_status.value,
        "status": decision.status.value,
        "service_id": decision.facts.service_id,
        "asset_id": decision.facts.asset_id,
        "impact": decision.facts.impact.value if decision.facts.impact else None,
        "urgency": decision.facts.urgency.value if decision.facts.urgency else None,
        "priority": decision.priority.value if decision.priority else None,
        "target_team": decision.target_team,
        "catalog_version": decision.catalog_version,
    }
    connection.execute(
        """
        INSERT INTO audit_events (id, ticket_id, event_type, details)
        VALUES (%s, %s, %s, %s)
        """,
        (uuid4(), ticket_id, "TICKET_TRIAGE_EVALUATED", Jsonb(details)),
    )
