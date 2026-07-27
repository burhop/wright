# Feature Specification: State Migrations and Recovery

**Feature Branch**: `codex/044-state-migrations-and-recovery`

**Created**: 2026-07-10

**Status**: Draft

**Input**: User description: "Implement roadmap item R1.5: numbered transactional migrations and repositories, remove schema and catalog mutation from boot, fail readiness closed, cover fresh and supported prior databases, and provide status, backup, upgrade, and restore operations."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upgrade State Without Corruption (Priority: P1)

As an operator upgrading Wright, I can move an existing supported database to the current schema without losing user state or serving against a partially upgraded database.

**Why this priority**: An interrupted or ambiguous upgrade can corrupt local engineering state and blocks a trustworthy release.

**Independent Test**: Start from each supported prior-state fixture, perform the upgrade, and prove that user records survive, every migration is recorded exactly once, and a simulated interruption leaves the database at its last complete version.

**Acceptance Scenarios**:

1. **Given** a fresh installation, **When** state is initialized, **Then** all numbered changes are applied in order and the database reports the current version.
2. **Given** the unversioned database shape shipped immediately before this feature, **When** upgrade runs, **Then** it is safely adopted as the legacy baseline and upgraded without deleting user-created catalog or workspace state.
3. **Given** an interruption during a change, **When** the operation fails, **Then** that change and its ledger entry are both rolled back and readiness remains closed.
4. **Given** a previously applied change whose recorded checksum differs from the installed definition, **When** status or upgrade runs, **Then** the operation fails with a non-secret diagnostic and makes no mutation.

---

### User Story 2 - Inspect and Operate Database Lifecycle (Priority: P2)

As an operator, I can inspect state, create a verified backup, run an explicit upgrade, and restore a compatible backup through documented commands.

**Why this priority**: Operators need deterministic recovery actions that do not depend on editing files or invoking application internals.

**Independent Test**: Exercise status, backup, upgrade, and restore from a command shell and verify stable exit behavior, machine-readable status, restricted backup files, and restored application data.

**Acceptance Scenarios**:

1. **Given** any database path, **When** status runs, **Then** it reports existence, integrity, current/target version, pending changes, and readiness without changing the database.
2. **Given** an intact database, **When** backup runs, **Then** it produces a consistent snapshot plus an integrity and schema manifest without exposing credentials.
3. **Given** a compatible verified backup, **When** restore runs, **Then** the current database is preserved for rollback and the restored copy is integrity-checked before activation.
4. **Given** a corrupt, incomplete, incompatible, or tampered backup, **When** restore runs, **Then** it refuses activation and leaves the current database unchanged.

---

### User Story 3 - Start Only on Verified State (Priority: P3)

As a Wright user, I never receive a ready application backed by corrupt, newer-than-supported, or partially migrated state.

**Why this priority**: Fail-closed readiness prevents subtle data loss and cross-feature failures after an unsuccessful upgrade.

**Independent Test**: Start the application against current, prior, corrupt, interrupted, and newer-version fixtures and verify that only a fully upgraded, integrity-checked database reaches readiness.

**Acceptance Scenarios**:

1. **Given** a supported prior database, **When** the application starts, **Then** the compatibility entrypoint invokes the migration service and readiness opens only after successful verification.
2. **Given** corruption, an unknown future version, a checksum mismatch, or migration failure, **When** the application starts, **Then** startup fails before repositories or runtime services begin serving.
3. **Given** a current database, **When** the application restarts repeatedly, **Then** migration is idempotent and catalog reconciliation occurs outside the schema transaction.

### Edge Cases

- The database path does not exist, its parent is read-only, or the backup destination cannot be created.
- SQLite reports a busy/locked database while an operator operation is requested.
- A legacy database contains only a subset of historical tables or columns.
- A migration definition is missing, duplicated, reordered, or has changed after being recorded.
- The database reports failed integrity or foreign-key checks before or after migration.
- A backup manifest is missing, malformed, refers to another database identity, or its digest does not match the snapshot.
- Restore is interrupted before or after verification but before atomic activation.
- The installed software is older than the database schema.
- A legacy plaintext credential backup from Feature 043 coexists with the state backup workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST maintain an ordered, durable ledger of applied schema and data changes using immutable identifiers and checksums.
- **FR-002**: Each change MUST apply transactionally with its ledger record so an interruption cannot expose a partially applied change as complete.
- **FR-003**: The migration service MUST validate ordering, uniqueness, continuity, and recorded checksums before applying changes.
- **FR-004**: Wright MUST support both fresh initialization and adoption of the unversioned database state shipped immediately before Feature 044, including representative historical partial schemas.
- **FR-005**: Upgrade MUST preserve user-created workspaces, sessions, messages, settings, MCP servers, tool state, and credential-migration markers unless a documented change explicitly transforms them.
- **FR-006**: Schema migration MUST NOT perform catalog seeding, runtime reconciliation, test-data cleanup, or unrelated application behavior.
- **FR-007**: State persistence and migration ownership MUST reside in the data-vault boundary; the API compatibility entrypoint MAY delegate to it for one release.
- **FR-008**: Startup and readiness MUST fail closed before application repositories and runtimes serve when preflight, migration, checksum, version, integrity, or postflight validation fails.
- **FR-009**: Preflight and postflight validation MUST include database integrity and foreign-key consistency checks.
- **FR-010**: Operators MUST have explicit status, backup, upgrade, and restore commands with stable nonzero failure behavior and a machine-readable output option.
- **FR-011**: Status MUST be read-only and report database existence, integrity, detected/current/target version, pending changes, compatibility, and readiness without secret values.
- **FR-012**: Backup MUST create a consistent snapshot plus a restricted manifest containing schema version, applied checksums, database digest, integrity results, creation metadata, and product compatibility metadata.
- **FR-013**: Restore MUST validate the manifest, digest, integrity, foreign keys, and supported schema range before atomically activating a snapshot.
- **FR-014**: Restore MUST preserve the displaced database as a recoverable rollback copy and MUST leave the active database unchanged on any pre-activation failure.
- **FR-015**: Downgrade MUST occur only by restoring a verified pre-upgrade backup compatible with the older release; reverse schema mutations are not required.
- **FR-016**: Database mutation operations MUST use an exclusive lifecycle lock or equivalent serialization and provide a bounded, actionable failure when state is busy.
- **FR-017**: Logs, command output, manifests, and errors MUST avoid database row contents and credential values.
- **FR-018**: Documentation MUST define supported source states, automatic-startup behavior, explicit operations, failure recovery, backup retention, and rollback.
- **FR-019**: Automated evidence MUST cover fresh state, each supported prior fixture, repeated execution, interruption, corruption, checksum mismatch, future-version refusal, backup/restore, downgrade-by-restore, and startup fail-closed behavior.

### Key Entities

- **Migration Definition**: An immutable ordered change identified by version, name, checksum, and transactional apply behavior.
- **Migration Ledger Entry**: Durable evidence that one exact migration definition completed, including version, checksum, and application metadata.
- **Database Status**: A read-only assessment of integrity, compatibility, current and target versions, pending changes, and readiness.
- **State Backup**: A consistent database snapshot paired with a restricted verification manifest.
- **Backup Manifest**: Versioned metadata used to authenticate the snapshot contents and decide whether restore is safe.
- **Lifecycle Lock**: The serialization boundary preventing concurrent upgrade, backup activation, or restore operations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Fresh initialization and every supported prior-state fixture reach the current state with 100% of seeded user records preserved.
- **SC-002**: Every simulated interruption leaves zero partially applied changes or unmatched ledger entries across at least one failure point per migration.
- **SC-003**: Corrupt, tampered, future-version, and checksum-mismatched state is rejected in 100% of automated startup and operator scenarios.
- **SC-004**: A verified backup can be restored and returned to ready service in under five minutes for a one-gigabyte local database on supported development hardware.
- **SC-005**: Repeating status, backup validation, and upgrade against current state produces no schema or user-data changes in 100 consecutive runs.
- **SC-006**: Operator output and generated manifests contain zero seeded credential values in automated leak checks.

## Assumptions

- The supported prior-release baseline is the unversioned schema present at commit `49bf248`, plus representative partial variants already tolerated by the legacy boot routine.
- SQLite remains the single embedded state database; migration of LanceDB or workspace artifacts is outside this feature unless required to keep state references valid.
- Catalog contents continue to be reconciled at application startup through a separate idempotent service after database readiness, not by schema migrations.
- Backups are local operator-managed artifacts; automated retention scheduling and remote backup services are outside this feature.
- Reverse migrations are intentionally excluded; rollback uses the verified pre-upgrade snapshot.
- Feature 043 credential backups remain a separate recovery artifact and are never embedded in normal command output.
