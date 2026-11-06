from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, UUID4, field_validator


class TicketStatus(str, Enum):
    NOVO = "NOVO"
    EM_TRIAGEM = "EM_TRIAGEM"
    PENDENTE_INFORMACAO = "PENDENTE_INFORMACAO"
    CLASSIFICADO = "CLASSIFICADO"
    ERRO_INTEGRACAO = "ERRO_INTEGRACAO"


class TicketCreate(BaseModel):
    description: str = Field(min_length=1, max_length=4000)

    @field_validator("description")
    @classmethod
    def description_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description must not be blank")
        return value


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    description: str
    status: TicketStatus
    created_at: datetime
