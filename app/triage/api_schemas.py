from pydantic import BaseModel, ConfigDict, Field

from app.triage.schemas import TriageFacts


class TicketTriageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(ge=0)
    facts: TriageFacts
