# kedb-lookup verification

**Verdict**: PASS
**Proofs**: `proofs.md` at c891bdb
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/integration/test_ticket_interpretation_api.py::test_interpretation_queries_kedb_with_extracted_facts` | yes |
| C2 | `tests/unit/test_kedb_normalization.py::test_normalization_handles_accents_whitespace_and_case` | yes |
| C3 | `tests/integration/test_kedb_repository.py::test_search_matches_by_service_candidate` | yes |
| C4 | `tests/integration/test_kedb_repository.py::test_search_falls_back_to_symptoms` | yes |
| C5 | `tests/integration/test_kedb_repository.py::test_matches_ordered_by_error_id_asc` | yes |
| C6 | `tests/unit/test_kedb_schemas.py::test_kedb_match_schema_accepts_valid_payload` | yes |
| C7 | `tests/unit/test_kedb_service.py::test_service_returns_available_status_with_matches` | yes |
| C8 | `tests/integration/test_ticket_interpretation_api.py::test_kedb_database_failure_returns_partial_success` | yes |
| C9 | `tests/unit/test_openrouter_client.py::test_client_sends_schema_constrained_description_only_request` | yes |
| C10 | `tests/integration/test_ticket_interpretation_api.py::test_kedb_lookup_leaves_ticket_and_audit_unchanged` | yes |
| C11 | `tests/integration/test_app_runtime.py::test_server_binds_to_loopback_only` | yes |

## Findings

None - Probed each contract, normalization, repository query, fallback behavior, partial failure resilience, and local runtime boundary at source HEAD c891bdb; no failing or under-specified check remained.

