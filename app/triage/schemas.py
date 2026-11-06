from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.tickets.schemas import TicketStatus


class Impact(str, Enum):
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAIXO = "BAIXO"


class Urgency(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"


class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class TriageFacts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service_id: str | None = None
    asset_id: str | None = None
    impact: Impact | None = None
    urgency: Urgency | None = None


class CatalogSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version_id: str
    services: frozenset[str]
    asset_services: dict[str, str]
    service_teams: dict[str, str]


class EvaluationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: TicketStatus
    facts: TriageFacts
    priority: Priority | None = None
    target_team: str | None = None
    catalog_version: str


class TriageResult(EvaluationDecision):
    ticket_id: UUID
    facts_revision: int = Field(ge=0)


class TriageError(Exception):
    pass


class InvalidTriageFacts(TriageError):
    pass


class TriageConflict(TriageError):
    pass


class TriageStateError(TriageError):
    pass


class CatalogConfigurationError(TriageError):
    pass
