# LLM Ticket Interpretation Specification

**Approved**: 2026-11-06 - user: "approve"

## Problem Statement

The current triage API requires callers to provide structured facts, so it cannot interpret the free-text description already stored with a ticket. This feature asks an LLM to extract a reviewable proposal while keeping catalog validation, deterministic classification, and ticket updates under application control.

## Goals

- Interpret the persisted description of an existing ticket through OpenRouter.
- Return structured proposed facts, evidence, missing information, and textual uncertainty without modifying the ticket.
- Keep deterministic evaluation as a separate, explicit call through the existing triage API.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Automatic deterministic evaluation or ticket mutation | The user chose a proposal-first workflow; a later explicit request uses the existing triage endpoint. |
| Sending ticket identifiers, other ticket fields, or catalog records to OpenRouter | The user authorized sending only the persisted description. |
| Automatic mapping of free-text service or asset candidates to catalog IDs | Catalog values are not sent to the model; callers must resolve and validate candidates before deterministic triage. |
| Numeric confidence scores | The user chose evidence, missing fields, and textual uncertainty instead. |
| LLM provider fallback or automatic retry | The user chose explicit provider errors and manual retry. |
| KEDB lookup, public-network access, remote authentication, or an operator UI | These are separate planned features. |

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Workflow | A new local operation returns a proposal; the existing triage route remains a separate explicit action. | Preserves deterministic evaluation and keeps model suggestions reviewable. | y |
| Text source | Read the description from the persisted ticket; the request does not accept replacement text. | Prevents a caller from interpreting text different from the ticket being reviewed. | y |
| Provider and model configuration | OpenRouter; require `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`, with no implicit model fallback. | The user chose OpenRouter and explicit model configuration. No secret value is needed in source or tests. | y |
| Provider input | Send only the ticket description as ticket data; do not send ticket ID, other ticket fields, or catalog records. | The user authorized cloud processing of the description only. | y |
| Candidate identifiers | Return service and asset candidates as free text, never as resolved catalog identifiers. | The catalog is not shared with the provider; callers must map candidates explicitly. | y |
| Partial extraction | Return valid partial proposals with evidence, missing information, and textual uncertainty; never mutate the ticket. | Supports human review without treating uncertain extraction as a decision. | y |
| Provider retry | Do not retry automatically; return an explicit error and let the caller retry manually. | Avoids hidden latency and provider charges. | y |
| Provider timeout | Use a finite 30-second request timeout; return `503` without mutation when it expires. | Bounds local request duration while allowing a hosted model response. | n |
| Invalid provider response | Return `502` if the response cannot be parsed or fails the extraction schema; do not persist it. | An invalid model response is an upstream failure, not a valid partial proposal. | n |

**Open questions:** none - product decisions were resolved during discussion; technical defaults are recorded above.

## User Stories

### P1: Request a reviewable interpretation ⭐ MVP

**User Story**: Como operador local, quero obter uma proposta estruturada a partir da descrição salva de um chamado para revisar os fatos antes de solicitar a triagem determinística.

**Why P1**: A extração do texto é a evolução escolhida e prepara a entrada para as regras já implementadas sem delegar decisões de negócio ao modelo.

**Acceptance Criteria**:

1. **LLM-01** WHEN a local client requests `POST /tickets/{ticket_id}/interpretation` for an existing ticket THEN the system SHALL read the persisted description and SHALL send no ticket ID, other ticket fields, or catalog records as ticket data to OpenRouter.
2. **LLM-02** IF the requested ticket does not exist THEN the system SHALL return `404` and SHALL NOT call OpenRouter.
3. **LLM-03** WHEN OpenRouter returns a valid extraction THEN the system SHALL return `200` with `ticket_id`, nullable free-text `service_candidate` and `asset_candidate`, nullable allowed `impact` and `urgency`, `symptoms`, `impact_evidence`, `urgency_evidence`, `missing_information`, `uncertainties`, and a nullable `technical_summary`.
4. **LLM-04** The system SHALL NOT return a model-selected priority or target team; deterministic rules and catalog mappings remain authoritative.
5. **LLM-05** WHEN the model cannot determine every fact THEN the system SHALL return a valid partial proposal with unresolved fields null and the relevant information in `missing_information` or `uncertainties`.
6. **LLM-06** WHEN a proposal is returned, whether complete or partial, THEN the system SHALL leave the persisted ticket, triage result, revision, and audit events unchanged.
7. **LLM-07** IF `OPENROUTER_API_KEY` or `OPENROUTER_MODEL` is missing THEN the system SHALL return `503` without sending a provider request or changing the ticket.
8. **LLM-08** IF OpenRouter times out, is unavailable, or rejects the request, including a rate limit, THEN the system SHALL return `503`, SHALL NOT retry automatically, and SHALL leave the ticket unchanged.
9. **LLM-09** IF the provider response is malformed or fails the extraction schema THEN the system SHALL return `502` and SHALL leave the ticket unchanged.
10. **LLM-10** The system SHALL accept unauthenticated interpretation requests only through the local development server bound to `127.0.0.1`.
11. **LLM-11** The system SHALL NOT persist or log the ticket description, provider prompt, provider response, or API key.

**Independent Test**: Create a ticket through the existing API, request an interpretation using a mocked OpenRouter response, verify the structured proposal and unchanged persisted ticket/audit state, then use an explicitly resolved valid fact snapshot with the existing triage endpoint.

## Edge Cases

- Missing ticket returns `404` without a provider request.
- Missing provider key or model returns `503` without exposing secret values.
- A partial extraction returns `200`, null unresolved facts, and review details.
- Invalid enum values or malformed provider JSON returns `502` without persistence.
- Provider timeout, unavailability, or rate limiting returns `503`; no automatic retry occurs.
- Repeated interpretation requests do not create ticket changes or audit events.
- Service and asset candidates remain text; the system does not invent catalog IDs, priority, or target team.
- Requests remain local to the loopback-bound development server.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| LLM-01 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-02 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-03 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-04 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-05 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-06 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-07 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-08 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-09 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-10 | P1: Request a reviewable interpretation | Tasks | Pending |
| LLM-11 | P1: Request a reviewable interpretation | Tasks | Pending |

**Coverage:** 11 total, 11 mapped to the story, 0 unmapped.

## Differences from the source

None. No binding screen or design reference was provided.

## Sources

- `PROJECT.md` - implemented local scope and planned LLM interpretation.
- `ARCHITECTURE.md` - LLM is limited to extraction; deterministic application logic validates facts and owns decisions.
- `.specs/features/ticket-triage-api/spec.md` - existing local deterministic evaluation contract.
- `app/tickets/routes.py` and `app/tickets/schemas.py` - current ticket API and description validation.
- User discussion in `.specs/features/llm-ticket-interpretation/context.md` - OpenRouter, privacy boundary, workflow, and retry decisions.

## Success Criteria

- The local API returns structured, reviewable extraction results from a persisted ticket description.
- No proposal changes ticket state or bypasses deterministic evaluation.
- Provider errors, malformed output, or incomplete configuration fail explicitly without partial writes or automatic retries.
- The project remains functional without a real provider credential in automated tests.
