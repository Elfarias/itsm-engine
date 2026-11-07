# kedb-lookup proofs

**HEAD**: c891bdb
**Tree**: clean
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 11 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run tests / tests/integration/test_ticket_interpretation_api.py::test_interpretation_queries_kedb_with_extract` | pass |
| C2 | `run tests / tests/unit/test_kedb_normalization.py::test_normalization_handles_accents_whitespace_and_case PASS` | pass |
| C3 | `run tests / tests/integration/test_kedb_repository.py::test_search_matches_by_service_candidate PASSED` | pass |
| C4 | `run tests / tests/integration/test_kedb_repository.py::test_search_falls_back_to_symptoms PASSED` | pass |
| C5 | `run tests / tests/integration/test_kedb_repository.py::test_matches_ordered_by_error_id_asc PASSED` | pass |
| C6 | `run tests / tests/unit/test_kedb_schemas.py::test_kedb_match_schema_accepts_valid_payload PASSED` | pass |
| C7 | `run tests / tests/unit/test_kedb_service.py::test_service_returns_available_status_with_matches PASSED` | pass |
| C8 | `run tests / tests/integration/test_ticket_interpretation_api.py::test_kedb_database_failure_returns_partial_su` | pass |
| C9 | `run tests / tests/unit/test_openrouter_client.py::test_client_sends_schema_constrained_description_only_reques` | pass |
| C10 | `run tests / tests/integration/test_ticket_interpretation_api.py::test_kedb_lookup_leaves_ticket_and_audit_unch` | pass |
| C11 | `run tests / tests/integration/test_app_runtime.py::test_server_binds_to_loopback_only PASSED` | pass |

## Output

`Run tests` - exit 0

```
tests/unit/test_triage_rules.py::test_priority_matrix_covers_all_nine_combinations PASSED [ 93%]
tests/unit/test_triage_rules.py::test_complete_facts_calculate_priority_and_use_catalog_mapped_team PASSED [ 94%]
tests/unit/test_triage_rules.py::test_catalog_mapping_controls_team_and_rejects_caller_assignment PASSED [ 95%]
tests/unit/test_triage_rules.py::test_missing_facts_or_team_mapping_produce_pending_without_assignment PASSED [ 96%]
tests/unit/test_triage_rules.py::test_asset_service_mismatch_produces_pending_without_assignment PASSED [ 97%]
tests/unit/test_triage_schemas.py::test_triage_facts_accept_allowed_values_and_optional_asset PASSED [ 98%]
tests/unit/test_triage_schemas.py::test_triage_facts_reject_invalid_values_and_caller_assignments PASSED [100%]

============================== warnings summary ===============================
..\..\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\Elon\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 96 passed, 1 warning in 21.25s ========================
```
