from enum import Enum
from pydantic import BaseModel, ConfigDict


class KedbLookupStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class KedbMatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    error_id: str
    title: str
    summary: str
    match_reasons: list[str]
    workaround: str


class KedbLookupResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: KedbLookupStatus
    matches: list[KedbMatch]
