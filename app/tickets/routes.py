import os
from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException, status

from app.tickets.repository import create_ticket, get_ticket
from app.tickets.schemas import TicketCreate, TicketResponse

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
