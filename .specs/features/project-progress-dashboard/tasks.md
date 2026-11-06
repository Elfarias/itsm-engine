# Project Progress Dashboard Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: skipped - this is a project-document progress table with a focused documentation contract test.
**Status**: Complete
**Approved**: 2026-11-06 - user: "Aprovar as tarefas"
**Build**: none - no separate build, type-check, or lint command is configured; pytest is the project validation command.
**Run tests**: `pytest -v tests/unit/test_project_progress.py`

---

## Test Coverage Matrix

> Generated from project docs and test configuration. `README.md`, `PROJECT.md`, and `pyproject.toml` define the current project context and pytest usage; no `AGENTS.md`, `CONTRIBUTING.md`, or documentation-specific test command was found.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Project progress documentation contract | unit | Verify all verified deliveries, links to source-of-truth artifacts, unprioritized roadmap entries, and same-delivery-commit maintenance policy | `tests/unit/test_project_progress.py` | `pytest -v tests/unit/test_project_progress.py` |

## Gate Check Commands

| Gate Level | When to Use | Command |
| ---------- | ---------- | ------- |
| Quick | After the documentation contract test | `pytest -v tests/unit/test_project_progress.py` |
| Full | Final feature validation | `pytest -v` |
| Build | No separate build, type-check, or lint command exists | `pytest -v` |

**Co-located tests:** T1 updates the progress document and its contract test together. The test verifies the documented statuses, links, backlog, and maintenance rule.

---

## Execution Plan

### Phase 1: Progress tracker

```text
T1
```

## Task Breakdown

### T1: Centralizing project progress in PROJECT.md

**What**: Add a single progress view in `PROJECT.md` that records delivered, in-progress, and planned scope, links each delivery to its detailed evidence, and requires updating the view in the same commit as each future delivery.
**Where**: `PROJECT.md`
**Depends on**: None
**Reuses**: The current implemented-scope and future-evolutions sections in `PROJECT.md`, plus feature task and verification files.
**Requirement**: PROGRESS-01, PROGRESS-02, PROGRESS-03, PROGRESS-04

**Done when**:

- [x] The dashboard lists the three existing verified deliveries with links to their specs, task checklists, and passing verification reports.
- [x] Planned scope matches `PROJECT.md` and is clearly unprioritized.
- [x] The maintenance rule requires updating the dashboard in the same commit as each feature delivery.
- [x] `tests/unit/test_project_progress.py` verifies the dashboard content and source links.
- [x] Gate check passes: `pytest -v tests/unit/test_project_progress.py`.
- [x] Test count: 4 focused tests pass; the full suite passes 62 tests.

**Tests**: unit
**Gate**: quick
**Commit**: `docs(progress): centralize project delivery status`
**Status**: Complete
**Gate result**: `pytest -v tests/unit/test_project_progress.py` - 4 passed; `pytest -v` - 62 passed, 1 pre-existing deprecation warning.

## Checks

**Run tests**: `pytest -v tests/unit/test_project_progress.py`

**C1** - `PROJECT.md` lists each existing verified delivery and links its specification, task checklist, and passing verification report (PROGRESS-01, AC 1 and 4)
Proof: run tests | `tests/unit/test_project_progress.py::test_dashboard_lists_verified_deliveries_and_evidence PASSED`

**C2** - `PROJECT.md` lists the documented future scope without assigning priorities (PROGRESS-02, AC 2)
Proof: run tests | `tests/unit/test_project_progress.py::test_dashboard_lists_unprioritized_roadmap PASSED`

**C3** - `PROJECT.md` requires refreshing the progress entry in the same commit as each delivery (PROGRESS-03, AC 3)
Proof: run tests | `tests/unit/test_project_progress.py::test_dashboard_requires_same_commit_updates PASSED`

**C4** - A delivery shown as complete is backed by a passing verification report (PROGRESS-04, AC 4)
Proof: run tests | `tests/unit/test_project_progress.py::test_completed_dashboard_rows_have_passing_verification PASSED`

## Handoff

**Settled during Specify**: User selected an unprioritized backlog and requested `PROJECT.md` be updated at the end of each delivery.
**Dispatched**: Verifier pending after the final proof run; screens not applicable because no criterion cites a capture.
**Walked**: not applicable; this is a documentation tracker with no user-facing application screen.
