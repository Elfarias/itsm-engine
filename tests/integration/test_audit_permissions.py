import psycopg


def test_runtime_role_cannot_update_or_delete_audit_events(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, _ = migrated_database_roles

    with psycopg.connect(owner_connection) as connection:
        privileges = connection.execute(
            """
            SELECT
                has_table_privilege('itsm_runtime', 'public.audit_events', 'SELECT'),
                has_table_privilege('itsm_runtime', 'public.audit_events', 'INSERT'),
                has_table_privilege('itsm_runtime', 'public.audit_events', 'UPDATE'),
                has_table_privilege('itsm_runtime', 'public.audit_events', 'DELETE')
            """
        ).fetchone()

    assert privileges == (True, True, False, False)
