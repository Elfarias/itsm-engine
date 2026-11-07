from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.triage.kedb_schemas import KedbLookupResult
from app.triage.schemas import Impact, Urgency


class InterpretationProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service_candidate: str | None
    asset_candidate: str | None
    impact: Impact | None
    urgency: Urgency | None
    symptoms: list[str]
    impact_evidence: list[str]
    urgency_evidence: list[str]
    missing_information: list[str]
    uncertainties: list[str]
    technical_summary: str | None


class TicketInterpretationResponse(InterpretationProposal):
    ticket_id: UUID
    kedb: KedbLookupResult | None = None
