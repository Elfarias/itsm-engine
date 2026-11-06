from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.tickets.schemas import TicketCreate, TicketResponse, TicketStatus


def test_ticket_create_schema_accepts_description_boundaries() -> None:
    assert TicketCreate(description="x").description == "x"
    assert TicketCreate(description="x" * 4000).description == "x" * 4000


def test_ticket_create_schema_rejects_missing_blank_and_oversized_descriptions() -> None:
    invalid_payloads = [
        {},
        {"description": ""},
        {"description": "   \t\n"},
        {"description": "x" * 4001},
    ]

    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            TicketCreate.model_validate(payload)


def test_ticket_create_schema_preserves_nonblank_description() -> None:
    description = "  Disk failure  "

    assert TicketCreate(description=description).description == description


def test_ticket_response_schema_exposes_specified_fields() -> None:
    created_at = datetime.now(timezone.utc)
    ticket_id = uuid4()
    response = TicketResponse(
        id=ticket_id,
        description="Disk failure",
        status=TicketStatus.NOVO,
        created_at=created_at,
    )

    assert response.id == ticket_id
    assert response.status is TicketStatus.NOVO
    assert response.created_at == created_at
    assert response.created_at.utcoffset().total_seconds() == 0
    assert response.description == "Disk failure"
