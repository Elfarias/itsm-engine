# API Local de Triagem Determinística Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: skipped - this is a route adapter using the existing ticket router, triage service and loopback server configuration; no architectural decision or new pattern is needed.
**Status**: In progress
**Approved**: 2026-11-06 - user: "Aprovar as tarefas"
**Build**: none - no separate build, type-check or lint command is configured; `pytest -v` is the project validation command.
**Run tests**: `pytest -v`

---

## Test Coverage Matrix

> Generated from project guidelines, test configuration and representative tests. Guidelines found: `README.md`, `PROJECT.md`, and `pyproject.toml`; no `AGENTS.md`, `CONTRIBUTING.md`, CI workflow, linter/type-checker configuration or coverage threshold was found. Existing integration tests use FastAPI `TestClient` with a migrated PostgreSQL fixture; unit tests use pytest and Pydantic schemas. Strong defaults applied to every spec criterion and listed edge case.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| HTTP request schema | unit | Required nonnegative revision, optional full-snapshot facts, enum validation, rejection of extra fields | `tests/unit/test_triage_api_schemas.py` | `pytest -v` |
| Ticket triage route | integration | Every response and failure in TRIAPI-02 through TRIAPI-13; persisted state and audit effects; retry and catalog-version transitions | `tests/integration/test_triage_api.py`, `tests/integration/test_app_runtime.py` | `pytest -v` |
| Project documentation | none | Verify endpoint scope, request/response behavior and local-only boundary match the approved spec and implementation | `README.md`, `ARCHITECTURE.md`, `PROJECT.md` | Build gate only |

## Gate Check Commands

> Generated from `pyproject.toml`, current tests, and project documentation.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | After unit-test tasks | `pytest -v tests/unit` |
| Full | After integration-test tasks | `pytest -v` |
| Build | After documentation-only tasks; no separate build, type-check or lint command exists | `pytest -v` |

**Co-located tests:** Schema unit tests are included in T1. The endpoint integration tests are included in T2 and use the existing PostgreSQL migration and API-client fixtures. Documentation-only tasks use the build gate.

---

## Execution Plan

Phases run sequentially. Tasks within each phase execute in the listed order.

### Phase 1: Request contract

```text
T1
```

### Phase 2: HTTP integration

```text
T2
```

### Phase 3: Documentation

```text
T3, T4, T5
```

---

## Task Breakdown

### T1: Defining the triage API request schema

**What**: Add the typed HTTP request model for a complete triage-facts snapshot and a required nonnegative `expected_revision`.
**Where**: `app/triage/api_schemas.py`
**Depends on**: None
**Reuses**: `TriageFacts` from `app/triage/schemas.py` and the Pydantic patterns in `app/tickets/schemas.py`.
**Requirement**: TRIAPI-01, TRIAPI-06

**Done when**:

- [x] The request model requires an integer `expected_revision` greater than or equal to zero and a `facts` object.
- [x] The facts object accepts the optional fields defined by the spec as a complete snapshot and rejects extra fields.
- [x] Unit tests cover valid complete and partial requests, missing/negative revision, and extra fields.
- [x] Gate check passes: `pytest -v tests/unit`.
- [x] Test count: 14 unit tests pass (11 existing plus 3 new schema tests).

**Tests**: unit
**Gate**: quick
**Commit**: `feat(triage): define local API request schema`

---

### T2: Exposing deterministic triage through the ticket API

**What**: Add `POST /tickets/{ticket_id}/triage`, invoke `evaluate_ticket`, return its persisted result, and translate domain and persistence failures to the approved HTTP statuses.
**Where**: `app/tickets/routes.py`
**Depends on**: T1
**Reuses**: `evaluate_ticket` from `app/triage/service.py`, `TicketTriageRequest` from `app/triage/api_schemas.py`, and existing ticket route error handling.
**Requirement**: TRIAPI-02, TRIAPI-03, TRIAPI-04, TRIAPI-05, TRIAPI-06, TRIAPI-07, TRIAPI-08, TRIAPI-09, TRIAPI-10, TRIAPI-11, TRIAPI-12, TRIAPI-13

**Done when**:

- [ ] The endpoint returns the response fields and successful complete/pending outcomes specified in the Spec.
- [ ] It maps missing tickets to 404, malformed/invalid requests and facts to 422, state/revision conflicts to 409, and database/catalog failures to 503.
- [ ] Integration tests cover the complete, pending, missing-ticket, invalid-input, conflict, pending-retry, active-catalog-change, completed-retry, persistence-failure and missing-active-catalog cases.
- [ ] The existing loopback binding test remains green; no public-interface binding is introduced.
- [ ] Gate check passes: `pytest -v`.
- [ ] Integration gate: `pytest -v tests/integration` passes 44 tests (34 existing plus 10 new API tests).
- [ ] Full gate: `pytest -v` passes 58 tests.

**Tests**: integration
**Gate**: full
**Commit**: `feat(api): expose local ticket triage`

---

### T3: Documenting the local triage API in the README

**What**: Replace the claim that no classification route exists with the new local-only endpoint, payload shape, response outcomes and a runnable request example.
**Where**: `README.md`
**Depends on**: T2
**Reuses**: The existing triage-flow, local-configuration and API usage sections.
**Requirement**: TRIAPI-01, TRIAPI-02, TRIAPI-03, TRIAPI-13

**Done when**:

- [ ] The endpoint and request fields match the implementation.
- [ ] Documentation distinguishes a local HTTP endpoint from public-network exposure.
- [ ] The documented success and error outcomes match the Spec.
- [ ] Gate check passes: `pytest -v`.

**Tests**: none
**Gate**: build
**Commit**: `docs(readme): describe local triage API`

---

### T4: Updating the architecture description

**What**: Update the architecture's API boundary and flow to describe the local HTTP adapter over the existing triage service.
**Where**: `ARCHITECTURE.md`
**Depends on**: T2
**Reuses**: Existing sections describing the internal triage service, state flow and local server boundary.
**Requirement**: TRIAPI-01, TRIAPI-02, TRIAPI-07, TRIAPI-13

**Done when**:

- [ ] The API layer is described as local-only and separate from the deterministic domain service.
- [ ] Request revision, full-snapshot and retry behavior match the approved Spec.
- [ ] No public-network access, LLM extraction or external integration is described as part of this feature.
- [ ] Gate check passes: `pytest -v`.

**Tests**: none
**Gate**: build
**Commit**: `docs(architecture): document local triage API`

---

### T5: Updating the project scope baseline

**What**: Record the local triage API as part of the implemented slice and remove statements that the project has no classification API.
**Where**: `PROJECT.md`
**Depends on**: T2
**Reuses**: Existing implemented-slice, scope and future-evolution sections.
**Requirement**: TRIAPI-01, TRIAPI-13

**Done when**:

- [ ] The implemented scope identifies the local-only triage endpoint.
- [ ] Public-network access, authentication, LLM and external ITSM remain future scope.
- [ ] Gate check passes: `pytest -v`.

**Tests**: none
**Gate**: build
**Commit**: `docs(project): record local triage API`

---

## Checks

**Run tests**: `pytest -v`

**C1** - The request facts object accepts the optional fields as a complete snapshot (TRIAPI-01, AC 1)
Proof: run tests | `tests/unit/test_triage_api_schemas.py::test_triage_request_accepts_complete_and_partial_facts PASSED`

**C2** - A successful evaluation returns all specified response fields with HTTP 200 (TRIAPI-02, AC 2)
Proof: run tests | `tests/integration/test_triage_api.py::test_complete_triage_returns_persisted_result PASSED`

**C3** - Complete facts persist mapped priority and team and return `EM_TRIAGEM` (TRIAPI-03, AC 3)
Proof: run tests | `tests/integration/test_triage_api.py::test_complete_triage_returns_persisted_result PASSED`

**C4** - Partial or inconsistent facts persist as pending and return HTTP 200 with unset priority/team where applicable (TRIAPI-04, AC 4)
Proof: run tests | `tests/integration/test_triage_api.py::test_partial_and_conflicting_facts_return_pending PASSED`

**C5** - A valid UUID for a missing ticket returns 404 without creating or changing a ticket (TRIAPI-05, AC 5)
Proof: run tests | `tests/integration/test_triage_api.py::test_missing_ticket_returns_404 PASSED`

**C6** - Invalid request shape, path UUID, facts, enum or catalog reference returns 422 without changing the ticket (TRIAPI-06, AC 6)
Proof: run tests | `tests/integration/test_triage_api.py::test_invalid_request_and_catalog_facts_return_422_without_changes PASSED`

**C7** - A stale revision or incompatible state returns 409 and preserves persisted facts and result (TRIAPI-07, AC 7)
Proof: run tests | `tests/integration/test_triage_api.py::test_stale_revision_and_invalid_state_return_409 PASSED`

**C8** - An identical pending snapshot with the same active catalog version returns without a duplicate audit event (TRIAPI-08, AC 8)
Proof: run tests | `tests/integration/test_triage_api.py::test_pending_identical_retry_is_idempotent PASSED`

**C9** - An identical pending snapshot with the current revision is re-evaluated after catalog activation changes (TRIAPI-09, AC 9)
Proof: run tests | `tests/integration/test_triage_api.py::test_pending_retry_uses_new_active_catalog_version PASSED`

**C10** - An identical `EM_TRIAGEM` retry returns its persisted result and catalog version regardless of the active catalog (TRIAPI-10, AC 10)
Proof: run tests | `tests/integration/test_triage_api.py::test_em_triagem_retry_returns_stored_catalog_version PASSED`

**C11** - Evaluation or audit persistence failure returns 503 without partial ticket or audit writes (TRIAPI-11, AC 11)
Proof: run tests | `tests/integration/test_triage_api.py::test_evaluation_or_audit_failure_returns_503_without_partial_changes PASSED`

**C12** - Missing active catalog returns 503 and leaves the ticket unchanged (TRIAPI-12, AC 12)
Proof: run tests | `tests/integration/test_triage_api.py::test_missing_active_catalog_returns_503 PASSED`

**C13** - The API server binds only to `127.0.0.1` (TRIAPI-13, AC 13)
Proof: run tests | `tests/integration/test_app_runtime.py::test_server_binds_to_loopback_only PASSED`

---

## Handoff

The feature's live state, written as it happens.

**Settled mid-build**: none.
**Dispatched**: none.
**Walked**: not yet; the feature is an API with no user-facing screen.

---

## Phase Execution Map

```text
T1 → T2
T2 → T3
T2 → T4
T2 → T5
```

Execution is strictly sequential by phase and task order; each task gets its own gate and atomic commit.
