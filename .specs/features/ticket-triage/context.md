# Ticket Triage Context

**Gathered:** 2026-11-06
**Spec:** `.specs/features/ticket-triage/spec.md`
**Status:** T4 complete; ready to execute T5

---

## Feature Boundary

The next feature starts with reference catalogs and deterministic ticket-classification rules. The current impact/urgency priority matrix is the initial rule.

## Implementation Decisions

- The user selected "Catálogos e regras determinísticas (recomendado)" as the next project slice.
- The user chose "Usar a matriz atual como regra inicial".
- The user chose synthetic demonstration records and requested formats used by leading ITSM products.
- The user chose a vendor-neutral, interoperable ITSM/CMDB model for the synthetic records.
- The user chose versioned initial catalog data without administrative CRUD endpoints.
- The user deferred the KEDB from this feature.
- The user chose an internal classification service, with API and LLM integration in a later feature.
- The user chose `PENDENTE_INFORMACAO` when required information or a service mapping is missing; the system must not invent a classification.
- The user chose to persist the classification fields on the ticket.
- The user chose `EM_TRIAGEM` as the status after a complete deterministic evaluation, until the future ITSM integration confirms completion.
- The user chose idempotent retries for identical classification inputs; retries with different inputs are rejected.
- The user chose `PENDENTE_INFORMACAO`, with no priority or team assignment, when the provided asset conflicts with the service mapping.
- The user chose to persist validated partial facts while leaving priority and team assignment unset until classification is complete.
- The user chose to allow updated facts to re-evaluate a pending ticket; after transition to `EM_TRIAGEM`, only an identical retry is accepted.
- The user chose full-snapshot semantics for re-evaluation: each call replaces the previous fact snapshot with the complete currently known facts.
- The user chose conflict rejection for concurrent, different re-evaluations of the same pending ticket: one update may be accepted and the competing update must be retried explicitly.
- The user chose to use the active catalog version for each new evaluation of a pending ticket. An identical retry of a ticket already in `EM_TRIAGEM` returns the previously persisted result and catalog version.

## Agent's Discretion

None delegated.

## Declined / Undiscussed Gray Areas → Assumptions

None.

## Specific References

The project and architecture baselines define simulated service, asset, team, and operational-knowledge data, plus deterministic priority and service-to-team routing. The chosen first slice excludes KEDB.

## Deferred Ideas

LLM provider, data-handling policy, and structured extraction remain for a later feature slice.
