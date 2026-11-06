from uuid import uuid4

import psycopg

from app.tickets.schemas import TicketResponse


def create_ticket(connection_string: str, description: str) -> TicketResponse:
    ticket_id = uuid4()
    audit_event_id = uuid4()

    with psycopg.connect(connection_string) as connection:
        ticket = connection.execute(
            """
            INSERT INTO tickets (id, description)
            VALUES (%s, %s)
            RETURNING id, description, status, created_at
            """,
            (ticket_id, description),
        ).fetchone()
        if ticket is None:
            raise RuntimeError("Ticket insert returned no row")

        connection.execute(
            """
            INSERT INTO audit_events (id, ticket_id, event_type)
            VALUES (%s, %s, %s)
            """,
            (audit_event_id, ticket_id, "TICKET_CREATED"),
        )

    return TicketResponse(
        id=ticket[0],
        description=ticket[1],
        status=ticket[2],
        created_at=ticket[3],
    )
