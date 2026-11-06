from uuid import uuid4

import psycopg
import pytest
from psycopg.errors import CheckViolation

from app.tickets.repository import create_ticket, get_ticket


def test_ticket_schema_defaults_and_constraints(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = uuid4()

    with psycopg.connect(owner_connection) as connection:
        row = connection.execute(
            """
            INSERT INTO tickets (id, description)
            VALUES (%s, %s)
            RETURNING id, description, status, created_at
            """,
            (ticket_id, "Disk failure"),
        ).fetchone()

    assert row is not None
    assert row[0] == ticket_id
    assert row[1] == "Disk failure"
    assert row[2] == "NOVO"
    assert row[3].utcoffset().total_seconds() == 0

    for invalid_description in ("\t\n ", "x" * 4001):
        with pytest.raises(CheckViolation):
            with psycopg.connect(owner_connection) as connection:
                connection.execute(
                    "INSERT INTO tickets (id, description) VALUES (%s, %s)",
                    (uuid4(), invalid_description),
                )


def test_create_commits_exactly_one_linked_audit_event(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles

    ticket = create_ticket(runtime_connection, "Disk failure")

    with psycopg.connect(owner_connection) as connection:
        stored_ticket = connection.execute(
            "SELECT id, description, status, created_at FROM tickets WHERE id = %s",
            (ticket.id,),
        ).fetchone()
        audit_events = connection.execute(
            """
            SELECT ticket_id, event_type
            FROM audit_events
            WHERE ticket_id = %s
            """,
            (ticket.id,),
        ).fetchall()

    assert stored_ticket is not None
    assert stored_ticket == (
        ticket.id,
        "Disk failure",
        "NOVO",
        ticket.created_at,
    )
    assert audit_events == [(ticket.id, "TICKET_CREATED")]


def test_audit_insert_failure_rolls_back_ticket(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    description = f"rollback-check-{uuid4()}"

    with psycopg.connect(owner_connection) as connection:
        connection.execute(
            """
            CREATE FUNCTION reject_audit_event() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                RAISE EXCEPTION 'forced audit insert failure';
            END;
            $$;
            CREATE TRIGGER reject_audit_event
            BEFORE INSERT ON audit_events
            FOR EACH ROW EXECUTE FUNCTION reject_audit_event();
            """
        )

    try:
        with pytest.raises(psycopg.errors.RaiseException):
            create_ticket(runtime_connection, description)
    finally:
        with psycopg.connect(owner_connection) as connection:
            connection.execute(
                """
                DROP TRIGGER IF EXISTS reject_audit_event ON audit_events;
                DROP FUNCTION IF EXISTS reject_audit_event();
                """
            )

    with psycopg.connect(owner_connection) as connection:
        ticket_count = connection.execute(
            "SELECT count(*) FROM tickets WHERE description = %s",
            (description,),
        ).fetchone()[0]
        event_count = connection.execute(
            """
            SELECT count(*)
            FROM audit_events AS events
            JOIN tickets ON tickets.id = events.ticket_id
            WHERE tickets.description = %s
            """,
            (description,),
        ).fetchone()[0]

    assert ticket_count == 0
    assert event_count == 0


def test_get_ticket_returns_persisted_ticket_fields(
    migrated_database_roles: tuple[str, str],
) -> None:
    _, runtime_connection = migrated_database_roles
    created_ticket = create_ticket(runtime_connection, "Network outage")

    retrieved_ticket = get_ticket(runtime_connection, created_ticket.id)

    assert retrieved_ticket == created_ticket


def test_get_ticket_returns_none_for_unknown_id(
    migrated_database_roles: tuple[str, str],
) -> None:
    _, runtime_connection = migrated_database_roles

    retrieved_ticket = get_ticket(runtime_connection, uuid4())

    assert retrieved_ticket is None
