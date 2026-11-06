import os
import secrets
import socket
import subprocess
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = PROJECT_ROOT / "migrations" / "001_tickets_and_audit.sql"


@pytest.fixture(scope="session")
def database_roles() -> Iterator[tuple[str, str]]:
    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]

    owner_password = secrets.token_urlsafe(24)
    runtime_password = secrets.token_urlsafe(24)
    compose_project = f"itsm-test-{os.getpid()}"
    environment = os.environ.copy()
    environment["POSTGRES_OWNER_PASSWORD"] = owner_password
    environment["POSTGRES_RUNTIME_PASSWORD"] = runtime_password
    environment["POSTGRES_PORT"] = str(port)

    compose = ["docker", "compose", "-p", compose_project]
    owner_connection = (
        f"host=127.0.0.1 port={port} dbname=itsm "
        f"user=itsm_owner password={owner_password}"
    )
    runtime_connection = (
        f"host=127.0.0.1 port={port} dbname=itsm "
        f"user=itsm_runtime password={runtime_password}"
    )

    try:
        subprocess.run(
            [*compose, "up", "--detach", "--wait"],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            timeout=120,
        )
        with psycopg.connect(owner_connection, connect_timeout=10):
            pass
        yield owner_connection, runtime_connection
    finally:
        subprocess.run(
            [*compose, "down", "--volumes", "--remove-orphans"],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            timeout=60,
        )


@pytest.fixture(scope="session")
def migrated_database_roles(
    database_roles: tuple[str, str],
) -> tuple[str, str]:
    owner_connection, runtime_connection = database_roles
    migration = MIGRATION_PATH.read_text(encoding="utf-8")
    with psycopg.connect(owner_connection) as connection:
        connection.execute(migration)
    return owner_connection, runtime_connection
