from collections.abc import Iterator
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.triage.interpretation_schemas import InterpretationProposal
from app.triage.openrouter_client import (
    OpenRouterConfigurationError,
    OpenRouterError,
    OpenRouterInvalidResponse,
    OpenRouterUnavailable,
)


@pytest.fixture(autouse=True)
def activate_initial_catalog(
    migrated_database_roles: tuple[str, str],
) -> Iterator[None]:
    owner_connection, _ = migrated_database_roles
    with psycopg.connect(owner_connection) as connection:
        connection.execute("UPDATE catalog_versions SET is_active = FALSE")
        connection.execute(
            """
            UPDATE catalog_versions
            SET is_active = TRUE
            WHERE version_id = 'catalog-v1'
            """
        )
    yield


def _create_classified_ticket(
    api_client: TestClient,
    description: str,
) -> UUID:
    created = api_client.post("/tickets", json={"description": description})
    assert created.status_code == 201
    ticket_id = UUID(created.json()["id"])

    triaged = api_client.post(
        f"/tickets/{ticket_id}/triage",
        json={
            "expected_revision": 0,
            "facts": {
                "service_id": "service-endpoint",
                "asset_id": "asset-laptop-001",
                "impact": "ALTO",
                "urgency": "ALTA",
            },
        },
    )
    assert triaged.status_code == 200
    return ticket_id


def _ticket_snapshot(
    owner_connection: str,
    ticket_id: UUID,
) -> tuple[object, ...] | None:
    with psycopg.connect(owner_connection) as connection:
        return connection.execute(
            """
            SELECT id, description, status, created_at, service_id, asset_id,
                   impact, urgency, priority, target_team, catalog_version,
                   facts_revision
            FROM tickets
            WHERE id = %s
            """,
            (ticket_id,),
        ).fetchone()


def _audit_snapshot(
    owner_connection: str,
    ticket_id: UUID,
) -> list[tuple[object, ...]]:
    with psycopg.connect(owner_connection) as connection:
        return connection.execute(
            """
            SELECT id, event_type, occurred_at, details
            FROM audit_events
            WHERE ticket_id = %s
            ORDER BY occurred_at, id
            """,
            (ticket_id,),
        ).fetchall()


def _proposal() -> InterpretationProposal:
    return InterpretationProposal.model_validate(
        {
            "service_candidate": "Serviço de endpoint",
            "asset_candidate": "Laptop do usuário",
            "impact": "ALTO",
            "urgency": "ALTA",
            "symptoms": ["Falha de acesso"],
            "impact_evidence": ["Afeta múltiplos usuários"],
            "urgency_evidence": ["Atividade bloqueada"],
            "missing_information": [],
            "uncertainties": [],
            "technical_summary": "Falha ampla de acesso.",
        }
    )


def test_interpretation_returns_proposal_for_existing_ticket(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_connection, _ = migrated_database_roles
    description = "private-description: endpoint access is unavailable"
    ticket_id = _create_classified_ticket(api_client, description)
    ticket_before = _ticket_snapshot(owner_connection, ticket_id)
    audit_before = _audit_snapshot(owner_connection, ticket_id)
    proposal = _proposal()
    received_descriptions: list[str] = []

    def fake_interpretation(
        received_description: str,
    ) -> InterpretationProposal:
        received_descriptions.append(received_description)
        return proposal

    monkeypatch.setattr(
        "app.tickets.routes.interpret_description",
        fake_interpretation,
    )

    response = api_client.post(f"/tickets/{ticket_id}/interpretation")

    assert response.status_code == 200
    assert response.json() == {
        **proposal.model_dump(mode="json"),
        "ticket_id": str(ticket_id),
    }
    assert received_descriptions == [description]
    assert _ticket_snapshot(owner_connection, ticket_id) == ticket_before
    assert _audit_snapshot(owner_connection, ticket_id) == audit_before


def test_missing_and_unavailable_ticket_lookups_return_without_provider_call(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_calls: list[str] = []

    def fake_interpretation(description: str) -> InterpretationProposal:
        provider_calls.append(description)
        return _proposal()

    monkeypatch.setattr(
        "app.tickets.routes.interpret_description",
        fake_interpretation,
    )

    missing_response = api_client.post(f"/tickets/{uuid4()}/interpretation")

    def fail_lookup(connection_string: str, ticket_id: UUID) -> None:
        raise psycopg.OperationalError("database unavailable")

    monkeypatch.setattr("app.tickets.routes.get_ticket", fail_lookup)
    unavailable_response = api_client.post(f"/tickets/{uuid4()}/interpretation")

    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Ticket not found"}
    assert unavailable_response.status_code == 503
    assert unavailable_response.json() == {
        "detail": "Ticket interpretation unavailable"
    }
    assert provider_calls == []


@pytest.mark.parametrize(
    ("error_type", "expected_status", "expected_detail"),
    [
        (
            OpenRouterConfigurationError,
            503,
            "Ticket interpretation unavailable",
        ),
        (
            OpenRouterUnavailable,
            503,
            "Ticket interpretation unavailable",
        ),
        (
            OpenRouterInvalidResponse,
            502,
            "Ticket interpretation returned an invalid provider response",
        ),
    ],
)
def test_provider_failures_return_errors_without_ticket_or_audit_changes(
    api_client: TestClient,
    migrated_database_roles: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[OpenRouterError],
    expected_status: int,
    expected_detail: str,
) -> None:
    owner_connection, _ = migrated_database_roles
    ticket_id = _create_classified_ticket(api_client, "Sensitive incident details")
    ticket_before = _ticket_snapshot(owner_connection, ticket_id)
    audit_before = _audit_snapshot(owner_connection, ticket_id)

    def fail_interpretation(description: str) -> InterpretationProposal:
        raise error_type("sensitive provider failure")

    monkeypatch.setattr(
        "app.tickets.routes.interpret_description",
        fail_interpretation,
    )

    response = api_client.post(f"/tickets/{ticket_id}/interpretation")

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    assert _ticket_snapshot(owner_connection, ticket_id) == ticket_before
    assert _audit_snapshot(owner_connection, ticket_id) == audit_before


def test_interpretation_does_not_log_sensitive_content(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    description = "private-description-923"
    api_key = "private-api-key-581"
    prompt = "private-prompt-742"
    provider_response = "private-provider-response-619"
    created = api_client.post("/tickets", json={"description": description})
    assert created.status_code == 201
    ticket_id = UUID(created.json()["id"])
    monkeypatch.setenv("OPENROUTER_API_KEY", api_key)

    def fail_interpretation(received_description: str) -> InterpretationProposal:
        raise OpenRouterUnavailable(
            f"{prompt} {provider_response} {api_key} {received_description}"
        )

    monkeypatch.setattr(
        "app.tickets.routes.interpret_description",
        fail_interpretation,
    )

    response = api_client.post(f"/tickets/{ticket_id}/interpretation")

    assert response.status_code == 503
    assert response.json() == {"detail": "Ticket interpretation unavailable"}
    assert all(
        sensitive_value not in caplog.text
        for sensitive_value in (description, api_key, prompt, provider_response)
    )
