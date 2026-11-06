# Ticket Triage API Context

**Gathered:** 2026-11-06
**Spec:** `.specs/features/ticket-triage-api/spec.md`
**Status:** Ready for task approval

---

## Feature Boundary

Expose the existing structured triage service through an API restricted to
local development. This feature does not add LLM-based fact extraction or
public-network access.

---

## Implementation Decisions

### Access scope

- The endpoint is unauthenticated and restricted to localhost for local
  development. The user selected `local_only`.

### Workflow

- Add a separate endpoint to evaluate an existing ticket. The user chose
  `separate_existing`, preserving the existing ticket-creation contract
  and enabling reevaluation with an expected revision.

### Existing triage behavior

- Preserve the approved `ticket-triage` behavior for partial facts,
  persisted snapshots, retries, revision conflicts, status transitions,
  catalog selection, and transactional audit.

### HTTP outcomes and retries

- Valid partial or inconsistent facts are persisted as
  `PENDENTE_INFORMACAO` and return HTTP 200. The user selected
  `persist_200`.
- A missing ticket returns 404; invalid facts or catalog references return
  422; stale revisions and incompatible ticket states return 409. The
  user selected `standard`.
- Repeating an identical pending snapshot with the same active catalog
  version does not duplicate side effects. If the active catalog changed,
  the pending ticket is re-evaluated. An identical retry for a ticket in
  `EM_TRIAGEM` returns the stored result regardless of the active catalog.
  The user selected `active_catalog`.

---

## Agent's Discretion

- API details already determined by the current application and the
  approved `ticket-triage` specification.

---

## Declined / Undiscussed Gray Areas → Assumptions

- HTTP success shape, catalog outage response, and server binding follow
  the current API and approved triage service conventions.

---

## Specific References

- `.specs/features/ticket-triage/spec.md`
- `.specs/features/ticket-api/spec.md`

---

## Deferred Ideas

- Public-network API access, authentication, LLM extraction, KEDB lookup,
  and external ITSM integration remain outside this feature.
