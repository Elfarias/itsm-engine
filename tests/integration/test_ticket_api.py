import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

import psycopg
from fastapi.testclient import TestClient

from app.tickets.repository import create_ticket


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _start_server(port: int, database_url: str) -> subprocess.Popen[bytes]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Uvicorn exited with status {process.returncode}")
        try:
            with urlopen(f"{base_url}/openapi.json", timeout=1):
                return process
        except (URLError, TimeoutError):
            time.sleep(0.1)

    _stop_server(process)
    raise TimeoutError("Uvicorn did not become ready")


def _stop_server(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _request_json(
    method: str,
    url: str,
    payload: dict[str, str] | None = None,
) -> tuple[int, dict[str, str]]:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read())

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


def test_local_ticket_endpoints_accept_requests_without_auth(
    api_client: TestClient,
) -> None:
    create_response = api_client.post(
        "/tickets",
        json={"description": "Unauthenticated local request"},
    )
    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]
    read_response = api_client.get(f"/tickets/{ticket_id}")

    assert read_response.status_code == 200
    assert read_response.json() == create_response.json()


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


def test_get_returns_persisted_ticket_fields(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    created_ticket = create_ticket(runtime_connection, "Network outage")

    response = api_client.get(f"/tickets/{created_ticket.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(created_ticket.id)
    assert payload["description"] == "Network outage"
    assert payload["status"] == "NOVO"
    assert datetime.fromisoformat(payload["created_at"]) == created_ticket.created_at

    with psycopg.connect(owner_connection) as connection:
        stored_ticket = connection.execute(
            "SELECT id, description, status, created_at FROM tickets WHERE id = %s",
            (created_ticket.id,),
        ).fetchone()

    assert stored_ticket == (
        created_ticket.id,
        payload["description"],
        payload["status"],
        datetime.fromisoformat(payload["created_at"]),
    )


def test_get_missing_ticket_returns_404(api_client: TestClient) -> None:
    response = api_client.get(f"/tickets/{uuid4()}")

    assert response.status_code == 404


def test_get_invalid_uuid_returns_422(api_client: TestClient) -> None:
    response = api_client.get("/tickets/not-a-uuid")

    assert response.status_code == 422


def test_get_returns_ticket_after_app_restart(
    migrated_database_roles: tuple[str, str],
) -> None:
    _, runtime_connection = migrated_database_roles
    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]

    base_url = f"http://127.0.0.1:{port}"
    description = f"restart-check-{uuid4()}"
    first_process = _start_server(port, runtime_connection)
    try:
        create_status, created_ticket = _request_json(
            "POST",
            f"{base_url}/tickets",
            {"description": description},
        )
        assert create_status == 201
    finally:
        _stop_server(first_process)

    second_process = _start_server(port, runtime_connection)
    try:
        read_status, retrieved_ticket = _request_json(
            "GET",
            f"{base_url}/tickets/{created_ticket['id']}",
        )
    finally:
        _stop_server(second_process)

    assert read_status == 200
    assert retrieved_ticket == created_ticket
