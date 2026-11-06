# ticket-triage proofs

**HEAD**: b498b59
**Tree**: clean
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 16 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run tests / tests/integration/test_triage_catalogs.py::test_catalog_seed_is_versioned_and_referentially_consis` | pass |
| C2 | `run tests / tests/integration/test_triage_catalogs.py::test_public_api_exposes_no_catalog_admin_routes PASSED` | pass |
| C3 | `run tests / tests/unit/test_triage_rules.py::test_priority_matrix_covers_all_nine_combinations PASSED` | pass |
| C4 | `run tests / tests/unit/test_triage_rules.py::test_complete_facts_calculate_priority_and_use_catalog_mapped_tea` | pass |
| C5 | `run tests / tests/unit/test_triage_rules.py::test_catalog_mapping_controls_team_and_rejects_caller_assignment ` | pass |
| C6 | `run tests / tests/integration/test_triage_service.py::test_complete_evaluation_persists_snapshot_and_em_triage` | pass |
| C7 | `run tests / tests/integration/test_triage_service.py::test_missing_facts_or_team_mapping_leave_ticket_pending ` | pass |
| C8 | `run tests / tests/integration/test_triage_service.py::test_asset_service_conflict_leaves_ticket_pending PASSED` | pass |
| C9 | `run tests / tests/integration/test_triage_service.py::test_pending_reevaluation_replaces_full_snapshot PASSED` | pass |
| C10 | `run tests / tests/integration/test_triage_service.py::test_pending_identical_retry_is_idempotent PASSED` | pass |
| C11 | `run tests / tests/integration/test_triage_service.py::test_different_facts_after_em_triagem_are_rejected PASSE` | pass |
| C12 | `run tests / tests/integration/test_triage_service.py::test_invalid_facts_leave_ticket_unchanged PASSED` | pass |
| C13 | `run tests / tests/integration/test_triage_service.py::test_concurrent_snapshots_reject_stale_revision PASSED` | pass |
| C14 | `run tests / tests/integration/test_triage_service.py::test_complete_evaluation_persists_snapshot_and_em_triage` | pass |
| C15 | `run tests / tests/integration/test_triage_service.py::test_ticket_and_audit_write_failures_roll_back_evaluatio` | pass |
| C16 | `run tests / tests/integration/test_triage_service.py::test_em_triagem_retry_returns_stored_catalog_version PAS` | pass |

## Output

`Run tests` - exit 0

```
tests/unit/test_triage_rules.py::test_priority_matrix_covers_all_nine_combinations PASSED [ 86%]
tests/unit/test_triage_rules.py::test_complete_facts_calculate_priority_and_use_catalog_mapped_team PASSED [ 88%]
tests/unit/test_triage_rules.py::test_catalog_mapping_controls_team_and_rejects_caller_assignment PASSED [ 91%]
tests/unit/test_triage_rules.py::test_missing_facts_or_team_mapping_produce_pending_without_assignment PASSED [ 93%]
tests/unit/test_triage_rules.py::test_asset_service_mismatch_produces_pending_without_assignment PASSED [ 95%]
tests/unit/test_triage_schemas.py::test_triage_facts_accept_allowed_values_and_optional_asset PASSED [ 97%]
tests/unit/test_triage_schemas.py::test_triage_facts_reject_invalid_values_and_caller_assignments PASSED [100%]

============================== warnings summary ===============================
..\..\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\Elon\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 45 passed, 1 warning in 17.56s ========================
```
