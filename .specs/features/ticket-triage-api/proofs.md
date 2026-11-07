# ticket-triage-api proofs

**HEAD**: af612d5
**Tree**: clean
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 13 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run tests / tests/unit/test_triage_api_schemas.py::test_triage_request_validates_revision_and_complete_partial` | pass |
| C2 | `run tests / tests/integration/test_triage_api.py::test_complete_triage_returns_persisted_result PASSED` | pass |
| C3 | `run tests / tests/integration/test_triage_api.py::test_complete_triage_returns_persisted_result PASSED` | pass |
| C4 | `run tests / tests/integration/test_triage_api.py::test_partial_and_conflicting_facts_return_pending PASSED` | pass |
| C5 | `run tests / tests/integration/test_triage_api.py::test_missing_ticket_returns_404 PASSED` | pass |
| C6 | `run tests / tests/integration/test_triage_api.py::test_invalid_request_and_catalog_facts_return_422_without_ch` | pass |
| C7 | `run tests / tests/integration/test_triage_api.py::test_stale_revision_and_invalid_state_return_409 PASSED` | pass |
| C8 | `run tests / tests/integration/test_triage_api.py::test_pending_identical_retry_is_idempotent PASSED` | pass |
| C9 | `run tests / tests/integration/test_triage_api.py::test_pending_retry_uses_new_active_catalog_version PASSED` | pass |
| C10 | `run tests / tests/integration/test_triage_api.py::test_em_triagem_retry_returns_stored_catalog_version PASSED` | pass |
| C11 | `run tests / tests/integration/test_triage_api.py::test_evaluation_or_audit_failure_returns_503_without_partial` | pass |
| C12 | `run tests / tests/integration/test_triage_api.py::test_missing_active_catalog_returns_503 PASSED` | pass |
| C13 | `run tests / tests/integration/test_app_runtime.py::test_server_binds_to_loopback_only PASSED` | pass |

## Output

`Run tests` - exit 0

```
tests/unit/test_triage_rules.py::test_priority_matrix_covers_all_nine_combinations PASSED [ 89%]
tests/unit/test_triage_rules.py::test_complete_facts_calculate_priority_and_use_catalog_mapped_team PASSED [ 91%]
tests/unit/test_triage_rules.py::test_catalog_mapping_controls_team_and_rejects_caller_assignment PASSED [ 93%]
tests/unit/test_triage_rules.py::test_missing_facts_or_team_mapping_produce_pending_without_assignment PASSED [ 94%]
tests/unit/test_triage_rules.py::test_asset_service_mismatch_produces_pending_without_assignment PASSED [ 96%]
tests/unit/test_triage_schemas.py::test_triage_facts_accept_allowed_values_and_optional_asset PASSED [ 98%]
tests/unit/test_triage_schemas.py::test_triage_facts_reject_invalid_values_and_caller_assignments PASSED [100%]

============================== warnings summary ===============================
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\Elon\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 58 passed, 1 warning in 23.94s ========================
```
