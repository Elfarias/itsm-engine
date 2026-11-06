import psycopg
import pytest

from app.tickets.repository import create_ticket
from app.tickets.schemas import TicketStatus
from app.triage.repository import (
    append_evaluation_event,
    lock_ticket,
    save_evaluation,
)
from app.triage.schemas import (
    EvaluationDecision,
    Impact,
    Priority,
    TriageFacts,
    Urgency,
)


def _complete_decision() -> EvaluationDecision:
    return EvaluationDecision(
        status=TicketStatus.EM_TRIAGEM,
        facts=TriageFacts(
            service_id="service-endpoint",
            asset_id="asset-laptop-001",
            impact=Impact.ALTO,
            urgency=Urgency.ALTA,
        ),
        priority=Priority.P1,
        target_team="team-workplace",
        catalog_version="catalog-v1",
    )


def test_evaluation_audit_records_catalog_version(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Endpoint failure")
    decision = _complete_decision()

    with psycopg.connect(runtime_connection) as connection:
        snapshot = lock_ticket(connection, ticket.id)
        assert snapshot is not None
        save_evaluation(connection, ticket.id, decision, 1)
        append_evaluation_event(connection, ticket.id, snapshot.status, decision)

    with psycopg.connect(owner_connection) as connection:
        stored_ticket = connection.execute(
            """
            SELECT service_id, asset_id, impact, urgency, priority,
                   target_team, catalog_version, status, facts_revision
            FROM tickets
            WHERE id = %s
            """,
            (ticket.id,),
        ).fetchone()
        event = connection.execute(
            """
            SELECT event_type, details
            FROM audit_events
            WHERE ticket_id = %s AND event_type = 'TICKET_TRIAGE_EVALUATED'
            """,
            (ticket.id,),
        ).fetchone()

    assert stored_ticket == (
        "service-endpoint",
        "asset-laptop-001",
        "ALTO",
        "ALTA",
        "P1",
        "team-workplace",
        "catalog-v1",
        "EM_TRIAGEM",
        1,
    )
    assert event == (
        "TICKET_TRIAGE_EVALUATED",
        {
            "previous_status": "NOVO",
            "status": "EM_TRIAGEM",
            "service_id": "service-endpoint",
            "asset_id": "asset-laptop-001",
            "impact": "ALTO",
            "urgency": "ALTA",
            "priority": "P1",
            "target_team": "team-workplace",
            "catalog_version": "catalog-v1",
        },
    )


def test_same_event_type_can_be_appended_more_than_once(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Intermittent endpoint issue")
    decision = _complete_decision()

    with psycopg.connect(runtime_connection) as connection:
        append_evaluation_event(connection, ticket.id, TicketStatus.NOVO, decision)
        append_evaluation_event(
            connection,
            ticket.id,
            TicketStatus.PENDENTE_INFORMACAO,
            decision,
        )

    with psycopg.connect(owner_connection) as connection:
        event_count = connection.execute(
            """
            SELECT count(*)
            FROM audit_events
            WHERE ticket_id = %s AND event_type = 'TICKET_TRIAGE_EVALUATED'
            """,
            (ticket.id,),
        ).fetchone()[0]

    assert event_count == 2


def test_audit_failure_rolls_back_evaluation(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Rollback triage evaluation")
    decision = _complete_decision()

    with psycopg.connect(owner_connection) as connection:
        connection.execute(
            """
            CREATE FUNCTION reject_triage_audit_event() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                IF NEW.event_type = 'TICKET_TRIAGE_EVALUATED' THEN
                    RAISE EXCEPTION 'forced triage audit failure';
                END IF;
                RETURN NEW;
            END;
            $$;
            CREATE TRIGGER reject_triage_audit_event
            BEFORE INSERT ON audit_events
            FOR EACH ROW EXECUTE FUNCTION reject_triage_audit_event();
            """
        )

    try:
        with pytest.raises(psycopg.errors.RaiseException):
            with psycopg.connect(runtime_connection) as connection:
                snapshot = lock_ticket(connection, ticket.id)
                assert snapshot is not None
                save_evaluation(connection, ticket.id, decision, 1)
                append_evaluation_event(
                    connection,
                    ticket.id,
                    snapshot.status,
                    decision,
                )
    finally:
        with psycopg.connect(owner_connection) as connection:
            connection.execute(
                """
                DROP TRIGGER IF EXISTS reject_triage_audit_event ON audit_events;
                DROP FUNCTION IF EXISTS reject_triage_audit_event();
                """
            )

    with psycopg.connect(owner_connection) as connection:
        ticket_state = connection.execute(
            """
            SELECT status, service_id, priority, target_team,
                   catalog_version, facts_revision
            FROM tickets
            WHERE id = %s
            """,
            (ticket.id,),
        ).fetchone()
        triage_events = connection.execute(
            """
            SELECT count(*)
            FROM audit_events
            WHERE ticket_id = %s AND event_type = 'TICKET_TRIAGE_EVALUATED'
            """,
            (ticket.id,),
        ).fetchone()[0]

    assert ticket_state == ("NOVO", None, None, None, None, 0)
    assert triage_events == 0
