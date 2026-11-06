# ticket-api proofs

**HEAD**: b13a10a
**Tree**: clean
**Shell**: C:/Program Files/Git\bin\bash.exe
**Result**: 13 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run tests / tests/integration/test_ticket_api.py::test_post_returns_uuid_novo_and_utc_timestamp PASSED` | pass |
| C2 | `run tests / tests/integration/test_ticket_api.py::test_post_rejects_missing_blank_and_whitespace_descriptions ` | pass |
| C3 | `run tests / tests/integration/test_ticket_api.py::test_post_rejects_description_over_4000_characters PASSED` | pass |
| C4 | `run tests / tests/integration/test_ticket_api.py::test_repeated_posts_create_distinct_tickets PASSED` | pass |
| C5 | `run tests / tests/integration/test_ticket_repository.py::test_create_commits_exactly_one_linked_audit_event PA` | pass |
| C6 | `run tests / tests/integration/test_ticket_api.py::test_audit_insert_failure_returns_503_and_rolls_back_ticket ` | pass |
| C7 | `run tests / tests/integration/test_ticket_api.py::test_local_ticket_endpoints_accept_requests_without_auth PAS` | pass |
| C8 | `run tests / tests/integration/test_app_runtime.py::test_server_binds_to_loopback_only PASSED` | pass |
| C9 | `run tests / tests/integration/test_ticket_api.py::test_get_returns_persisted_ticket_fields PASSED` | pass |
| C10 | `run tests / tests/integration/test_ticket_api.py::test_get_missing_ticket_returns_404 PASSED` | pass |
| C11 | `run tests / tests/integration/test_ticket_api.py::test_get_returns_ticket_after_app_restart PASSED` | pass |
| C12 | `run tests / tests/integration/test_audit_permissions.py::test_runtime_role_cannot_update_or_delete_audit_event` | pass |
| C13 | `run tests / tests/integration/test_ticket_api.py::test_get_invalid_uuid_returns_422 PASSED` | pass |

## Output

`Run tests` - exit 0

```
tests/integration/test_ticket_repository.py::test_audit_insert_failure_rolls_back_ticket PASSED [ 72%]
tests/integration/test_ticket_repository.py::test_get_ticket_returns_persisted_ticket_fields PASSED [ 77%]
tests/integration/test_ticket_repository.py::test_get_ticket_returns_none_for_unknown_id PASSED [ 81%]
tests/unit/test_ticket_schemas.py::test_ticket_create_schema_accepts_description_boundaries PASSED [ 86%]
tests/unit/test_ticket_schemas.py::test_ticket_create_schema_rejects_missing_blank_and_oversized_descriptions PASSED [ 90%]
tests/unit/test_ticket_schemas.py::test_ticket_create_schema_preserves_nonblank_description PASSED [ 95%]
tests/unit/test_ticket_schemas.py::test_ticket_response_schema_exposes_specified_fields PASSED [100%]

============================== warnings summary ===============================
..\..\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\Elon\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 22 passed, 1 warning in 17.44s ========================
```
