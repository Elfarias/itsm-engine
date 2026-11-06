# Project Progress Dashboard Specification

**Approved**: 2026-11-06 - user: "Aprovar a Spec"
**Status**: Verified

## Problem Statement

Project progress is split between `PROJECT.md` and separate feature task files. Readers cannot quickly see all completed deliveries and remaining scope in one place, and the central summary can become stale after new deliveries.

## Goals

- Provide one project-level view of completed, in-progress, and planned work.
- Link completed and active deliveries to their detailed specifications and task checklists.
- Keep the view synchronized with each feature delivery.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Web-based dashboard or project-management integration | A maintained Markdown document is sufficient for the current project. |
| Prioritizing future items | The user chose to keep the backlog unprioritized. |
| Replacing feature specifications and task checklists | Those files remain the detailed source of truth for each feature. |

## Assumptions & Open Questions

| Decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Central tracker location | `PROJECT.md` | It is the existing project overview and the file the user identified. | y |
| Backlog order | No priority order; list future work as planned | The user selected an unprioritized backlog. | y |
| Detailed status source | Feature `tasks.md` and `verification.md` files | These contain task completion and independent verification evidence. | y |

**Open questions:** none.

## User Stories

### P1: Read project progress in one place

**User Story**: Como pessoa acompanhando o projeto, quero consultar um único arquivo para saber o que foi entregue, o que está em andamento e o que ainda está planejado.

**Why P1**: Evita que o progresso dependa de localizar e combinar vários documentos.

**Acceptance Criteria**:

1. WHEN a reader opens `PROJECT.md` THEN the document SHALL show a progress table with delivery name, status, delivered scope, and links to the detailed feature specification and task checklist.
2. WHEN a reader reviews planned work THEN `PROJECT.md` SHALL list the future scope already recorded in the project without implying an order or priority.
3. WHEN a feature delivery changes its implementation status THEN the delivery SHALL update the corresponding `PROJECT.md` progress entry in the same delivery commit.
4. WHEN a feature is marked complete in the progress table THEN its linked task checklist SHALL show all tasks complete, and any required verification report SHALL show a passing verdict.

**Independent Test**: Compare the progress table with each feature's tasks and verification artifacts, then confirm the future entries match the roadmap and have no priority labels.

## Edge Cases

- A feature without a verification report must not be presented as independently verified.
- A newly started feature must appear as in progress rather than as complete.
- Future scope without an approved delivery sequence remains unprioritized.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| PROGRESS-01 | P1: Read project progress in one place | Execute | Verified |
| PROGRESS-02 | P1: Read project progress in one place | Execute | Verified |
| PROGRESS-03 | P1: Read project progress in one place | Execute | Verified |
| PROGRESS-04 | P1: Read project progress in one place | Execute | Verified |

**Coverage:** 4 total, 4 mapped to the story, 0 unmapped.

## Differences from the source

None. No binding screen or design reference was provided.

## Sources

- `PROJECT.md` - project scope, implemented slice, and future evolutions.
- `.specs/features/ticket-api/tasks.md` - ticket API task status.
- `.specs/features/ticket-triage/tasks.md` - deterministic triage task status.
- `.specs/features/ticket-triage-api/tasks.md` and `verification.md` - local triage API delivery and verification.

## Success Criteria

- `PROJECT.md` identifies all delivered features and their status with links to detailed evidence.
- The planned work is visible in the same progress view, without invented priorities.
- The project instructions in `PROJECT.md` require updating that view in every feature delivery commit.
