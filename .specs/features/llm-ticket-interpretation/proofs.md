# llm-ticket-interpretation proofs

**HEAD**: 4169f2a
**Tree**: clean
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 16 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run tests / tests/unit/test_interpretation_schemas.py::test_interpretation_schema_accepts_complete_and_partial` | pass |
| C2 | `run tests / tests/unit/test_openrouter_client.py::test_client_sends_schema_constrained_description_only_reques` | pass |
| C3 | `run tests / tests/unit/test_openrouter_client.py::test_client_maps_missing_config_and_provider_failures_withou` | pass |
| C4 | `run tests / tests/unit/test_interpretation_service.py::test_service_returns_partial_proposal_and_propagates_in` | pass |
| C5 | `run tests / tests/unit/test_interpretation_service.py::test_service_treats_description_as_untrusted_without_ot` | pass |
| C6 | `run tests / tests/integration/test_ticket_interpretation_api.py::test_interpretation_returns_proposal_for_exis` | pass |
| C7 | `run tests / tests/integration/test_ticket_interpretation_api.py::test_missing_and_unavailable_ticket_lookups_r` | pass |
| C8 | `run tests / tests/integration/test_ticket_interpretation_api.py::test_provider_failures_return_errors_without_` | pass |
| C9 | `run tests / tests/integration/test_ticket_interpretation_api.py::test_provider_failures_return_errors_without_` | pass |
| C10 | `run tests / tests/integration/test_ticket_interpretation_api.py::test_provider_failures_return_errors_without_` | pass |
| C11 | `run tests / tests/integration/test_ticket_interpretation_api.py::test_interpretation_does_not_log_sensitive_co` | pass |
| C12 | `run tests / tests/integration/test_app_runtime.py::test_server_binds_to_loopback_only PASSED` | pass |
| C13 | `run tests / tests/unit/test_interpretation_docs.py::test_readme_documents_local_proposal_flow_and_configuratio` | pass |
| C14 | `run tests / tests/unit/test_interpretation_docs.py::test_architecture_documents_provider_and_deterministic_bou` | pass |
| C15 | `run tests / tests/unit/test_project_progress.py::test_dashboard_lists_verified_interpretation_delivery PASSED` | pass |
| C16 | `run tests / tests/unit/test_project_progress.py::test_dashboard_lists_verified_interpretation_delivery PASSED` | pass |

## Output

`Run tests` - exit 0

```
tests/unit/test_triage_rules.py::test_priority_matrix_covers_all_nine_combinations PASSED [ 92%]
tests/unit/test_triage_rules.py::test_complete_facts_calculate_priority_and_use_catalog_mapped_team PASSED [ 93%]
tests/unit/test_triage_rules.py::test_catalog_mapping_controls_team_and_rejects_caller_assignment PASSED [ 94%]
tests/unit/test_triage_rules.py::test_missing_facts_or_team_mapping_produce_pending_without_assignment PASSED [ 96%]
tests/unit/test_triage_rules.py::test_asset_service_mismatch_produces_pending_without_assignment PASSED [ 97%]
tests/unit/test_triage_schemas.py::test_triage_facts_accept_allowed_values_and_optional_asset PASSED [ 98%]
tests/unit/test_triage_schemas.py::test_triage_facts_reject_invalid_values_and_caller_assignments PASSED [100%]

============================== warnings summary ===============================
..\..\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\Elon\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 79 passed, 1 warning in 28.64s ========================
```
