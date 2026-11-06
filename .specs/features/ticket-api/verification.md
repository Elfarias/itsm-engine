# ticket-api verification

**Verdict**: PASS
**Proofs**: `proofs.md` at 6b4b7d3
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/integration/test_ticket_api.py` `test_post_returns_uuid_novo_and_utc_timestamp` | yes |
| C2 | `tests/integration/test_ticket_api.py` `test_post_rejects_missing_blank_and_whitespace_descriptions` | yes |
| C3 | `tests/integration/test_ticket_api.py` `test_post_rejects_description_over_4000_characters` | yes |
| C4 | `tests/integration/test_ticket_api.py` `test_repeated_posts_create_distinct_tickets` | yes |
| C5 | `tests/integration/test_ticket_repository.py` `test_create_commits_exactly_one_linked_audit_event` | yes |
| C6 | `tests/integration/test_ticket_api.py` `test_audit_insert_failure_returns_503_and_rolls_back_ticket` | yes |
| C7 | `tests/integration/test_ticket_api.py` `test_local_ticket_endpoints_accept_requests_without_auth` | yes |
| C8 | `tests/integration/test_app_runtime.py` `test_server_binds_to_loopback_only` | yes |
| C9 | `tests/integration/test_ticket_api.py` `test_get_returns_persisted_ticket_fields` | yes |
| C10 | `tests/integration/test_ticket_api.py` `test_get_missing_ticket_returns_404` | yes |
| C11 | `tests/integration/test_ticket_api.py` `test_get_returns_ticket_after_app_restart` | yes |
| C12 | `tests/integration/test_audit_permissions.py` `test_runtime_role_cannot_update_or_delete_audit_events` | yes |
| C13 | `tests/integration/test_ticket_api.py` `test_get_invalid_uuid_returns_422` | yes |

## Findings

None - all checks hold at HEAD; extra boundary probes also accepted a 1-character description and a padded nonblank description while rejecting a whitespace-only description.