import pytest
from pydantic import ValidationError

from app.triage.api_schemas import TicketTriageRequest
from app.triage.schemas import Impact, Urgency


def test_triage_request_validates_revision_and_complete_partial_facts() -> None:
    complete = TicketTriageRequest.model_validate(
        {
            "expected_revision": 0,
            "facts": {
                "service_id": "service-endpoint",
                "asset_id": "asset-001",
                "impact": "ALTO",
                "urgency": "ALTA",
            },
        }
    )
    partial = TicketTriageRequest.model_validate(
        {"expected_revision": 2, "facts": {"impact": "MEDIO"}}
    )

    assert complete.expected_revision == 0
    assert complete.facts.service_id == "service-endpoint"
    assert complete.facts.asset_id == "asset-001"
    assert complete.facts.impact is Impact.ALTO
    assert complete.facts.urgency is Urgency.ALTA
    assert partial.expected_revision == 2
    assert partial.facts.service_id is None
    assert partial.facts.asset_id is None
    assert partial.facts.impact is Impact.MEDIO
    assert partial.facts.urgency is None
    for invalid_revision in (True, False, 1.0, "1"):
        with pytest.raises(ValidationError):
            TicketTriageRequest.model_validate(
                {"expected_revision": invalid_revision, "facts": {}}
            )


def test_triage_request_requires_facts_and_nonnegative_revision() -> None:
    invalid_requests = (
        {"facts": {}},
        {"expected_revision": -1, "facts": {}},
        {"expected_revision": 0},
        {"expected_revision": True, "facts": {}},
        {"expected_revision": False, "facts": {}},
        {"expected_revision": 1.0, "facts": {}},
        {"expected_revision": "1", "facts": {}},
    )

    for payload in invalid_requests:
        with pytest.raises(ValidationError):
            TicketTriageRequest.model_validate(payload)


def test_triage_request_rejects_extra_fields() -> None:
    invalid_requests = (
        {"expected_revision": 0, "facts": {}, "status": "EM_TRIAGEM"},
        {"expected_revision": 0, "facts": {"priority": "P1"}},
    )

    for payload in invalid_requests:
        with pytest.raises(ValidationError):
            TicketTriageRequest.model_validate(payload)
