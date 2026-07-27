# Tasks: Secrets, Container, and Provider Configuration

## Phase 1: Setup

- [x] T001 Record Feature 043 baseline, branch, finding state, and exact validation commands in docs/gpt5-6-implementation-status.md
- [x] T002 [P] Add shared credential/redaction test fixtures and leak-scan helpers in packages/core/tests/conftest.py and tests/security/
- [x] T003 [P] Add container security contract fixtures for current and legacy deployment definitions in tests/test_container_security_contract.py

## Phase 2: Foundational

- [x] T004 Add provider-neutral CredentialReference and SecretProvider contracts in packages/core/src/core/secrets.py
- [x] T005 Implement stable lock-file, temp-file, fsync, permission, and atomic-replace transactions in packages/core/src/core/atomic_secret_store.py
- [x] T006 Add shared recursive key/value redaction primitives in packages/core/src/core/redaction.py
- [x] T007 Export shared security contracts and document package ownership in packages/core/src/core/__init__.py and packages/core/README.md

## Phase 3: User Story 1 - Configure Providers Without Secret Disclosure

**Independent test**: Configure API, Git, MCP, and integration credentials; verify legitimate consumers receive values while API responses, SQLite, argv, logs, and diagnostics contain none.

- [x] T008 [P] [US1] Add masked settings and leak regression tests in apps/api/tests/test_settings_security.py
- [x] T009 [P] [US1] Add Git argv/URL/askpass characterization tests in packages/core/tests/test_git_credentials.py
- [x] T010 [P] [US1] Add MCP atomic concurrency and protocol-log redaction tests in packages/tool_registry/tests/test_secret_security.py
- [x] T011 [US1] Replace plaintext settings models and router behavior with credential status/write semantics in apps/api/src/api/schemas/settings.py and apps/api/src/api/routers/settings.py
- [x] T012 [US1] Adapt MCP credential services to the shared provider while preserving status contracts in packages/tool_registry/src/tool_registry/secrets.py and packages/tool_registry/src/tool_registry/services.py
- [x] T013 [US1] Replace tokenized Git URLs with short-lived askpass execution in packages/core/src/core/workspace.py
- [x] T014 [US1] Redact MCP commands, protocol payloads, stdout, stderr, errors, and API log output in packages/tool_registry/src/tool_registry/runners/ and apps/api/src/api/routers/logs.py

## Phase 4: User Story 2 - Upgrade Existing Secrets Safely

**Independent test**: Migrate representative legacy keys, verify backup/import/plaintext removal, simulate interruption, and restore without printing values.

- [x] T015 [P] [US2] Add backup, idempotency, interruption, fail-closed, and restore tests in apps/api/tests/test_secret_migration.py
- [x] T016 [US2] Implement backup-first credential extraction and verification seam in apps/api/src/api/database/secret_migration.py
- [x] T017 [US2] Invoke migration fail-closed during API lifespan and expose redacted recovery status in apps/api/src/api/main.py
- [x] T018 [US2] Add operator migration, rotation, recovery, and rollback commands/documentation in docs/security/credential-management.md and scripts/

## Phase 5: User Story 3 - Run a Least-Privilege Appliance

**Independent test**: Inspect and smoke the appliance to prove non-root execution, no sudo/default key, restricted privileges, narrow persistence, and successful documented state upgrade.

- [x] T019 [P] [US3] Add Dockerfile, supervisor, entrypoint, Compose, privilege, and volume regression assertions in tests/test_container_security_contract.py
- [x] T020 [US3] Remove sudo and default credentials and make entrypoint configuration fail closed in docker/Dockerfile, docker/supervisord.conf, and docker/entrypoint.sh
- [x] T021 [US3] Narrow production volumes and add no-new-privileges, capability drops, read-only rootfs, tmpfs, and explicit writable paths in docker-compose.yml and docker-compose.minimal.yml
- [x] T022 [US3] Add a clearly labeled one-release migration layout in docker-compose.legacy.yml and document appliance upgrade/rollback in docs/security/container-hardening.md
- [x] T023 [US3] Update Docker smoke checks to prove runtime identity, secret posture, persistence, and restart behavior in scripts/docker-smoke-test.sh and .github/workflows/docker-build.yml

## Phase 6: User Story 4 - Preserve Other Provider Configuration

**Independent test**: Update Wright-owned keys in representative provider configurations and verify unknown entries survive; simulate a failed concurrent write and retain the prior complete file.

- [x] T024 [P] [US4] Add golden merge, unknown-entry, and interrupted-write tests in packages/agent_adapters/tests/test_provider_config_merge.py
- [x] T025 [US4] Implement atomic merge-only configuration writers and adopt them in packages/agent_adapters/src/agent_adapters/ and apps/api/src/api/services/wright_gateway_sync.py

## Phase 7: Polish and Cross-Cutting Verification

- [x] T026 Run focused SEC-03/SEC-04/CTR-01 suites and a seeded-value repository/runtime leak scan
- [x] T027 Update docs navigation, environment examples, threat model, migration/rollback, and implementation ledger in mkdocs.yml, docker/.env.example, docs/security/, and docs/gpt5-6-implementation-status.md
- [x] T028 Run `scripts/check-dev-merge.sh`, record exact results, mark Feature 043 review-ready, and stop before Feature 044

## Dependencies

- Setup (T001-T003) precedes foundational contracts (T004-T007).
- User Story 1 depends on all foundational tasks and establishes the credential boundary used by Stories 2 and 3.
- User Story 2 depends on User Story 1 provider writes/status but is independently testable from seeded legacy state.
- User Story 3 depends on required-secret semantics from User Story 1; its static contracts can run in parallel with Story 2.
- User Story 4 depends on atomic write/redaction primitives but not on container work.
- Cross-cutting verification requires all story phases complete.

## Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T008, T009, and T010 characterize independent API, Git, and MCP surfaces before implementation.
- T015 can be developed alongside T019 after the shared provider is stable.
- T024 can proceed alongside container implementation because it owns separate adapter files.

## Implementation Strategy

1. Land the shared provider, atomic transaction, and redaction foundation.
2. Complete User Story 1 as the security MVP: no secret disclosure across API, Git, MCP, or logs.
3. Add safe legacy migration and recovery.
4. Harden the default appliance and preserve a migration-only legacy layout.
5. Make provider configuration merge-only, then run leak scans and the full merge gate.
