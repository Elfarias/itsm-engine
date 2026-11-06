from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import psycopg
import pytest
from pydantic import ValidationError

from app.tickets.repository import create_ticket
from app.tickets.schemas import TicketStatus
from app.triage.schemas import (
    Impact,
    InvalidTriageFacts,
    Priority,
    TriageConflict,
    TriageFacts,
    TriageStateError,
    Urgency,
)
from app.triage.service import evaluate_ticket


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
    include_unmapped_service: bool = False,
    remap_endpoint: bool = False,
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
        connection.execute(
            """
            INSERT INTO cmdb_assets (version_id, asset_id, service_id, name)
            SELECT %s, asset_id, service_id, name
            FROM cmdb_assets
            WHERE version_id = 'catalog-v1'
            """,
            (version_id,),
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
        if include_unmapped_service:
            connection.execute(
                """
                INSERT INTO cmdb_services (version_id, service_id, name)
                VALUES (%s, 'service-unmapped', 'Synthetic Unmapped Service')
                """,
                (version_id,),
            )
    return version_id


def _complete_facts(
    service_id: str = "service-endpoint",
    asset_id: str | None = None,
    impact: Impact = Impact.ALTO,
    urgency: Urgency = Urgency.ALTA,
) -> TriageFacts:
    return TriageFacts(
        service_id=service_id,
        asset_id=asset_id,
        impact=impact,
        urgency=urgency,
    )


def _stored_classification(
    owner_connection: str,
    ticket_id: UUID,
) -> tuple[object, ...]:
    with psycopg.connect(owner_connection) as connection:
        row = connection.execute(
            """
            SELECT status, service_id, asset_id, impact, urgency, priority,
                   target_team, catalog_version, facts_revision
            FROM tickets
            WHERE id = %s
            """,
            (ticket_id,),
        ).fetchone()
    if row is None:
        raise LookupError(f"Ticket not found: {ticket_id}")
    return row


def test_complete_evaluation_persists_snapshot_and_em_triagem(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Endpoint failure")
    facts = _complete_facts(asset_id="asset-laptop-001")

    result = evaluate_ticket(runtime_connection, ticket.id, facts, 0)

    assert result.status is TicketStatus.EM_TRIAGEM
    assert result.facts == facts
    assert result.priority is Priority.P1
    assert result.target_team == "team-workplace"
    assert result.catalog_version == "catalog-v1"
    assert result.facts_revision == 1
    assert _stored_classification(owner_connection, ticket.id) == (
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
    with psycopg.connect(owner_connection) as connection:
        event = connection.execute(
            """
            SELECT event_type, details
            FROM audit_events
            WHERE ticket_id = %s AND event_type = 'TICKET_TRIAGE_EVALUATED'
            """,
            (ticket.id,),
        ).fetchone()
    assert event == (
        "TICKET_TRIAGE_EVALUATED",
        {
            "previous_status": "NOVO",
            "status": "EM_TRIAGEM",
            "service_id": "service-endpoint",
            "asset_id": "asset-laptop-001",
            "impact": "ALTO",
            "urgency": "ALTA",
            "priority": "P1",
            "target_team": "team-workplace",
            "catalog_version": "catalog-v1",
        },
    )


def test_missing_facts_or_team_mapping_leave_ticket_pending(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    missing_facts_ticket = create_ticket(runtime_connection, "Missing urgency")
    missing_facts = TriageFacts(service_id="service-endpoint", impact=Impact.ALTO)

    missing_result = evaluate_ticket(
        runtime_connection,
        missing_facts_ticket.id,
        missing_facts,
        0,
    )

    assert missing_result.status is TicketStatus.PENDENTE_INFORMACAO
    assert missing_result.facts == missing_facts
    assert missing_result.priority is None
    assert missing_result.target_team is None
    assert _stored_classification(owner_connection, missing_facts_ticket.id) == (
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

    catalog_version = _activate_catalog_version(
        owner_connection,
        include_unmapped_service=True,
    )
    unmapped_ticket = create_ticket(runtime_connection, "Unmapped service")
    unmapped_facts = _complete_facts(service_id="service-unmapped")

    unmapped_result = evaluate_ticket(
        runtime_connection,
        unmapped_ticket.id,
        unmapped_facts,
        0,
    )

    assert unmapped_result.status is TicketStatus.PENDENTE_INFORMACAO
    assert unmapped_result.catalog_version == catalog_version
    assert unmapped_result.priority is None
    assert unmapped_result.target_team is None
    assert _stored_classification(owner_connection, unmapped_ticket.id)[0:7] == (
        "PENDENTE_INFORMACAO",
        "service-unmapped",
        None,
        "ALTO",
        "ALTA",
        None,
        None,
    )


def test_asset_service_conflict_leaves_ticket_pending(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Asset mapped to another service")
    facts = _complete_facts(asset_id="asset-router-001")

    result = evaluate_ticket(runtime_connection, ticket.id, facts, 0)

    assert result.status is TicketStatus.PENDENTE_INFORMACAO
    assert result.facts == facts
    assert result.priority is None
    assert result.target_team is None
    assert _stored_classification(owner_connection, ticket.id) == (
        "PENDENTE_INFORMACAO",
        "service-endpoint",
        "asset-router-001",
        "ALTO",
        "ALTA",
        None,
        None,
        "catalog-v1",
        1,
    )


def test_pending_reevaluation_replaces_full_snapshot(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Follow-up facts")
    initial_facts = TriageFacts(
        service_id="service-endpoint",
        asset_id="asset-laptop-001",
        impact=Impact.ALTO,
    )

    pending = evaluate_ticket(runtime_connection, ticket.id, initial_facts, 0)
    catalog_version = _activate_catalog_version(
        owner_connection,
        remap_endpoint=True,
    )
    updated_facts = _complete_facts()
    result = evaluate_ticket(
        runtime_connection,
        ticket.id,
        updated_facts,
        pending.facts_revision,
    )

    assert pending.status is TicketStatus.PENDENTE_INFORMACAO
    assert result.status is TicketStatus.EM_TRIAGEM
    assert result.facts == updated_facts
    assert result.facts.asset_id is None
    assert result.priority is Priority.P1
    assert result.target_team == "team-network"
    assert result.catalog_version == catalog_version
    assert result.facts_revision == pending.facts_revision + 1
    assert _stored_classification(owner_connection, ticket.id) == (
        "EM_TRIAGEM",
        "service-endpoint",
        None,
        "ALTO",
        "ALTA",
        "P1",
        "team-network",
        catalog_version,
        2,
    )


def test_pending_identical_retry_is_idempotent(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Retry pending evaluation")
    facts = TriageFacts(service_id="service-endpoint", impact=Impact.ALTO)

    first_result = evaluate_ticket(runtime_connection, ticket.id, facts, 0)
    with psycopg.connect(owner_connection) as connection:
        event_count_before = connection.execute(
            """
            SELECT count(*)
            FROM audit_events
            WHERE ticket_id = %s AND event_type = 'TICKET_TRIAGE_EVALUATED'
            """,
            (ticket.id,),
        ).fetchone()[0]

    retried_result = evaluate_ticket(runtime_connection, ticket.id, facts, 0)

    with psycopg.connect(owner_connection) as connection:
        event_count_after = connection.execute(
            """
            SELECT count(*)
            FROM audit_events
            WHERE ticket_id = %s AND event_type = 'TICKET_TRIAGE_EVALUATED'
            """,
            (ticket.id,),
        ).fetchone()[0]

    assert first_result.status is TicketStatus.PENDENTE_INFORMACAO
    assert retried_result == first_result
    assert event_count_before == 1
    assert event_count_after == event_count_before
    assert _stored_classification(owner_connection, ticket.id)[-1] == 1


def test_different_facts_after_em_triagem_are_rejected(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Do not overwrite classification")
    original_facts = _complete_facts()
    result = evaluate_ticket(runtime_connection, ticket.id, original_facts, 0)
    before = _stored_classification(owner_connection, ticket.id)

    with pytest.raises(TriageStateError):
        evaluate_ticket(
            runtime_connection,
            ticket.id,
            _complete_facts(service_id="service-connectivity"),
            result.facts_revision,
        )

    assert _stored_classification(owner_connection, ticket.id) == before

    for terminal_status in (
        TicketStatus.CLASSIFICADO,
        TicketStatus.ERRO_INTEGRACAO,
    ):
        with psycopg.connect(owner_connection) as connection:
            connection.execute(
                "UPDATE tickets SET status = %s WHERE id = %s",
                (terminal_status.value, ticket.id),
            )
        before = _stored_classification(owner_connection, ticket.id)

        with pytest.raises(TriageStateError):
            evaluate_ticket(
                runtime_connection,
                ticket.id,
                original_facts,
                result.facts_revision,
            )

        assert _stored_classification(owner_connection, ticket.id) == before


def test_invalid_facts_leave_ticket_unchanged(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Reject unknown catalog facts")
    before = _stored_classification(owner_connection, ticket.id)

    for invalid_values in (
        {"impact": "CRITICO"},
        {"urgency": "URGENTE"},
    ):
        with pytest.raises(ValidationError):
            TriageFacts.model_validate(invalid_values)

    invalid_snapshots = (
        _complete_facts(service_id="service-unknown"),
        _complete_facts(asset_id="asset-unknown"),
    )
    for facts in invalid_snapshots:
        with pytest.raises(InvalidTriageFacts):
            evaluate_ticket(runtime_connection, ticket.id, facts, 0)

    assert _stored_classification(owner_connection, ticket.id) == before


def test_ticket_and_audit_write_failures_roll_back_evaluation(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Rollback failed evaluation")
    facts = _complete_facts()
    before = _stored_classification(owner_connection, ticket.id)
    trigger_cases = (
        (
            """
            CREATE FUNCTION reject_triage_ticket_update() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                IF NEW.facts_revision > OLD.facts_revision THEN
                    RAISE EXCEPTION 'forced triage ticket failure';
                END IF;
                RETURN NEW;
            END;
            $$;
            CREATE TRIGGER reject_triage_ticket_update
            BEFORE UPDATE ON tickets
            FOR EACH ROW EXECUTE FUNCTION reject_triage_ticket_update();
            """,
            """
            DROP TRIGGER IF EXISTS reject_triage_ticket_update ON tickets;
            DROP FUNCTION IF EXISTS reject_triage_ticket_update();
            """,
        ),
        (
            """
            CREATE FUNCTION reject_triage_audit_insert() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                IF NEW.event_type = 'TICKET_TRIAGE_EVALUATED' THEN
                    RAISE EXCEPTION 'forced triage audit failure';
                END IF;
                RETURN NEW;
            END;
            $$;
            CREATE TRIGGER reject_triage_audit_insert
            BEFORE INSERT ON audit_events
            FOR EACH ROW EXECUTE FUNCTION reject_triage_audit_insert();
            """,
            """
            DROP TRIGGER IF EXISTS reject_triage_audit_insert ON audit_events;
            DROP FUNCTION IF EXISTS reject_triage_audit_insert();
            """,
        ),
    )

    for create_trigger, drop_trigger in trigger_cases:
        with psycopg.connect(owner_connection) as connection:
            connection.execute(create_trigger)
        try:
            with pytest.raises(psycopg.errors.RaiseException):
                evaluate_ticket(runtime_connection, ticket.id, facts, 0)
        finally:
            with psycopg.connect(owner_connection) as connection:
                connection.execute(drop_trigger)

        assert _stored_classification(owner_connection, ticket.id) == before
        with psycopg.connect(owner_connection) as connection:
            event_count = connection.execute(
                """
                SELECT count(*)
                FROM audit_events
                WHERE ticket_id = %s
                  AND event_type = 'TICKET_TRIAGE_EVALUATED'
                """,
                (ticket.id,),
            ).fetchone()[0]
        assert event_count == 0


def test_concurrent_snapshots_reject_stale_revision(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Concurrent facts")
    snapshots = (
        _complete_facts(service_id="service-endpoint"),
        _complete_facts(
            service_id="service-connectivity",
            impact=Impact.BAIXO,
            urgency=Urgency.BAIXA,
        ),
    )
    barrier = Barrier(2)

    def evaluate_snapshot(facts: TriageFacts) -> tuple[str, TriageFacts | None]:
        barrier.wait(timeout=10)
        try:
            result = evaluate_ticket(runtime_connection, ticket.id, facts, 0)
        except TriageConflict:
            return "conflict", None
        return "accepted", result.facts

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(evaluate_snapshot, snapshots))

    assert sorted(outcome for outcome, _ in outcomes) == ["accepted", "conflict"]
    accepted_facts = next(facts for outcome, facts in outcomes if outcome == "accepted")
    assert accepted_facts in snapshots
    stored = _stored_classification(owner_connection, ticket.id)
    assert stored[0] == "EM_TRIAGEM"
    assert stored[1] == accepted_facts.service_id
    assert stored[3] == accepted_facts.impact.value
    assert stored[4] == accepted_facts.urgency.value
    assert stored[8] == 1


def test_em_triagem_retry_returns_stored_catalog_version(
    migrated_database_roles: tuple[str, str],
) -> None:
    owner_connection, runtime_connection = migrated_database_roles
    ticket = create_ticket(runtime_connection, "Retry after catalog update")
    facts = _complete_facts()
    first_result = evaluate_ticket(runtime_connection, ticket.id, facts, 0)
    catalog_version = _activate_catalog_version(
        owner_connection,
        remap_endpoint=True,
    )

    retried_result = evaluate_ticket(runtime_connection, ticket.id, facts, 0)

    with psycopg.connect(owner_connection) as connection:
        event_count = connection.execute(
            """
            SELECT count(*)
            FROM audit_events
            WHERE ticket_id = %s AND event_type = 'TICKET_TRIAGE_EVALUATED'
            """,
            (ticket.id,),
        ).fetchone()[0]

    assert catalog_version != first_result.catalog_version
    assert first_result.catalog_version == "catalog-v1"
    assert first_result.target_team == "team-workplace"
    assert retried_result == first_result
    assert event_count == 1
