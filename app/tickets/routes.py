import os
from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException, status

from app.tickets.repository import create_ticket, get_ticket
from app.tickets.schemas import TicketCreate, TicketResponse
from app.triage.api_schemas import TicketTriageRequest
from app.triage.interpretation import interpret_description
from app.triage.interpretation_schemas import TicketInterpretationResponse
from app.triage.kedb_service import lookup_kedb
from app.triage.openrouter_client import (
    OpenRouterConfigurationError,
    OpenRouterInvalidResponse,
    OpenRouterUnavailable,
)
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


@router.post(
    "/tickets/{ticket_id}/interpretation",
    response_model=TicketInterpretationResponse,
)
def post_ticket_interpretation(ticket_id: UUID) -> TicketInterpretationResponse:
    try:
        ticket = get_ticket(os.environ["DATABASE_URL"], ticket_id)
    except psycopg.Error as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ticket interpretation unavailable",
        ) from error

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    try:
        proposal = interpret_description(ticket.description)
    except (OpenRouterConfigurationError, OpenRouterUnavailable) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ticket interpretation unavailable",
        ) from error
    except OpenRouterInvalidResponse as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ticket interpretation returned an invalid provider response",
        ) from error

    kedb_result = lookup_kedb(
        os.environ["DATABASE_URL"],
        proposal.service_candidate,
        proposal.symptoms,
    )

    return TicketInterpretationResponse(
        ticket_id=ticket.id,
        kedb=kedb_result,
        **proposal.model_dump(),
    )


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
