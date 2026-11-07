# KEDB Lookup Context

**Gathered:** 2026-11-06
**Spec:** `.specs/features/kedb-lookup/spec.md`
**Status:** Ready for Spec review

---

## Feature Boundary

Enrich the existing ticket interpretation proposal with deterministic
matches from a local Known Error Database (KEDB), including relevant
workaround guidance for operator review.

---

## Implementation Decisions

### KEDB source and matching

- The user selected `local_seeded_postgres`: keep the initial KEDB local in
  PostgreSQL; CRUD and import are outside this feature.
- The user selected `deterministic_text`: match against extracted facts
  without embeddings or LLM matching.
- Initial records will be synthetic demonstration examples, selected by
  the user as `synthetic_seed`.
- Matching prioritizes service; symptom matches act as fallback. The user
  selected `service_then_symptoms`.
- Service and symptom terms match by exact equality after case, accent,
  and whitespace normalization; the user selected `normalized_exact` to
  avoid suggestions from generic partial token overlap.

### Interpretation integration and failures

- The user selected `augment_interpretation`: add KEDB results to the
  existing interpretation response.
- The user selected `partial_success`: preserve the interpretation
  proposal if the KEDB lookup is unavailable; return an empty result list
  when there are no matches.
- Return explicit lookup status with the matches, selected as
  `status_field`; distinguish an empty successful result from an
  unavailable KEDB.
- Include the known-error ID and title, summary, match reasons, and
  workaround instructions, selected as `full_guidance`.
- KEDB records stay local and are not sent to OpenRouter, preserving the
  approved description-only provider data boundary.
- Workarounds are presented for operator review and are not executed
  automatically.

### Agent's Discretion

Use stable record-ID ordering to break ties among otherwise equally
relevant matches; do not introduce semantic search, confidence scores, or
provider calls.

### Declined / Undiscussed Gray Areas → Assumptions

None; the user resolved the identified KEDB source, matching, response
integration, and partial-failure decisions.

---

## Specific References

- User request: “Consultas à KEDB (Base de Erros Conhecidos): Enriquecer o
  diagnóstico dos incidentes cruzando os dados extraídos com uma base de
  erros conhecidos e soluções contornadas”.
- `.specs/features/llm-ticket-interpretation/context.md` restricts provider
  data to the stored ticket description and keeps extracted candidates as
  free text until explicit deterministic validation.
- `ARCHITECTURE.md` describes KEDB entries as known errors, symptoms,
  related services, and reference procedures; the current implementation
  has no KEDB data or lookup behavior.

## Deferred Ideas

None.
