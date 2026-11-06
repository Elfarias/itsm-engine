from uuid import uuid4

import psycopg
import pytest
from psycopg.errors import CheckViolation


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
