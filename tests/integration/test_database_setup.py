import psycopg


def test_database_is_ready_and_roles_are_distinct(
    database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = database_roles

    with psycopg.connect(owner_connection) as owner:
        owner_name = owner.execute("SELECT current_user").fetchone()[0]

    with psycopg.connect(runtime_connection) as runtime:
        runtime_name = runtime.execute("SELECT current_user").fetchone()[0]

    assert owner_name == "itsm_owner"
    assert runtime_name == "itsm_runtime"
    assert runtime_name != owner_name
