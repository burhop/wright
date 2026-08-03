# Tasks: Rivet Workspace Persistence

## Phase 1 — Foundations

- [X] T001 Create typed workflow IDs, revisions, summaries, documents, and typed errors in `packages/core/src/core/workflows/`.
- [X] T002 Add a workspace-confined workflow path/slug validator and size/version policy.
- [X] T003 Add atomic staged-write, fsync/replace, digest, and recovery primitives without following links.
- [X] T004 Add unit tests for values, slug/path validation, limits, and error mapping.

## Phase 2 — Storage and Index

- [X] T005 Implement workspace project/dataset create/read/save/rename/delete/recover operations in `workspace_service`.
- [X] T006 Implement a rebuildable metadata index repository and additive migration in `data_vault`.
- [X] T007 Wire index updates transactionally around successful filesystem operations and rebuild from files.
- [X] T008 Add concurrent save, crash/atomicity, recovery, index rebuild, moved/read-only workspace, and cross-workspace integration tests (Windows symlink creation unavailable; limitation recorded for native hardening).

## Phase 3 — API and Absence

- [X] T009 Add authenticated thin workflow persistence schemas and routes in `apps/api`.
- [X] T010 Add default-off feature configuration and typed feature-disabled responses without Rivet/Node imports.
- [X] T011 Add API contract, auth, stale ETag, malformed/oversized, traversal/symlink, and disabled/missing-dependency tests (direct disabled endpoint and focused persistence coverage; symlink-host limitation recorded).

## Phase 4 — Evidence and Completion

- [X] T012 Run format, lint, type, unit, contract, integration, security, migration, rollback, and Windows filesystem checks.
- [X] T013 Record traceability, platform limitations, migration/index rebuild, disabled behavior, recovery/rollback evidence.
- [ ] T014 Review scope, commit, and locally merge only after all checks pass.

## Dependency order

T001–T004 → T005–T008 → T009–T011 → T012–T014. No editor, Node runtime, tab, or gateway code is permitted.
