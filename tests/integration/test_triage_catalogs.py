from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient


def test_catalog_seed_is_versioned_and_referentially_consistent(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles

    with psycopg.connect(owner_connection) as connection:
        active_versions = connection.execute(
            """
            SELECT version_id
            FROM catalog_versions
            WHERE is_active
            """
        ).fetchall()
        assert active_versions == [("catalog-v1",)]
        service_mappings = connection.execute(
            """
            SELECT service_id, team_id
            FROM service_team_mappings
            WHERE version_id = %s
            ORDER BY service_id
            """,
            (active_versions[0][0],),
        ).fetchall()
        services = connection.execute(
            """
            SELECT service_id, name
            FROM cmdb_services
            WHERE version_id = %s
            ORDER BY service_id
            """,
            (active_versions[0][0],),
        ).fetchall()
        teams = connection.execute(
            """
            SELECT team_id, name
            FROM support_teams
            WHERE version_id = %s
            ORDER BY team_id
            """,
            (active_versions[0][0],),
        ).fetchall()
        assets = connection.execute(
            """
            SELECT asset_id, service_id, name
            FROM cmdb_assets
            WHERE version_id = %s
            ORDER BY asset_id
            """,
            (active_versions[0][0],),
        ).fetchall()

    assert service_mappings == [
        ("service-connectivity", "team-network"),
        ("service-endpoint", "team-workplace"),
    ]
    assert services == [
        ("service-connectivity", "Synthetic Network Connectivity"),
        ("service-endpoint", "Synthetic Endpoint Management"),
    ]
    assert teams == [
        ("team-network", "Synthetic Network Operations"),
        ("team-workplace", "Synthetic Workplace Support"),
    ]
    assert assets == [
        (
            "asset-laptop-001",
            "service-endpoint",
            "Synthetic Laptop 001",
        ),
        (
            "asset-router-001",
            "service-connectivity",
            "Synthetic Router 001",
        ),
    ]

    assert all(
        name.startswith("Synthetic ")
        for records in (services, teams)
        for _, name in records
    )
    assert all(name.startswith("Synthetic ") for _, _, name in assets)
    _assert_catalog_and_ticket_constraints(migrated_database_roles)


def _assert_catalog_and_ticket_constraints(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = uuid4()

    with psycopg.connect(owner_connection) as connection:
        connection.execute(
            """
            INSERT INTO tickets (id, description)
            VALUES (%s, 'Validate database constraints')
            """,
            (ticket_id,),
        )

        with pytest.raises(psycopg.errors.UniqueViolation):
            with connection.transaction():
                connection.execute(
                    """
                    INSERT INTO catalog_versions (version_id, is_active)
                    VALUES ('catalog-v2-duplicate-active', TRUE)
                    """
                )

        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            with connection.transaction():
                connection.execute(
                    """
                    UPDATE service_team_mappings
                    SET team_id = 'team-unknown'
                    WHERE version_id = 'catalog-v1'
                      AND service_id = 'service-endpoint'
                    """
                )

        with pytest.raises(psycopg.errors.CheckViolation):
            with connection.transaction():
                connection.execute(
                    """
                    INSERT INTO cmdb_services (version_id, service_id, name)
                    VALUES ('catalog-v1', ' ', 'Invalid blank service')
                    """
                )

        invalid_ticket_updates = (
            ("impact", "CRITICO"),
            ("urgency", "URGENTE"),
            ("priority", "P0"),
            ("facts_revision", -1),
        )
        for column, value in invalid_ticket_updates:
            with pytest.raises(psycopg.errors.CheckViolation):
                with connection.transaction():
                    connection.execute(
                        f"UPDATE tickets SET {column} = %s WHERE id = %s",
                        (value, ticket_id),
                    )

        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            with connection.transaction():
                connection.execute(
                    """
                    UPDATE tickets
                    SET catalog_version = 'catalog-v1',
                        service_id = 'service-endpoint',
                        target_team = 'team-network'
                    WHERE id = %s
                    """,
                    (ticket_id,),
                )

        ticket_state = connection.execute(
            """
            SELECT status, impact, urgency, priority, catalog_version,
                   facts_revision
            FROM tickets
            WHERE id = %s
            """,
            (ticket_id,),
        ).fetchone()

    assert ticket_state == ("NOVO", None, None, None, None, 0)


def test_runtime_role_can_read_but_not_write_catalogs(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles

    with psycopg.connect(owner_connection) as connection:
        catalog_privileges = connection.execute(
            """
            SELECT
                has_table_privilege('itsm_runtime', 'public.cmdb_services', 'SELECT'),
                has_table_privilege('itsm_runtime', 'public.cmdb_services', 'INSERT'),
                has_table_privilege('itsm_runtime', 'public.cmdb_services', 'UPDATE'),
                has_table_privilege('itsm_runtime', 'public.cmdb_services', 'DELETE')
            """
        ).fetchone()
        ticket_update_privileges = connection.execute(
            """
            SELECT
                has_column_privilege('itsm_runtime', 'public.tickets', 'status', 'UPDATE'),
                has_column_privilege('itsm_runtime', 'public.tickets', 'description', 'UPDATE')
            """
        ).fetchone()
        audit_update_privileges = connection.execute(
            """
            SELECT
                has_table_privilege('itsm_runtime', 'public.audit_events', 'UPDATE'),
                has_table_privilege('itsm_runtime', 'public.audit_events', 'DELETE')
            """
        ).fetchone()

    assert catalog_privileges == (True, False, False, False)
    assert ticket_update_privileges == (True, False)
    assert audit_update_privileges == (False, False)


def test_public_api_exposes_no_catalog_admin_routes(api_client: TestClient) -> None:
    response = api_client.get("/openapi.json")

    assert response.status_code == 200
    operations = {
        path: {
            method
            for method in path_item
            if method in {"get", "post", "put", "patch", "delete"}
        }
        for path, path_item in response.json()["paths"].items()
    }
    assert operations == {
        "/tickets": {"post"},
        "/tickets/{ticket_id}": {"get"},
        "/tickets/{ticket_id}/interpretation": {"post"},
        "/tickets/{ticket_id}/triage": {"post"},
    }
