# Tasks: State Migrations and Recovery

## Phase 1: Setup

- [x] T001 Record Feature 044 baseline, branch, DATA-01 state, surfaces, and exact validation commands in docs/gpt5-6-implementation-status.md
- [x] T002 [P] Add fresh, Feature 043, partial legacy, future-version, and corrupt database fixture builders in packages/data_vault/tests/fixtures.py
- [x] T003 [P] Add lifecycle result and exception contracts in packages/data_vault/src/data_vault/models.py

## Phase 2: Foundational

- [x] T004 Implement foreign-key, busy-timeout, read-only, and transaction connection policies in packages/data_vault/src/data_vault/state_store.py
- [x] T005 Implement a stable cross-platform bounded lifecycle lock in packages/data_vault/src/data_vault/lifecycle_lock.py
- [x] T006 Define canonical migration operations, immutable definitions, checksums, and ledger repository in packages/data_vault/src/data_vault/migrations.py
- [x] T007 Export the lifecycle contracts from packages/data_vault/src/data_vault/__init__.py and add the internal console entry point in packages/data_vault/pyproject.toml

## Phase 3: User Story 1 - Upgrade State Without Corruption

**Independent test**: Initialize fresh state and upgrade every supported legacy fixture; verify record preservation, exact ledger order, idempotency, and rollback at injected migration failure points.

- [x] T008 [P] [US1] Add fresh/legacy/idempotency/checksum/future-version migration tests in packages/data_vault/tests/test_migrations.py
- [x] T009 [P] [US1] Add per-migration interruption and user-record preservation tests in packages/data_vault/tests/test_migration_failures.py
- [x] T010 [US1] Implement numbered schema definitions for MCP, workspace/session, context/message, settings, and indexes in packages/data_vault/src/data_vault/migrations.py
- [x] T011 [US1] Implement preflight, transactional ordered upgrade, postflight, and typed status behavior in packages/data_vault/src/data_vault/migrations.py
- [x] T012 [US1] Extract catalog seed/update/reset behavior from schema migration into packages/tool_registry/src/tool_registry/catalog_reconcile.py
- [x] T013 [US1] Replace apps/api/src/api/database/migrate.py with a one-release delegate and call catalog reconciliation separately from apps/api/src/api/main.py
- [x] T014 [US1] Update API fixtures and catalog compatibility tests in apps/api/tests/conftest.py and apps/api/tests/test_mcp_catalog_seed.py

## Phase 4: User Story 2 - Inspect and Operate Database Lifecycle

**Independent test**: Run status, backup, upgrade, and restore through the CLI; verify stable JSON/exit contracts, restricted verified snapshots, tamper refusal, displaced-state rollback, and zero secret disclosure.

- [x] T015 [P] [US2] Add snapshot, manifest, tamper, atomic activation, and downgrade-by-restore tests in packages/data_vault/tests/test_backup_restore.py
- [x] T016 [P] [US2] Add CLI grammar, JSON, exit-code, permission, busy, and leak tests in packages/data_vault/tests/test_cli.py
- [x] T017 [US2] Implement consistent snapshot creation, manifest publication, digest/integrity validation, and retention-safe naming in packages/data_vault/src/data_vault/backup.py
- [x] T018 [US2] Implement candidate validation, displaced-state backup, atomic restore activation, and cleanup in packages/data_vault/src/data_vault/backup.py
- [x] T019 [US2] Implement status, backup, upgrade, and restore command dispatch in packages/data_vault/src/data_vault/cli.py
- [x] T020 [US2] Add operator procedures, failure recovery, retention, and rollback guidance in docs/operations/database-recovery.md and mkdocs.yml

## Phase 5: User Story 3 - Start Only on Verified State

**Independent test**: Start the API against current, prior, corrupt, interrupted, checksum-drifted, and future-version fixtures; only verified current state reaches runtime construction/readiness.

- [x] T021 [P] [US3] Add fail-closed lifespan and runtime-construction ordering tests in apps/api/tests/test_database_startup.py
- [x] T022 [P] [US3] Add direct-upgrade versus catalog-reconciliation separation tests in packages/tool_registry/tests/test_catalog_reconcile.py
- [x] T023 [US3] Make API lifespan propagate lifecycle failure before engines/managers are constructed in apps/api/src/api/main.py
- [x] T024 [US3] Add redacted structured startup/recovery diagnostics in apps/api/src/api/main.py and packages/data_vault/src/data_vault/models.py

## Phase 6: Polish and Cross-Cutting Verification

- [x] T025 Run focused DATA-01 migration, backup/restore, CLI, catalog, and startup suites plus a seeded-value output scan
- [x] T026 Verify the `wright-data-vault` wheel contains migrations/CLI resources and the public `wright-engineering` wheel has no private package dependency using scripts/build-python-distributions.sh and content inspection
- [x] T027 Update package documentation, status ledger, migration/rollback evidence, remaining risks, and exact next action in packages/data_vault/ and docs/gpt5-6-implementation-status.md
- [x] T028 Run `scripts/check-dev-merge.sh`, record exact results, mark Feature 044 review-ready, and stop before Feature 045

## Dependencies

- Setup (T001-T003) precedes foundational lifecycle contracts (T004-T007).
- User Story 1 depends on all foundational tasks and establishes the schema/status boundary used by Stories 2 and 3.
- User Story 2 depends on verified status and migration ledger semantics from User Story 1, but its backup fixtures can begin in parallel with catalog extraction.
- User Story 3 depends on the migration delegate and catalog separation from User Story 1; its characterization tests can be added while Story 2 implementation proceeds.
- Cross-cutting verification requires all stories complete.

## Parallel Opportunities

- T002 and T003 can proceed independently after T001.
- T008 and T009 characterize distinct successful and interrupted migration paths.
- T015 and T016 characterize backup and CLI contracts in separate files.
- T021 and T022 characterize API startup and catalog separation independently.

## Implementation Strategy

1. Establish typed results, connection policy, locking, immutable definitions, and the ledger.
2. Complete User Story 1 as the safety MVP: deterministic transactional upgrades with no catalog behavior.
3. Add verified snapshot/restore and operator commands.
4. Wire fail-closed startup and separate catalog reconciliation.
5. Verify package contents, leak posture, and the full dev merge gate before review.
