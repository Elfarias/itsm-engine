# ticket-triage verification

**Verdict**: PASS
**Proofs**: `proofs.md` at `eba98c11eda6eb56dc9c3a95acbeb24037b0ae53`
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `test_triage_catalogs.py` `test_catalog_seed_is_versioned_and_referentially_consistent` | yes |
| C2 | `test_triage_catalogs.py` `test_public_api_exposes_no_catalog_admin_routes` | yes |
| C3 | `test_triage_rules.py` `test_priority_matrix_covers_all_nine_combinations` | yes |
| C4 | `test_triage_rules.py` `test_complete_facts_calculate_priority_and_use_catalog_mapped_team` | yes |
| C5 | `test_triage_rules.py` `test_catalog_mapping_controls_team_and_rejects_caller_assignment` | yes |
| C6 | `test_triage_service.py` `test_complete_evaluation_persists_snapshot_and_em_triagem` | yes |
| C7 | `test_triage_service.py` `test_missing_facts_or_team_mapping_leave_ticket_pending` | yes |
| C8 | `test_triage_service.py` `test_asset_service_conflict_leaves_ticket_pending` | yes |
| C9 | `test_triage_service.py` `test_pending_reevaluation_replaces_full_snapshot` | yes |
| C10 | `test_triage_service.py` `test_pending_identical_retry_is_idempotent` | yes |
| C11 | `test_triage_service.py` `test_different_facts_after_em_triagem_are_rejected` | yes |
| C12 | `test_triage_service.py` `test_invalid_facts_leave_ticket_unchanged` | yes |
| C13 | `test_triage_service.py` `test_concurrent_snapshots_reject_stale_revision` | yes |
| C14 | `test_triage_service.py` `test_complete_evaluation_persists_snapshot_and_em_triagem` | yes |
| C15 | `test_triage_service.py` `test_ticket_and_audit_write_failures_roll_back_evaluation` | yes |
| C16 | `test_triage_service.py` `test_em_triagem_retry_returns_stored_catalog_version` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C1 did not verify synthetic, vendor-neutral catalog content | The original test checked version IDs and relationships but not the seeded service, asset, or team records. | Assert the synthetic catalog records and their relationships. | `eba98c1` — C1 |
| C2 did not rule out catalog administration routes with unrelated path names | The original test only rejected paths containing `catalog` or `triage`. | Check exposed route/method pairs against the public API whitelist. | `eba98c1` — C2 |
| C4 did not prove complete evaluations use the priority matrix | The original test exercised only MEDIO/ALTA, which yields P2. | Evaluate all nine impact/urgency combinations with complete facts. | `eba98c1` — C4 |
| C5 did not prove mapping controls team selection | The original test checked one mapping without supplying caller team input. | Test an alternate catalog mapping and reject caller-supplied team assignment. | `eba98c1` — C5 |
| C12 left invalid urgency uncovered | The original service test checked invalid impact but not invalid urgency. | Assert invalid urgency is rejected without changing the ticket. | `eba98c1` — C12 |
| C14 did not prove the evaluation flow appends its audit event | The original test invoked repository save and audit methods directly. | Exercise `evaluate_ticket` and assert the resulting audit event carries the ticket and catalog version. | `eba98c1` — C14 |
| C15 covered only audit-write failure | The original rollback test did not fail the ticket evaluation write. | Verify explicit failure and rollback for both ticket-write and audit-write failures. | `eba98c1` — C15 |
| Migration constraints were not tested by violating them | Existing catalog tests did not attempt invalid active-version, relationship, domain, or revision writes. | Add focused integration assertions that representative invalid writes are rejected by the database constraints. | `eba98c1` — C1 |
