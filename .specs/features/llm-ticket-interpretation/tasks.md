# LLM Ticket Interpretation Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/llm-ticket-interpretation/design.md`
**Status**: In progress
**Approved**: 2026-11-06 - user: "approve"
**Build**: none - no separate build, type-check, or lint command is configured; `pytest -v` is the project validation command.
**Run tests**: `pytest -v`

---

## Test Coverage Matrix

> Generated from `README.md`, `PROJECT.md`, `ARCHITECTURE.md`, `pyproject.toml`, current pytest tests, and the feature Spec. No `AGENTS.md`, `CONTRIBUTING.md`, CI workflow, linter/type-checker configuration, or coverage threshold was found. Existing integration tests use FastAPI TestClient with PostgreSQL fixtures; unit tests use pytest and Pydantic. Strong defaults apply to each acceptance criterion and edge case.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Interpretation response schemas | unit | Exact structured fields, nullability, allowed enums, extra-field rejection, partial outputs | `tests/unit/test_interpretation_schemas.py` | `pytest -v` |
| OpenRouter HTTP client | unit | Correct endpoint/auth/model/schema/timeout; only one request; missing config, timeout, HTTP errors, malformed envelope | `tests/unit/test_openrouter_client.py` | `pytest -v` |
| Interpretation service | unit | Prompt treats the description as untrusted text with no ticket identifiers or catalog data; complete, partial, and invalid model output behavior | `tests/unit/test_interpretation_service.py` | `pytest -v` |
| Ticket interpretation endpoint | integration | Existing/missing ticket, response contract, provider failures, no ticket/audit writes, loopback-only exposure | `tests/integration/test_ticket_interpretation_api.py`, `tests/integration/test_app_runtime.py` | `pytest -v` |
| Documentation and progress tracker | unit | Required route, provider configuration, data boundary, non-mutation behavior, and in-progress delivery entry are recorded | `tests/unit/test_interpretation_docs.py`, `tests/unit/test_project_progress.py` | `pytest -v` |

## Gate Check Commands

| Gate Level | When to Use | Command |
| ---------- | ---------- | ------- |
| Quick | After unit-only tasks | `pytest -v tests/unit` |
| Full | After integration tasks and final verification | `pytest -v` |
| Build | Documentation-only tasks; no separate build, type-check, or lint command exists | `pytest -v` |

**Co-located tests:** Every task that changes a tested layer includes its tests. The external provider is always mocked in automated tests; no API credential or live network request is required by the test suite.

---

## Execution Plan

Phases run sequentially; tasks within each phase execute in order.

### Phase 1: Extraction contract and provider

```text
T1 → T2
T1 → T3
T2 → T3
```

### Phase 2: Local API integration

```text
T3 → T4
```

### Phase 3: Documentation and progress

```text
T4 → T5
T4 → T6
T4 → T7
```

## Task Breakdown

### T1: Defining the interpretation response schema

**What**: Add strict Pydantic models for provider-only extracted candidates and the API response that adds `ticket_id` after extraction.
**Where**: `app/triage/interpretation_schemas.py`
**Depends on**: None
**Reuses**: `Impact` and `Urgency` enums from `app/triage/schemas.py`.
**Requirement**: LLM-03, LLM-04, LLM-05, LLM-09

**Done when**:

- [x] Complete and partial proposals validate with explicit null values and empty lists.
- [x] Impact and urgency accept only existing domain enum values.
- [x] Extra fields, numeric confidence, priority, and target-team fields are rejected.
- [x] Unit tests cover the valid, partial, enum, and extra-field cases.
- [x] Gate check passes: `pytest -v tests/unit`.
- [x] Test count: 21 unit tests pass (18 existing plus 3 schema tests).

**Tests**: unit
**Gate**: quick
**Commit**: `feat(triage): define interpretation response schema`
**Status**: Complete
**Gate result**: `pytest -v tests/unit` - 21 passed.

---

### T2: Implementing the OpenRouter HTTP client

**What**: Add one bounded, non-retrying standard-library HTTP call to OpenRouter Chat Completions using required environment configuration and strict JSON Schema output.
**Where**: `app/triage/openrouter_client.py`
**Depends on**: T1
**Reuses**: The output schema from T1 and Python `urllib.request`.
**Requirement**: LLM-01, LLM-07, LLM-08, LLM-09, LLM-11

**Done when**:

- [x] Requests use `OPENROUTER_API_KEY`, required `OPENROUTER_MODEL`, bearer authentication, non-streaming JSON Schema output, `require_parameters: true`, and a 30-second timeout.
- [x] The provider request contains the description as its only ticket data; it contains no ticket ID, other ticket fields, or catalog values.
- [x] Missing configuration, timeout, rate limit, and provider errors produce typed failures without retrying or logging secrets/content.
- [x] Unit tests mock the HTTP boundary and assert request details, timeout, single-attempt behavior, and mapped failures.
- [x] Gate check passes: `pytest -v tests/unit`.
- [x] Test count: 24 unit tests pass (21 before this task plus 3 provider-client tests).

**Tests**: unit
**Gate**: quick
**Commit**: `feat(triage): add OpenRouter extraction client`
**Status**: Complete
**Gate result**: `pytest -v tests/unit` - 24 passed.

---

### T3: Coordinating prompt construction and extraction validation

**What**: Add the interpretation service that instructs the model to extract only reviewable facts from untrusted ticket text and validates the returned proposal.
**Where**: `app/triage/interpretation.py`
**Depends on**: T1, T2
**Reuses**: The interpretation schema and OpenRouter client.
**Requirement**: LLM-03, LLM-04, LLM-05, LLM-09, LLM-11

**Done when**:

- [x] The service returns complete or partial validated proposals and never calculates priority/team or maps free-text candidates to catalog IDs.
- [x] Prompt construction treats the ticket description as untrusted text and includes no ticket identifiers or catalog data.
- [x] Invalid or malformed model output is surfaced as an explicit upstream-response error.
- [x] Unit tests cover full and partial extraction, prompt data boundaries, and invalid responses.
- [x] Gate check passes: `pytest -v tests/unit`.

**Tests**: unit
**Gate**: quick
**Commit**: `feat(triage): implement ticket interpretation service`
**Status**: Complete
**Gate result**: `pytest -v tests/unit` - 26 passed (24 before this task plus 2 service tests).

---

### T4: Exposing interpretation through the local ticket API

**What**: Add `POST /tickets/{ticket_id}/interpretation`, load the persisted description, return the validated proposal, and map lookup/provider errors without changing ticket state.
**Where**: `app/tickets/routes.py`
**Depends on**: T3
**Reuses**: `get_ticket`, the local router, and the interpretation service.
**Requirement**: LLM-01, LLM-02, LLM-03, LLM-05, LLM-06, LLM-07, LLM-08, LLM-09, LLM-10

**Done when**:

- [x] The endpoint returns the specified proposal for an existing ticket and returns `404` before contacting the provider for a missing ticket.
- [x] Missing config/provider availability/timeout/rate limit map to `503`; invalid provider output maps to `502`.
- [x] Integration tests assert ticket fields, revision, classification, and audit events remain unchanged on both valid proposals and failures.
- [x] The loopback-only runtime test remains green; no public-interface binding is introduced.
- [x] Gate check passes: `pytest -v`.

**Tests**: integration
**Gate**: full
**Commit**: `feat(api): expose local ticket interpretation`
**Status**: Complete
**Gate result**: `pytest -v` - 76 passed, 1 pre-existing Starlette deprecation warning.

---

### T5: Documenting interpretation in the README

**What**: Document the local endpoint, OpenRouter environment variables, description-only data sharing, review-before-triage flow, and failure responses.
**Where**: `README.md`
**Depends on**: T4
**Reuses**: Existing API setup and local triage sections.
**Requirement**: LLM-01, LLM-03, LLM-06, LLM-07, LLM-08, LLM-10

**Done when**:

- [x] The example shows how to request a proposal without sending a description or secret in the request.
- [x] Documentation states that proposals are not persisted and the existing deterministic triage call remains separate.
- [x] Provider configuration and errors match the Spec.
- [x] A documentation contract test verifies these statements.
- [x] Gate check passes: `pytest -v`.

**Tests**: unit
**Gate**: build
**Commit**: `docs(readme): describe local LLM interpretation`
**Status**: Complete
**Gate result**: `pytest -v` - 77 passed, 1 pre-existing Starlette deprecation warning.

---

### T6: Updating the LLM architecture boundary

**What**: Document the synchronous OpenRouter extraction component and its strict separation from deterministic evaluation and persistence.
**Where**: `ARCHITECTURE.md`
**Depends on**: T4
**Reuses**: Existing API, orchestrator, LLM, and deterministic triage sections.
**Requirement**: LLM-01, LLM-04, LLM-06, LLM-08, LLM-11

**Done when**:

- [x] The architecture distinguishes the proposal endpoint, provider client, deterministic triage endpoint, and their data boundaries.
- [x] It records no automatic retries, the timeout, output validation, and no ticket mutation by interpretation.
- [x] A documentation contract test verifies these boundaries.
- [x] Gate check passes: `pytest -v`.

**Tests**: unit
**Gate**: build
**Commit**: `docs(architecture): record LLM interpretation boundary`
**Status**: Complete
**Gate result**: `pytest -v` - 78 passed, 1 pre-existing Starlette deprecation warning.

---

### T7: Updating the project progress tracker

**What**: Add the LLM interpretation delivery to the centralized `PROJECT.md` progress table and mark it as in progress pending independent verification.
**Where**: `PROJECT.md`
**Depends on**: T4
**Reuses**: The progress dashboard and maintenance rule established by the project progress tracker.
**Requirement**: LLM-01, LLM-06

**Done when**:

- [x] The progress table links this feature's Spec, task checklist, and verification report and marks it as in progress until the independent verifier passes.
- [x] The roadmap lists LLM interpretation as active, not as an unprioritized future item.
- [x] Tests verify the in-progress entry and linked evidence paths.
- [x] Gate check passes: `pytest -v`.

**Tests**: unit
**Gate**: build
**Commit**: `docs(progress): track LLM interpretation delivery`
**Status**: Complete
**Gate result**: `pytest -v` - 79 passed, 1 pre-existing Starlette deprecation warning.

## Checks

**Run tests**: `pytest -v`

**C1** - The response schema accepts complete and partial proposals with only the allowed fields and enum values (LLM-03, LLM-04, LLM-05)
Proof: run tests | `tests/unit/test_interpretation_schemas.py::test_interpretation_schema_accepts_complete_and_partial_proposals PASSED`

**C2** - The provider client sends only the ticket description as ticket data with required model, bearer auth, structured output, and 30-second timeout (LLM-01, LLM-07)
Proof: run tests | `tests/unit/test_openrouter_client.py::test_client_sends_schema_constrained_description_only_request PASSED`

**C3** - Missing configuration and upstream timeout/rate limit fail explicitly without retry (LLM-07, LLM-08)
Proof: run tests | `tests/unit/test_openrouter_client.py::test_client_maps_missing_config_and_provider_failures_without_retry PASSED`

**C4** - The service returns complete and partial proposals and surfaces malformed provider output (LLM-03, LLM-05, LLM-09)
Proof: run tests | `tests/unit/test_interpretation_service.py::test_service_returns_partial_proposal_and_propagates_invalid_output PASSED`

**C5** - The prompt treats descriptions as untrusted text and contains no ticket identifiers or catalog data (LLM-01, LLM-11)
Proof: run tests | `tests/unit/test_interpretation_service.py::test_service_treats_description_as_untrusted_without_other_ticket_data PASSED`

**C6** - The route returns a proposal from the persisted description without changing ticket or audit state (LLM-01, LLM-03, LLM-06)
Proof: run tests | `tests/integration/test_ticket_interpretation_api.py::test_interpretation_returns_proposal_for_existing_ticket PASSED`

**C7** - Missing tickets return `404` and database lookup failures return `503`, both before contacting the provider (LLM-02)
Proof: run tests | `tests/integration/test_ticket_interpretation_api.py::test_missing_and_unavailable_ticket_lookups_return_without_provider_call PASSED`

**C8** - Missing provider configuration maps to `503` without changing the ticket or audit state (LLM-06, LLM-07)
Proof: run tests | `tests/integration/test_ticket_interpretation_api.py::test_provider_failures_return_errors_without_ticket_or_audit_changes[OpenRouterConfigurationError-503-Ticket interpretation unavailable] PASSED`

**C9** - Provider availability failures map to `503` without changing the ticket or audit state (LLM-06, LLM-08)
Proof: run tests | `tests/integration/test_ticket_interpretation_api.py::test_provider_failures_return_errors_without_ticket_or_audit_changes[OpenRouterUnavailable-503-Ticket interpretation unavailable] PASSED`

**C10** - Invalid provider output maps to `502` without changing the ticket or audit state (LLM-06, LLM-09)
Proof: run tests | `tests/integration/test_ticket_interpretation_api.py::test_provider_failures_return_errors_without_ticket_or_audit_changes[OpenRouterInvalidResponse-502-Ticket interpretation returned an invalid provider response] PASSED`

**C11** - Interpretation does not log descriptions, prompts, provider responses, or keys (LLM-11)
Proof: run tests | `tests/integration/test_ticket_interpretation_api.py::test_interpretation_does_not_log_sensitive_content PASSED`

**C12** - Interpretation remains available only through the loopback-bound local server (LLM-10)
Proof: run tests | `tests/integration/test_app_runtime.py::test_server_binds_to_loopback_only PASSED`

**C13** - README documents the local proposal-first flow and required configuration (LLM-01, LLM-06, LLM-07, LLM-10)
Proof: run tests | `tests/unit/test_interpretation_docs.py::test_readme_documents_local_proposal_flow_and_configuration PASSED`

**C14** - Architecture docs preserve the separation between LLM proposals and deterministic decisions, including provider boundaries, timeout, validation, and no retry (LLM-04, LLM-06, LLM-08, LLM-11)
Proof: run tests | `tests/unit/test_interpretation_docs.py::test_architecture_documents_provider_and_deterministic_boundaries PASSED`

**C15** - The centralized project progress tracker links this feature's Spec, task checklist, and verification report (LLM-01)
Proof: run tests | `tests/unit/test_project_progress.py::test_dashboard_lists_verified_interpretation_delivery PASSED`

**C16** - After independent verification passes, the centralized project tracker marks the feature complete and links its passing verification report (LLM-01)
Proof: run tests | `tests/unit/test_project_progress.py::test_dashboard_lists_verified_interpretation_delivery PASSED`

---

## Handoff

**Settled during Specify**: User chose proposal-first workflow, OpenRouter, description-only provider data, `OPENROUTER_MODEL` configuration, partial proposals with explicit errors, stored ticket descriptions, no automatic retries, no catalog context, and no numeric confidence score.
**Settled during Design**: User selected a synchronous route, dedicated service, and standard-library HTTP client.
**Dispatched**: Verifier 1 returned PASS at HEAD `dd8e77e`; final-state Verifier 2 returned PASS at HEAD `8f1a6f9`; no screens review (no capture-bound criteria).
**Walked**: not applicable; this feature adds a local API without a user-facing screen.

## Phase Execution Map

```text
T1 → T2 → T3 → T4
T4 → T5
T4 → T6
T4 → T7
```
