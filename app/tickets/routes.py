import os

import psycopg
from fastapi import APIRouter, HTTPException, status

from app.tickets.repository import create_ticket
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
