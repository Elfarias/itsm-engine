# API Básica de Chamados — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: skipped - medium scope; inline decisions are listed below.
**Status**: Approved
**Approved**: 2026-11-06 - user: "Aprovar as tarefas"
**Build**: none - no build, type-check or lint command is configured; `pytest -v` is the agreed validation command.
**Run tests**: `pytest -v`

## Inline Design Decisions

- Use FastAPI and Pydantic for the HTTP API and contracts.
- Use PostgreSQL through `psycopg` with explicit SQL. Store schema changes as SQL migrations; do not add an ORM or a migration framework for this slice.
- Run `postgres:17-alpine` locally through Docker Compose for development and integration tests. The test setup starts the database before `pytest -v`.
- Use separate schema-owner and application-runtime database roles. The runtime role receives only the table permissions needed by this feature; it cannot update or delete audit events.
- Bind the unauthenticated development server to `127.0.0.1`. Preserve the submitted description after validating that it is not blank.
- The project has no application code, test samples, test configuration, build configuration, or lint/type-check commands yet. `TECHNOLOGY-STACK.md` proposes pytest, and the user confirmed unit and integration tests with `pytest -v`.

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `TECHNOLOGY-STACK.md` proposes pytest; `README.md`, `PROJECT.md`, and `MPLEMENTATION-PLAN.md` describe required test coverage but do not define test commands. No code, tests, or test/build configuration exist; strong defaults applied. The user confirmed unit and integration tests and `pytest -v`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Pydantic request/response schemas | unit | Required and boundary fields; valid description; missing, blank, whitespace-only, and over-limit descriptions; UUID representation | `tests/unit/test_ticket_schemas.py` | `pytest -v` |
| PostgreSQL schema, roles, and repository | integration | Ticket defaults and constraints; transaction success and rollback; audit insert and append-only permissions; lookup of persisted records | `tests/integration/test_ticket_repository.py`, `tests/integration/test_audit_permissions.py` | `pytest -v` |
| FastAPI routes | integration | Every in-scope route: success, invalid input, missing record, duplicate submissions, persistence failure, and unauthenticated local requests | `tests/integration/test_ticket_api.py` | `pytest -v` |
| Application runtime binding | integration | Server listens on loopback only; no unauthenticated public listener | `tests/integration/test_app_runtime.py` | `pytest -v` |

## Gate Check Commands

> Generated from project documentation and the user's test-runner decision; confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | After unit-test tasks; the agreed command runs the complete test suite | `pytest -v` |
| Full | After integration-test tasks | `pytest -v` |
| Build | No separate build, type-check, or lint tool is configured | none - `pytest -v` is the only project validation command defined for this slice |

**Co-located tests:** Every task that adds or changes a tested layer includes its tests. The PostgreSQL integration fixture starts the local test database so the agreed `pytest -v` command can run the complete suite.

---

## Execution Plan

Phases run sequentially. Tasks in each phase execute in the listed order.

### Phase 1: Foundation

```text
T1 -> T2
T1 -> T3
```

### Phase 2: Persistence

```text
T2 -> T4
T3 -> T5
T4 -> T5
T5 -> T6
```

### Phase 3: API

```text
T1 -> T7
T3 -> T7
T5 -> T7
T1 -> T8
T3 -> T8
T6 -> T8
T7 -> T8
```

## Task Breakdown

### T1: Bootstrapping the local FastAPI application

**What**: Create the minimal Python project configuration and FastAPI entry point, including the unauthenticated development server bound explicitly to `127.0.0.1`.
**Where**: `app/main.py`
**Depends on**: None
**Reuses**: The FastAPI, Pydantic, PostgreSQL, and pytest stack specified in `TECHNOLOGY-STACK.md`.
**Requirement**: TKT-07, TKT-08

**Done when**:

- [x] `pytest -v` can import and start the application.
- [x] The development server binds to loopback and does not listen on a public interface.
- [x] One runtime integration test proves the loopback binding.
- [x] Test count: 1 runtime integration test passes.

**Tests**: integration
**Gate**: Full
**Commit**: `feat(api): bootstrap local FastAPI application`
**Status**: Complete
**Gate result**: `pytest -v` - 1 passed.

---

### T2: Configuring the local PostgreSQL test service

**What**: Configure the Docker Compose PostgreSQL service and test fixture, with distinct schema-owner and runtime roles and local-only database access.
**Where**: `compose.yaml`
**Depends on**: T1
**Reuses**: The PostgreSQL and Docker Compose choices in `TECHNOLOGY-STACK.md`.
**Requirement**: TKT-05, TKT-06, TKT-12

**Done when**:

- [x] The test fixture starts a healthy local PostgreSQL service before integration tests run.
- [x] The schema-owner and application-runtime roles are distinct and use local environment configuration without committed secrets.
- [x] One integration test verifies database readiness and role separation.
- [x] Test count: 1 database setup integration test passes.

**Tests**: integration
**Gate**: Full
**Commit**: `test(db): configure local PostgreSQL integration service`
**Status**: Complete
**Gate result**: `pytest -v` - 2 passed.

---

### T3: Defining ticket request and response schemas

**What**: Define the Pydantic request and response contracts for ticket creation and retrieval, including description bounds and UUID v4 identifiers.
**Where**: `app/tickets/schemas.py`
**Depends on**: T1
**Reuses**: Pydantic, as specified by `TECHNOLOGY-STACK.md`.
**Requirement**: TKT-01, TKT-02, TKT-03, TKT-09, TKT-13

**Done when**:

- [x] The request schema accepts descriptions from 1 through 4,000 characters and rejects missing, blank, and whitespace-only descriptions and descriptions over 4,000 characters.
- [x] The response schema represents the identifier as UUID and includes description, status, and creation timestamp.
- [x] Four unit tests cover valid and invalid description boundaries and response fields.
- [x] Test count: 4 schema unit tests pass.

**Tests**: unit
**Gate**: Quick
**Commit**: `feat(tickets): define ticket API schemas`
**Status**: Complete
**Gate result**: `pytest -v` - 6 passed.

---

### T4: Creating ticket and append-only audit tables

**What**: Add one SQL migration for ticket and audit-event tables, UUID and timestamp fields, initial `NOVO` state, description constraints, and runtime-role grants that deny audit-event updates and deletes.
**Where**: `migrations/001_tickets_and_audit.sql`
**Depends on**: T2
**Reuses**: PostgreSQL and the separate schema-owner/runtime roles from T2.
**Requirement**: TKT-01, TKT-05, TKT-12

**Done when**:

- [x] The migration creates the ticket and audit-event schema with the specified defaults and constraints.
- [x] The runtime role can insert and read audit events but cannot update or delete them.
- [x] Two PostgreSQL integration tests verify schema constraints and runtime-role permissions.
- [x] Test count: 2 schema and permission integration tests pass.

**Tests**: integration
**Gate**: Full
**Commit**: `feat(db): add ticket and append-only audit schema`
**Status**: Complete
**Gate result**: `pytest -v` - 8 passed.

---

### T5: Persisting ticket creation and its audit event atomically

**What**: Implement the repository operation that inserts a UUID ticket and exactly one creation audit event in the same PostgreSQL transaction.
**Where**: `app/tickets/repository.py`
**Depends on**: T3, T4
**Reuses**: The ticket and audit schema from T4 and the runtime database role from T2.
**Requirement**: TKT-05, TKT-06

**Done when**:

- [x] A successful repository operation commits the ticket and exactly one linked creation audit event.
- [x] A failure inserting the audit event rolls back the ticket and the event.
- [x] Two PostgreSQL integration tests prove transaction success and rollback.
- [x] Test count: 2 repository transaction integration tests pass.

**Tests**: integration
**Gate**: Full
**Commit**: `feat(tickets): persist ticket and audit event atomically`
**Status**: Complete
**Gate result**: `pytest -v` - 10 passed.

---

### T6: Retrieving persisted tickets from PostgreSQL

**What**: Implement the repository lookup operation that returns a persisted ticket by UUID or a not-found result.
**Where**: `app/tickets/repository.py`
**Depends on**: T5
**Reuses**: The ticket schema and repository connection handling from T4 and T5.
**Requirement**: TKT-09, TKT-10, TKT-11

**Done when**:

- [ ] Lookup returns the stored identifier, description, state, and timestamp for an existing ticket.
- [ ] Lookup returns a not-found result for an unknown UUID.
- [ ] Two PostgreSQL integration tests cover existing and missing records.
- [ ] Test count: 2 repository lookup integration tests pass.

**Tests**: integration
**Gate**: Full
**Commit**: `feat(tickets): add ticket lookup by UUID`

---

### T7: Creating tickets through the REST endpoint

**What**: Implement `POST /tickets` to validate the request, call the atomic repository operation, return the created ticket, and map persistence failure to `503`.
**Where**: `app/tickets/routes.py`
**Depends on**: T1, T3, T5
**Reuses**: The FastAPI application from T1, schemas from T3, and repository operation from T5.
**Requirement**: TKT-01, TKT-02, TKT-03, TKT-04, TKT-05, TKT-06, TKT-07

**Done when**:

- [ ] A valid local request without authentication returns `201` with a UUID v4, status `NOVO`, UTC creation time, and submitted description.
- [ ] Missing, blank, whitespace-only, and over-limit descriptions return `422` without persisting a ticket.
- [ ] Repeating the same valid request creates distinct tickets.
- [ ] An audit persistence failure returns `503` and leaves neither ticket nor audit event persisted.
- [ ] Six route integration tests cover creation, invalid input, maximum length, duplicate requests, unauthenticated local access, and transaction failure.
- [ ] Test count: 6 route integration tests pass.

**Tests**: integration
**Gate**: Full
**Commit**: `feat(api): add ticket creation endpoint`

---

### T8: Retrieving tickets through the REST endpoint

**What**: Implement `GET /tickets/{id}` to validate UUID path values, return persisted ticket fields, and report missing records.
**Where**: `app/tickets/routes.py`
**Depends on**: T1, T3, T6, T7
**Reuses**: The FastAPI application and route module from T1 and T7, the response schema from T3, and repository lookup from T6.
**Requirement**: TKT-07, TKT-09, TKT-10, TKT-11, TKT-13

**Done when**:

- [ ] A local request without authentication returns `200` and the persisted identifier, description, state, and timestamp.
- [ ] An unknown UUID returns `404`; a path value that is not a UUID returns `422`.
- [ ] A ticket created before the application is restarted remains available after the application is restarted while PostgreSQL remains available.
- [ ] Five route integration tests cover response fields, missing UUID, invalid UUID, application restart, and unauthenticated local access.
- [ ] Test count: 5 route integration tests pass.

**Tests**: integration
**Gate**: Full
**Commit**: `feat(api): add ticket lookup endpoint`

---

## Checks

**Run tests**: `pytest -v`

**C1** - `POST /tickets` returns `201` with a UUID v4, state `NOVO`, UTC timestamp, and the submitted description (TKT-01, AC 1)
Proof: run tests | tests/integration/test_ticket_api.py::test_post_returns_uuid_novo_and_utc_timestamp PASSED

**C2** - Missing, empty, and whitespace-only descriptions return `422` without creating a ticket (TKT-02, AC 2)
Proof: run tests | tests/integration/test_ticket_api.py::test_post_rejects_missing_blank_and_whitespace_descriptions PASSED

**C3** - A description longer than 4,000 characters returns `422` without creating a ticket (TKT-03, AC 3)
Proof: run tests | tests/integration/test_ticket_api.py::test_post_rejects_description_over_4000_characters PASSED

**C4** - Repeated valid POST requests with the same description create tickets with different identifiers (TKT-04, AC 4)
Proof: run tests | tests/integration/test_ticket_api.py::test_repeated_posts_create_distinct_tickets PASSED

**C5** - One successful ticket creation commits exactly one linked audit event in the same transaction (TKT-05, AC 5)
Proof: run tests | tests/integration/test_ticket_repository.py::test_create_commits_exactly_one_linked_audit_event PASSED

**C6** - Audit persistence failure returns `503` and leaves no ticket or creation event persisted (TKT-06, AC 6)
Proof: run tests | tests/integration/test_ticket_api.py::test_audit_insert_failure_returns_503_and_rolls_back_ticket PASSED

**C7** - Local ticket requests succeed without authentication (TKT-07, AC 7)
Proof: run tests | tests/integration/test_ticket_api.py::test_local_ticket_endpoints_accept_requests_without_auth PASSED

**C8** - The unauthenticated development server binds only to loopback (TKT-08, AC 8)
Proof: run tests | tests/integration/test_app_runtime.py::test_server_binds_to_loopback_only PASSED

**C9** - `GET /tickets/{id}` returns the persisted identifier, description, state, and creation timestamp (TKT-09, AC 1)
Proof: run tests | tests/integration/test_ticket_api.py::test_get_returns_persisted_ticket_fields PASSED

**C10** - `GET /tickets/{id}` returns `404` for an unknown UUID (TKT-10, AC 2)
Proof: run tests | tests/integration/test_ticket_api.py::test_get_missing_ticket_returns_404 PASSED

**C11** - A ticket remains retrievable after the application restarts while PostgreSQL remains available (TKT-11, AC 3)
Proof: run tests | tests/integration/test_ticket_api.py::test_get_returns_ticket_after_app_restart PASSED

**C12** - The runtime database role cannot update or delete audit events (TKT-12, AC 9)
Proof: run tests | tests/integration/test_audit_permissions.py::test_runtime_role_cannot_update_or_delete_audit_events PASSED

**C13** - `GET /tickets/{id}` returns `422` when the path value is not a UUID (TKT-13, AC 4)
Proof: run tests | tests/integration/test_ticket_api.py::test_get_invalid_uuid_returns_422 PASSED

## Handoff

**Settled mid-build**: User confirmed unit and integration tests with `pytest -v`; user chose `postgres:17-alpine` for local Compose, saying "postgres_image=postgres:17-alpine".
**Dispatched**: none.
**Walked**: not started.

## Phase Execution Map

```text
Phase 1 → Phase 2 → Phase 3

Phase 1: T1 -> T2
         T1 -> T3

Phase 2: T2 -> T4
         T3 -> T5
         T4 -> T5
         T5 -> T6

Phase 3: T1 -> T7
         T3 -> T7
         T5 -> T7
         T1 -> T8
         T3 -> T8
         T6 -> T8
         T7 -> T8
```
