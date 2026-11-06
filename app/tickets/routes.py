import os
from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException, status

from app.tickets.repository import create_ticket, get_ticket
from app.tickets.schemas import TicketCreate, TicketResponse
from app.triage.api_schemas import TicketTriageRequest
from app.triage.schemas import (
    CatalogConfigurationError,
    InvalidTriageFacts,
    TriageConflict,
    TriageResult,
    TriageStateError,
)
from app.triage.service import evaluate_ticket

router = APIRouter()


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_ticket(request: TicketCreate) -> TicketResponse:
    try:
        return create_ticket(os.environ["DATABASE_URL"], request.description)
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ticket persistence failed",
        ) from error


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def read_ticket(ticket_id: UUID) -> TicketResponse:
    ticket = get_ticket(os.environ["DATABASE_URL"], ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket


@router.post("/tickets/{ticket_id}/triage")
def post_ticket_triage(
    ticket_id: UUID,
    request: TicketTriageRequest,
) -> TriageResult:
    connection_string = os.environ["DATABASE_URL"]
    try:
        return evaluate_ticket(
            connection_string,
            ticket_id,
            request.facts,
            request.expected_revision,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from error
    except InvalidTriageFacts as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid triage facts",
        ) from error
    except (TriageConflict, TriageStateError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ticket cannot be evaluated with the supplied revision or state",
        ) from error
    except (CatalogConfigurationError, psycopg.Error) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ticket triage unavailable",
        ) from error
