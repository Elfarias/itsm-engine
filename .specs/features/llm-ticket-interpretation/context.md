# LLM Ticket Interpretation Context

**Gathered:** 2026-11-06
**Spec:** `.specs/features/llm-ticket-interpretation/spec.md`
**Status:** Design approved

---

## Feature Boundary

Interpret ticket descriptions into structured triage facts while leaving domain validation, priority calculation, routing, and ticket persistence to the existing deterministic application flow.

---

## Implementation Decisions

### Interpretation workflow

- Return an extracted proposal separately; a later call to the existing deterministic triage API performs evaluation and persistence. User selected `proposal_then_triage`.
- Read the description from the persisted ticket; do not accept a replacement description in the interpretation request. User selected `stored_ticket_description`.

### LLM provider

- Use OpenRouter. The user supplied `OPENROUTER_API_KEY` as the environment-variable name, not a credential value.
- Do not request or record secret values in chat or project files.
- Require `OPENROUTER_MODEL` configuration; do not silently select a model or fallback. User selected `env_model_required`.

### Data sent to the provider

- The user permits sending only the ticket description to the cloud provider. Do not send the ticket identifier or other ticket/database fields as prompt data.
- Do not send catalog records or identifiers. Service and asset candidates in the response remain free text and require explicit validation/mapping before deterministic triage.

### Uncertainty and provider failure

- Return partial extraction proposals with missing-information details for review; do not mutate the ticket.
- Report provider failures explicitly and leave the ticket unchanged. User selected `partial_proposal_no_mutation`.
- Do not retry automatically on transient provider failures; let the caller retry manually. User selected `no_auto_retry`.
- Represent uncertainty with extracted evidence, missing information, and textual uncertainty details. Do not return numeric confidence scores. User selected `evidence_missing_uncertainty`.

### Agent's Discretion

- Keep provider request logs free of ticket descriptions and credentials; only safe operational metadata may be logged.
- Do not persist the LLM prompt or proposal; return the proposal to the caller only.
- Use a synchronous FastAPI route and a dedicated interpretation service with the Python standard-library HTTP client. User selected `sync_stdlib`.

### Declined / Undiscussed Gray Areas → Assumptions

- No further product decisions remain unresolved.

---

## Specific References

- The user selected: `workflow=proposal_then_triage`, `provider=OPENROUTER_API_KEY`, `data_sharing=cloud_description_only`, `uncertainty_failure=partial_proposal_no_mutation`, `description_source=stored_ticket_description`, `model_selection=env_model_required`, `retry_policy=no_auto_retry`, `catalog_context=description_only_free_candidate`, and `confidence_output=evidence_missing_uncertainty`.
- The user approved the Spec with the response "approve".
- The user selected the synchronous route, dedicated service, and standard-library HTTP approach for Design.
- The user approved the Design with the response "approve".
- The user approved the task breakdown with the response "approve".
- `.specs/features/ticket-triage-api/spec.md` defines the current local deterministic evaluation endpoint and its structured request.
- `ARCHITECTURE.md` limits the future LLM to interpretation and extraction; the application validates facts and owns deterministic decisions.

## Deferred Ideas

None.
