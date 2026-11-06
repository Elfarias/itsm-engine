import psycopg
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
        assets = connection.execute(
            """
            SELECT asset_id, service_id
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
    assert assets == [
        ("asset-laptop-001", "service-endpoint"),
        ("asset-router-001", "service-connectivity"),
    ]


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
    paths = response.json()["paths"]
    assert not any(
        "catalog" in path.lower() or "triage" in path.lower()
        for path in paths
    )
