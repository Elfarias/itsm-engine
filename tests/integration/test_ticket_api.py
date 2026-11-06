from datetime import datetime, timedelta
from uuid import UUID, uuid4

import psycopg
from fastapi.testclient import TestClient


def test_post_returns_uuid_novo_and_utc_timestamp(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    description = "Disk failure"

    response = api_client.post("/tickets", json={"description": description})

    assert response.status_code == 201
    payload = response.json()
    ticket_id = UUID(payload["id"])
    created_at = datetime.fromisoformat(payload["created_at"])
    assert ticket_id.version == 4
    assert payload["description"] == description
    assert payload["status"] == "NOVO"
    assert created_at.utcoffset() == timedelta(0)

    with psycopg.connect(owner_connection) as connection:
        stored_ticket = connection.execute(
            "SELECT id, description, status, created_at FROM tickets WHERE id = %s",
            (ticket_id,),
        ).fetchone()

    assert stored_ticket == (ticket_id, description, "NOVO", created_at)


def test_post_rejects_missing_blank_and_whitespace_descriptions(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    with psycopg.connect(owner_connection) as connection:
        before_count = connection.execute("SELECT count(*) FROM tickets").fetchone()[0]

    for body in ({}, {"description": ""}, {"description": " \t\n "}):
        response = api_client.post("/tickets", json=body)
        assert response.status_code == 422

    with psycopg.connect(owner_connection) as connection:
        after_count = connection.execute("SELECT count(*) FROM tickets").fetchone()[0]

    assert after_count == before_count


def test_post_rejects_description_over_4000_characters(
    api_client: TestClient,
) -> None:
    maximum_response = api_client.post(
        "/tickets",
        json={"description": "x" * 4000},
    )
    over_limit_response = api_client.post(
        "/tickets",
        json={"description": "x" * 4001},
    )

    assert maximum_response.status_code == 201
    assert len(maximum_response.json()["description"]) == 4000
    assert over_limit_response.status_code == 422


def test_repeated_posts_create_distinct_tickets(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    description = f"Repeated request {uuid4()}"

    first_response = api_client.post("/tickets", json={"description": description})
    second_response = api_client.post("/tickets", json={"description": description})

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    first_ticket_id = UUID(first_response.json()["id"])
    second_ticket_id = UUID(second_response.json()["id"])
    assert first_ticket_id != second_ticket_id

    with psycopg.connect(owner_connection) as connection:
        stored_count = connection.execute(
            "SELECT count(*) FROM tickets WHERE description = %s",
            (description,),
        ).fetchone()[0]

    assert stored_count == 2


def test_post_allows_unauthenticated_local_request(api_client: TestClient) -> None:
    response = api_client.post(
        "/tickets",
        json={"description": "Unauthenticated local request"},
    )

    assert response.status_code == 201
    assert response.json()["description"] == "Unauthenticated local request"


def test_audit_insert_failure_returns_503_and_rolls_back_ticket(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    description = f"api-rollback-{uuid4()}"

    with psycopg.connect(owner_connection) as connection:
        before_counts = connection.execute(
            """
            SELECT
                (SELECT count(*) FROM tickets),
                (SELECT count(*) FROM audit_events)
            """
        ).fetchone()
        connection.execute(
            """
            CREATE FUNCTION reject_api_audit_event() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                RAISE EXCEPTION 'forced API audit insert failure';
            END;
            $$;
            CREATE TRIGGER reject_api_audit_event
            BEFORE INSERT ON audit_events
            FOR EACH ROW EXECUTE FUNCTION reject_api_audit_event();
            """
        )

    try:
        response = api_client.post("/tickets", json={"description": description})
    finally:
        with psycopg.connect(owner_connection) as connection:
            connection.execute(
                """
                DROP TRIGGER IF EXISTS reject_api_audit_event ON audit_events;
                DROP FUNCTION IF EXISTS reject_api_audit_event();
                """
            )

    assert response.status_code == 503
    with psycopg.connect(owner_connection) as connection:
        after_counts = connection.execute(
            """
            SELECT
                (SELECT count(*) FROM tickets),
                (SELECT count(*) FROM audit_events)
            """
        ).fetchone()

    assert before_counts is not None
    assert after_counts == before_counts
