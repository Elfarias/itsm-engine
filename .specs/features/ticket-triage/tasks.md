# Ticket Triage Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/ticket-triage/design.md`
**Status**: Approved
**Approved**: 2026-11-06 - user: "Aprovar as tarefas"
**Build**: none - no separate build, type-check or lint command is configured; `pytest -v` is the project validation command.
**Run tests**: `pytest -v`

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `README.md`, `PROJECT.md`, and `ARCHITECTURE.md` describe required test coverage; `TECHNOLOGY-STACK.md` selects pytest for unit and integration tests; `pyproject.toml` configures pytest test discovery. No `AGENTS.md`, `CONTRIBUTING.md`, CI workflow, coverage threshold, or lint/type-check configuration was found. Existing schema, repository, API, database setup, audit permission, and runtime tests were sampled; strong defaults applied to every criterion and edge case.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Triage schemas and deterministic rules | unit | All branches; one-to-one coverage for TRI-03 through TRI-05 and TRI-12; every rule edge case in the spec | `tests/unit/test_triage_schemas.py`, `tests/unit/test_triage_rules.py` | `pytest -v` |
| Catalog migration, repository and PostgreSQL permissions | integration | Catalog seed and references; key query paths; transaction success and rollback; append-only audit and least-privilege checks | `tests/integration/test_triage_catalogs.py`, `tests/integration/test_triage_repository.py` | `pytest -v` |
| Triage service, ticket states and concurrency | integration | One-to-one coverage for TRI-06 through TRI-16; complete, pending, retry, conflict, invalid-input and persistence-failure outcomes | `tests/integration/test_triage_service.py` | `pytest -v` |
| Public API surface | integration | Confirm no classification or catalog-administration endpoint is exposed | `tests/integration/test_triage_catalogs.py` | `pytest -v` |
| Documentation | none | Confirm descriptions match the approved spec and implemented behavior | `ARCHITECTURE.md`, `PROJECT.md`, `README.md` | Build gate only |

## Gate Check Commands

> Generated from `pyproject.toml`, current tests, and project documentation.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | After unit-test tasks | `pytest -v tests/unit` |
| Full | After integration-test tasks | `pytest -v` |
| Build | After documentation-only tasks; no separate build, type-check or lint command exists | `pytest -v` |

**Co-located tests:** Every task that changes a tested layer includes its tests. The integration fixture starts PostgreSQL and applies all ordered SQL migrations before the tests. Documentation-only tasks have no test requirement.

---

## Execution Plan

Phases run sequentially. Tasks within each phase execute in the listed order.

### Phase 1: Foundation

- T1: versioned catalog migration and test fixture.
- T2: typed triage domain schemas.

### Phase 2: Rules and Persistence

- T3: deterministic rules; depends on T1 and T2.
- T4: transactional repository; depends on T1 and T2.

### Phase 3: Service Integration

- T5: internal triage service; depends on T3 and T4.

### Phase 4: Documentation

- T6, T7 and T8: documentation updates; each depends on T5.

---

## Task Breakdown

### T1: Creating versioned PostgreSQL catalogs and migration support

**What**: Add the catalog version, service, asset, support-team and service-to-team schema; seed the initial synthetic catalog; add ticket classification columns, revision and audit metadata; and make integration tests apply every migration.
**Where**: `migrations/002_ticket_triage_catalogs.sql`
**Depends on**: None
**Reuses**: The PostgreSQL schema-owner/runtime-role model in `migrations/001_tickets_and_audit.sql` and the database fixture in `tests/integration/conftest.py`.
**Requirement**: TRI-01, TRI-02

**Done when**:

- [x] The migration creates version-scoped catalog records with foreign keys, seeds one active synthetic catalog version, and creates the ticket fields and audit metadata required by the design.
- [x] `itsm_runtime` can read catalog rows but cannot create, update or delete them; ticket updates are limited to classification and state columns, and audit events remain append-only.
- [x] The integration fixture applies all SQL migration files in stable order, and tests verify seeded relationships, runtime privileges and the absence of public catalog CRUD routes.
- [x] Test count: 3 catalog/schema/API-surface integration tests pass.
- [x] Gate check passes: `pytest -v`.

**Tests**: integration
**Gate**: full
**Commit**: `feat(db): add versioned triage catalogs`
**Commit hash**: `2388139`
**Gate result**: `pytest -v` - 25 passed, 1 pre-existing deprecation warning.
**Status**: Complete

---

### T2: Defining triage domain schemas

**What**: Define typed fact snapshots, catalog records, evaluation results, allowed impact/urgency/priority values and explicit domain errors.
**Where**: `app/triage/schemas.py`
**Depends on**: None
**Reuses**: Pydantic and `TicketStatus` from `app/tickets/schemas.py`.
**Requirement**: TRI-12

**Done when**:

- [x] Fact snapshots allow absent service, asset, impact and urgency facts; supplied impact/urgency values use closed enums, and caller-selected priority or team fields are rejected.
- [x] Invalid impact and urgency values are rejected before evaluation.
- [x] Unit tests cover valid snapshots, optional assets and invalid enum values.
- [x] Test count: 2 triage-schema unit tests pass.
- [x] Gate check passes: `pytest -v tests/unit`.

**Tests**: unit
**Gate**: quick
**Commit**: `feat(triage): define domain schemas`
**Commit hash**: `22780a2`
**Gate result**: `pytest -v tests/unit` - 6 passed; phase build `pytest -v` - 27 passed, 1 pre-existing deprecation warning.
**Status**: Complete

---

### T3: Implementing deterministic triage rules

**What**: Implement pure priority, sufficiency, service-team routing and asset-service consistency rules.
**Where**: `app/triage/rules.py`
**Depends on**: T1, T2
**Reuses**: The approved matrix in TRI-03 and typed domain values from T2.
**Requirement**: TRI-03, TRI-04, TRI-05, TRI-07, TRI-08

**Done when**:

- [x] Priority calculation matches all nine impact/urgency combinations in TRI-03.
- [x] Complete facts produce the matrix priority and only the catalog-mapped team.
- [x] Missing required facts, missing team mapping and an asset/service mismatch produce pending decisions with no priority or target team.
- [x] Unit tests cover every rule branch and the listed rule edge cases.
- [x] Test count: 4 triage-rule unit tests pass.
- [x] Gate check passes: `pytest -v tests/unit`.

**Tests**: unit
**Gate**: quick
**Commit**: `feat(triage): implement deterministic rules`
**Commit hash**: `177dfbf`
**Gate result**: `pytest -v tests/unit` - 10 passed.
**Status**: Complete

---

### T4: Implementing transactional triage persistence

**What**: Add repository operations to lock and load a ticket, load the active catalog, persist the full evaluation snapshot and append audit details using one caller-owned transaction.
**Where**: `app/triage/repository.py`
**Depends on**: T1, T2
**Reuses**: psycopg connection and transaction patterns in `app/tickets/repository.py`.
**Requirement**: TRI-06, TRI-14, TRI-15

**Done when**:

- [x] Repository queries load version-scoped service, asset and team relationships and lock the ticket row for update.
- [x] Persistence writes the complete snapshot, status, revision and catalog-version audit details in the caller's transaction.
- [x] A failure inserting the audit event rolls back all corresponding ticket changes; multiple evaluation events can be appended without granting audit update/delete privileges.
- [x] Integration tests cover persistence, audit details/permissions and rollback.
- [x] Test count: 3 triage-repository integration tests pass.
- [x] Gate check passes: `pytest -v`.

**Tests**: integration
**Gate**: full
**Commit**: `feat(triage): persist evaluation transactionally`
**Commit hash**: `99aa944`
**Gate result**: `pytest -v` - 34 passed, 1 pre-existing deprecation warning.
**Status**: Complete

---

### T5: Implementing the internal triage service

**What**: Add the internal service that validates ticket state and expected revision, selects the applicable catalog version, evaluates the full snapshot, and commits pending or complete outcomes.
**Where**: `app/triage/service.py`
**Depends on**: T3, T4
**Reuses**: `TicketStatus`, repository operations from T4 and pure decisions from T3.
**Requirement**: TRI-06, TRI-07, TRI-08, TRI-09, TRI-10, TRI-11, TRI-12, TRI-13, TRI-16

**Done when**:

- [x] Complete evaluations persist priority and mapped team and leave the ticket in `EM_TRIAGEM`; incomplete or conflicting facts replace the full snapshot and leave the ticket pending without priority or team.
- [x] Pending retries with identical facts and the same active catalog version are idempotent; a new pending evaluation uses the active version.
- [x] Different facts after transition to `EM_TRIAGEM` are rejected; an identical retry returns the stored result and catalog version even when a newer catalog is active.
- [x] Invalid references and enum values leave the ticket unchanged; invalid ticket states are rejected.
- [x] Concurrent different snapshots based on one pending revision result in at most one accepted update and an explicit conflict for the stale update.
- [x] Integration tests cover complete and pending outcomes, full-snapshot replacement, retries, invalid input, state guards and concurrent updates.
- [x] Test count: 9 triage-service integration tests pass.
- [x] Gate check passes: `pytest -v` - 43 passed, 1 pre-existing deprecation warning.

**Tests**: integration
**Gate**: full
**Commit**: `feat(triage): evaluate ticket snapshots`
**Gate result**: `pytest -v` - 43 passed, 1 pre-existing deprecation warning.
**Status**: Complete

---

### T6: Updating the architecture documentation

**What**: Update the architecture's catalog model, version policy, ticket classification fields, audit behavior and internal triage flow to match the implemented feature.
**Where**: `ARCHITECTURE.md`
**Depends on**: T5
**Reuses**: Existing architecture sections for the CMDB, priority rules, ticket states and audit.
**Requirement**: TRI-01, TRI-03, TRI-06, TRI-09, TRI-13, TRI-14

**Done when**:

- [x] Catalog tables, active-version behavior, revision conflicts, state outcomes and audit details agree with the approved Spec and implementation.
- [x] The documented priority matrix matches all nine combinations in TRI-03.
- [x] No public classification endpoint, CRUD interface, LLM or KEDB is described as part of this feature.
- [x] Documentation is reviewed against the implementation; no test is required for this documentation-only task.

**Tests**: none
**Gate**: build
**Commit**: `docs(architecture): document deterministic triage`
**Gate result**: `pytest -v` - 43 passed, 1 pre-existing deprecation warning.
**Status**: Complete

---

### T7: Updating the project requirements baseline

**What**: Update the project baseline to record that the initial priority matrix is approved and describe the versioned catalog and deterministic triage scope.
**Where**: `PROJECT.md`
**Depends on**: T5
**Reuses**: The existing scope, priority and data-insufficiency sections.
**Requirement**: TRI-01, TRI-03, TRI-07, TRI-08

**Done when**:

- [x] The matrix is no longer described as awaiting business validation.
- [x] The project scope distinguishes this internal deterministic service from later LLM and public API work.
- [x] Documentation matches the approved Spec and implementation; no test is required for this documentation-only task.

**Tests**: none
**Gate**: build
**Commit**: `docs(project): record approved triage rules`
**Gate result**: `pytest -v` - 43 passed, 1 pre-existing deprecation warning.
**Status**: Complete

---

### T8: Updating the project README

**What**: Update the README's triage flow and next steps to reflect the completed catalog and deterministic-rules slice.
**Where**: `README.md`
**Depends on**: T5
**Reuses**: The existing overview, state list and project documentation links.
**Requirement**: TRI-01, TRI-03, TRI-06

**Done when**:

- [ ] The README describes deterministic catalog-backed classification and no longer lists confirmation of the initial matrix as a pending next step.
- [ ] The README continues to identify LLM interpretation and external ITSM integration as later work.
- [ ] Documentation matches the approved Spec and implementation; no test is required for this documentation-only task.

**Tests**: none
**Gate**: build
**Commit**: `docs(readme): describe deterministic triage slice`

---

## Checks

**Run tests**: `pytest -v`

**C1** - A versioned synthetic catalog contains stable service, asset and support-team identifiers with valid service-team and asset-service relations (TRI-01, AC 1)
Proof: run tests | tests/integration/test_triage_catalogs.py::test_catalog_seed_is_versioned_and_referentially_consistent PASSED

**C2** - No public API route exposes catalog create, update or delete operations (TRI-02, AC 2)
Proof: run tests | tests/integration/test_triage_catalogs.py::test_public_api_exposes_no_catalog_admin_routes PASSED

**C3** - All nine impact/urgency pairs map to the exact priority matrix (TRI-03, AC 3)
Proof: run tests | tests/unit/test_triage_rules.py::test_priority_matrix_covers_all_nine_combinations PASSED

**C4** - Complete valid facts return the priority specified by the matrix (TRI-04, AC 4)
Proof: run tests | tests/unit/test_triage_rules.py::test_complete_facts_calculate_priority_and_use_catalog_mapped_team PASSED

**C5** - The service mapping, not caller input, determines the target team (TRI-05, AC 5)
Proof: run tests | tests/unit/test_triage_rules.py::test_complete_facts_calculate_priority_and_use_catalog_mapped_team PASSED

**C6** - A complete evaluation persists its facts, priority and mapped team and leaves the ticket in `EM_TRIAGEM` (TRI-06, AC 6)
Proof: run tests | tests/integration/test_triage_service.py::test_complete_evaluation_persists_snapshot_and_em_triagem PASSED

**C7** - Missing facts or a missing team mapping persist valid partial facts as pending with no priority or team (TRI-07, AC 7)
Proof: run tests | tests/integration/test_triage_service.py::test_missing_facts_or_team_mapping_leave_ticket_pending PASSED

**C8** - An asset related to a different service leaves the ticket pending without priority or team (TRI-08, AC 8)
Proof: run tests | tests/integration/test_triage_service.py::test_asset_service_conflict_leaves_ticket_pending PASSED

**C9** - Re-evaluating a pending ticket replaces the prior facts with the complete new snapshot (TRI-09, AC 9)
Proof: run tests | tests/integration/test_triage_service.py::test_pending_reevaluation_replaces_full_snapshot PASSED

**C10** - Repeating a pending evaluation with identical facts and the same active catalog version has no duplicate side effects (TRI-10, AC 10)
Proof: run tests | tests/integration/test_triage_service.py::test_pending_identical_retry_is_idempotent PASSED

**C11** - Different facts after a ticket reaches `EM_TRIAGEM` are rejected without changing its classification (TRI-11, AC 11)
Proof: run tests | tests/integration/test_triage_service.py::test_different_facts_after_em_triagem_are_rejected PASSED

**C12** - Unknown references or invalid impact/urgency values are rejected without changing the ticket (TRI-12, AC 12)
Proof: run tests | tests/integration/test_triage_service.py::test_invalid_facts_leave_ticket_unchanged PASSED

**C13** - Competing snapshots for one pending revision accept at most one update and reject the stale request explicitly (TRI-13, AC 13)
Proof: run tests | tests/integration/test_triage_service.py::test_concurrent_snapshots_reject_stale_revision PASSED

**C14** - A changed evaluation appends an audit event associated with the ticket and catalog version (TRI-14, AC 14)
Proof: run tests | tests/integration/test_triage_repository.py::test_evaluation_audit_records_catalog_version PASSED

**C15** - An audit write failure rolls back the ticket evaluation and its audit event (TRI-15, AC 15)
Proof: run tests | tests/integration/test_triage_repository.py::test_audit_failure_rolls_back_evaluation PASSED

**C16** - An identical retry in `EM_TRIAGEM` returns the stored result and catalog version after the active catalog changes (TRI-16, AC 16)
Proof: run tests | tests/integration/test_triage_service.py::test_em_triagem_retry_returns_stored_catalog_version PASSED

---

## Handoff

The feature's live state, written as it happens - a compaction gives no warning.

**Settled mid-build**: none; T1-T7 complete, next is T8.
**Dispatched**: none; 8 tasks fit within one inline batch.
**Walked**: not yet; no user-facing screen or public classification API is in scope.

---

## Phase Execution Map

```text
T1 -> T3
T2 -> T3
T1 -> T4
T2 -> T4
T3 -> T5
T4 -> T5
T5 -> T6
T5 -> T7
T5 -> T8
```

Execution is strictly sequential by phase and task order; independent tasks remain without dependency edges.
