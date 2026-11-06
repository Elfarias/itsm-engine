from collections.abc import Iterator
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from httpx import Response


@pytest.fixture(autouse=True)
def reset_active_catalog(
    migrated_database_roles: tuple[str, str],
) -> Iterator[None]:
    owner_connection, _ = migrated_database_roles
    _activate_initial_catalog(owner_connection)
    yield
    _activate_initial_catalog(owner_connection)


def _activate_initial_catalog(owner_connection: str) -> None:
    with psycopg.connect(owner_connection) as connection:
        connection.execute(
            "UPDATE catalog_versions SET is_active = FALSE WHERE is_active"
        )
        connection.execute(
            """
            UPDATE catalog_versions
            SET is_active = TRUE
            WHERE version_id = 'catalog-v1'
            """
        )


def _activate_catalog_version(
    owner_connection: str,
    *,
    remap_endpoint: bool = False,
    remap_router: bool = False,
) -> str:
    version_id = f"catalog-v2-{uuid4().hex[:8]}"
    with psycopg.connect(owner_connection) as connection:
        connection.execute(
            "UPDATE catalog_versions SET is_active = FALSE WHERE is_active"
        )
        connection.execute(
            """
            INSERT INTO catalog_versions (version_id, is_active)
            VALUES (%s, TRUE)
            """,
            (version_id,),
        )
        connection.execute(
            """
            INSERT INTO cmdb_services (version_id, service_id, name)
            SELECT %s, service_id, name
            FROM cmdb_services
            WHERE version_id = 'catalog-v1'
            """,
            (version_id,),
        )
        connection.execute(
            """
            INSERT INTO support_teams (version_id, team_id, name)
            SELECT %s, team_id, name
            FROM support_teams
            WHERE version_id = 'catalog-v1'
            """,
            (version_id,),
        )
        assets = connection.execute(
            """
            SELECT asset_id, service_id, name
            FROM cmdb_assets
            WHERE version_id = 'catalog-v1'
            """
        ).fetchall()
        for asset_id, service_id, name in assets:
            if remap_router and asset_id == "asset-router-001":
                service_id = "service-endpoint"
            connection.execute(
                """
                INSERT INTO cmdb_assets (version_id, asset_id, service_id, name)
                VALUES (%s, %s, %s, %s)
                """,
                (version_id, asset_id, service_id, name),
            )

        mappings = connection.execute(
            """
            SELECT service_id, team_id
            FROM service_team_mappings
            WHERE version_id = 'catalog-v1'
            """
        ).fetchall()
        for service_id, team_id in mappings:
            if remap_endpoint and service_id == "service-endpoint":
                team_id = "team-network"
            connection.execute(
                """
                INSERT INTO service_team_mappings (version_id, service_id, team_id)
                VALUES (%s, %s, %s)
                """,
                (version_id, service_id, team_id),
            )
    return version_id


def _create_ticket(api_client: TestClient, description: str) -> UUID:
    response = api_client.post("/tickets", json={"description": description})
    assert response.status_code == 201
    return UUID(response.json()["id"])


def _complete_facts(asset_id: str = "asset-laptop-001") -> dict[str, str]:
    return {
        "service_id": "service-endpoint",
        "asset_id": asset_id,
        "impact": "ALTO",
        "urgency": "ALTA",
    }


def _post_triage(
    api_client: TestClient,
    ticket_id: UUID,
    facts: dict[str, str],
    expected_revision: int = 0,
) -> Response:
    return api_client.post(
        f"/tickets/{ticket_id}/triage",
        json={"expected_revision": expected_revision, "facts": facts},
    )


def _stored_ticket(
    owner_connection: str,
    ticket_id: UUID,
) -> tuple[object, ...] | None:
    with psycopg.connect(owner_connection) as connection:
        return connection.execute(
            """
            SELECT status, service_id, asset_id, impact, urgency, priority,
                   target_team, catalog_version, facts_revision
            FROM tickets
            WHERE id = %s
            """,
            (ticket_id,),
        ).fetchone()


def _evaluation_event_count(owner_connection: str, ticket_id: UUID) -> int:
    with psycopg.connect(owner_connection) as connection:
        return connection.execute(
            """
            SELECT count(*)
            FROM audit_events
            WHERE ticket_id = %s AND event_type = 'TICKET_TRIAGE_EVALUATED'
            """,
            (ticket_id,),
        ).fetchone()[0]


def test_complete_triage_returns_persisted_result(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = _create_ticket(api_client, "Endpoint failure")
    facts = _complete_facts()

    response = _post_triage(api_client, ticket_id, facts)

    assert response.status_code == 200
    assert response.json() == {
        "ticket_id": str(ticket_id),
        "status": "EM_TRIAGEM",
        "facts": facts,
        "priority": "P1",
        "target_team": "team-workplace",
        "catalog_version": "catalog-v1",
        "facts_revision": 1,
    }
    assert _stored_ticket(owner_connection, ticket_id) == (
        "EM_TRIAGEM",
        "service-endpoint",
        "asset-laptop-001",
        "ALTO",
        "ALTA",
        "P1",
        "team-workplace",
        "catalog-v1",
        1,
    )


def test_partial_and_conflicting_facts_return_pending(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    cases = (
        (
            "Missing urgency",
            {"service_id": "service-endpoint", "impact": "ALTO"},
        ),
        ("Asset service conflict", _complete_facts("asset-router-001")),
    )

    for description, facts in cases:
        ticket_id = _create_ticket(api_client, description)

        response = _post_triage(api_client, ticket_id, facts)

        assert response.status_code == 200
        payload = response.json()
        assert payload["ticket_id"] == str(ticket_id)
        assert payload["status"] == "PENDENTE_INFORMACAO"
        assert payload["facts"] == {
            "service_id": facts.get("service_id"),
            "asset_id": facts.get("asset_id"),
            "impact": facts.get("impact"),
            "urgency": facts.get("urgency"),
        }
        assert payload["priority"] is None
        assert payload["target_team"] is None
        assert payload["catalog_version"] == "catalog-v1"
        assert payload["facts_revision"] == 1
        assert _stored_ticket(owner_connection, ticket_id) == (
            "PENDENTE_INFORMACAO",
            facts.get("service_id"),
            facts.get("asset_id"),
            facts.get("impact"),
            facts.get("urgency"),
            None,
            None,
            "catalog-v1",
            1,
        )


def test_missing_ticket_returns_404(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = uuid4()

    response = _post_triage(api_client, ticket_id, _complete_facts())

    assert response.status_code == 404
    assert _stored_ticket(owner_connection, ticket_id) is None
    assert _evaluation_event_count(owner_connection, ticket_id) == 0


def test_invalid_request_and_catalog_facts_return_422_without_changes(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = _create_ticket(api_client, "Invalid triage requests")
    before = _stored_ticket(owner_connection, ticket_id)
    invalid_requests = (
        (
            f"/tickets/{ticket_id}/triage",
            {"expected_revision": 0, "facts": {}, "unexpected": True},
        ),
        (
            f"/tickets/{ticket_id}/triage",
            {"expected_revision": 0, "facts": {"impact": "CRITICO"}},
        ),
        (
            f"/tickets/{ticket_id}/triage",
            {
                "expected_revision": 0,
                "facts": {
                    "service_id": "service-unknown",
                    "impact": "ALTO",
                    "urgency": "ALTA",
                },
            },
        ),
        (
            f"/tickets/{ticket_id}/triage",
            {
                "expected_revision": 0,
                "facts": {
                    "service_id": "service-endpoint",
                    "asset_id": "asset-unknown",
                    "impact": "ALTO",
                    "urgency": "ALTA",
                },
            },
        ),
        (
            "/tickets/not-a-uuid/triage",
            {"expected_revision": 0, "facts": _complete_facts()},
        ),
    )

    for path, payload in invalid_requests:
        response = api_client.post(path, json=payload)
        assert response.status_code == 422

    assert _stored_ticket(owner_connection, ticket_id) == before
    assert _evaluation_event_count(owner_connection, ticket_id) == 0


def test_stale_revision_and_invalid_state_return_409(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = _create_ticket(api_client, "Revision conflict")

    stale_response = _post_triage(
        api_client,
        ticket_id,
        _complete_facts(),
        expected_revision=1,
    )
    before_success = _stored_ticket(owner_connection, ticket_id)
    success = _post_triage(api_client, ticket_id, _complete_facts())
    incompatible_response = _post_triage(
        api_client,
        ticket_id,
        _complete_facts("asset-router-001"),
        expected_revision=1,
    )

    assert stale_response.status_code == 409
    assert before_success == (
        "NOVO",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        0,
    )
    assert success.status_code == 200
    assert incompatible_response.status_code == 409
    assert _stored_ticket(owner_connection, ticket_id) == (
        "EM_TRIAGEM",
        "service-endpoint",
        "asset-laptop-001",
        "ALTO",
        "ALTA",
        "P1",
        "team-workplace",
        "catalog-v1",
        1,
    )
    assert _evaluation_event_count(owner_connection, ticket_id) == 1


def test_pending_identical_retry_is_idempotent(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = _create_ticket(api_client, "Pending retry")
    facts = {"service_id": "service-endpoint", "impact": "ALTO"}

    first_response = _post_triage(api_client, ticket_id, facts)
    first_payload = first_response.json()
    retry_response = _post_triage(
        api_client,
        ticket_id,
        facts,
        expected_revision=first_payload["facts_revision"],
    )

    assert first_response.status_code == 200
    assert first_payload["status"] == "PENDENTE_INFORMACAO"
    assert retry_response.status_code == 200
    assert retry_response.json() == first_payload
    assert _stored_ticket(owner_connection, ticket_id) == (
        "PENDENTE_INFORMACAO",
        "service-endpoint",
        None,
        "ALTO",
        None,
        None,
        None,
        "catalog-v1",
        1,
    )
    assert _evaluation_event_count(owner_connection, ticket_id) == 1


def test_pending_retry_uses_new_active_catalog_version(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = _create_ticket(api_client, "Pending catalog change")
    facts = _complete_facts("asset-router-001")
    first_response = _post_triage(api_client, ticket_id, facts)
    catalog_version = _activate_catalog_version(
        owner_connection,
        remap_endpoint=True,
        remap_router=True,
    )

    retry_response = _post_triage(
        api_client,
        ticket_id,
        facts,
        expected_revision=first_response.json()["facts_revision"],
    )

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "PENDENTE_INFORMACAO"
    assert retry_response.status_code == 200
    assert retry_response.json() == {
        "ticket_id": str(ticket_id),
        "status": "EM_TRIAGEM",
        "facts": facts,
        "priority": "P1",
        "target_team": "team-network",
        "catalog_version": catalog_version,
        "facts_revision": 2,
    }
    assert _stored_ticket(owner_connection, ticket_id) == (
        "EM_TRIAGEM",
        "service-endpoint",
        "asset-router-001",
        "ALTO",
        "ALTA",
        "P1",
        "team-network",
        catalog_version,
        2,
    )
    assert _evaluation_event_count(owner_connection, ticket_id) == 2


def test_em_triagem_retry_returns_stored_catalog_version(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = _create_ticket(api_client, "Completed retry")
    facts = _complete_facts()
    first_response = _post_triage(api_client, ticket_id, facts)
    _activate_catalog_version(owner_connection, remap_endpoint=True)

    retry_response = _post_triage(
        api_client,
        ticket_id,
        facts,
        expected_revision=first_response.json()["facts_revision"],
    )

    assert first_response.status_code == 200
    assert retry_response.status_code == 200
    assert retry_response.json() == first_response.json()
    assert retry_response.json()["catalog_version"] == "catalog-v1"
    assert retry_response.json()["target_team"] == "team-workplace"
    assert _stored_ticket(owner_connection, ticket_id) == (
        "EM_TRIAGEM",
        "service-endpoint",
        "asset-laptop-001",
        "ALTO",
        "ALTA",
        "P1",
        "team-workplace",
        "catalog-v1",
        1,
    )
    assert _evaluation_event_count(owner_connection, ticket_id) == 1


def test_evaluation_or_audit_failure_returns_503_without_partial_changes(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = _create_ticket(api_client, "Audit rollback")
    before = _stored_ticket(owner_connection, ticket_id)
    with psycopg.connect(owner_connection) as connection:
        connection.execute(
            """
            CREATE FUNCTION reject_triage_api_audit_event() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                IF NEW.event_type = 'TICKET_TRIAGE_EVALUATED' THEN
                    RAISE EXCEPTION 'forced triage audit insert failure';
                END IF;
                RETURN NEW;
            END;
            $$;
            CREATE TRIGGER reject_triage_api_audit_event
            BEFORE INSERT ON audit_events
            FOR EACH ROW EXECUTE FUNCTION reject_triage_api_audit_event();
            """
        )

    try:
        response = _post_triage(api_client, ticket_id, _complete_facts())
    finally:
        with psycopg.connect(owner_connection) as connection:
            connection.execute(
                """
                DROP TRIGGER IF EXISTS reject_triage_api_audit_event ON audit_events;
                DROP FUNCTION IF EXISTS reject_triage_api_audit_event();
                """
            )

    assert response.status_code == 503
    assert _stored_ticket(owner_connection, ticket_id) == before
    assert _evaluation_event_count(owner_connection, ticket_id) == 0


def test_missing_active_catalog_returns_503(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = _create_ticket(api_client, "Missing active catalog")
    before = _stored_ticket(owner_connection, ticket_id)
    with psycopg.connect(owner_connection) as connection:
        connection.execute(
            "UPDATE catalog_versions SET is_active = FALSE WHERE is_active"
        )

    response = _post_triage(api_client, ticket_id, _complete_facts())

    assert response.status_code == 503
    assert _stored_ticket(owner_connection, ticket_id) == before
    assert _evaluation_event_count(owner_connection, ticket_id) == 0
