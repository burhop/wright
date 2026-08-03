# Implementation Plan: Rivet Workspace Persistence

**Branch**: `056-rivet-workspace-persistence`  
**Base**: `b38942f`  
**Status**: Awaiting human approval; no tasks or implementation yet

## Technical approach

Add neutral workflow value types under `packages/core`, a workspace-scoped storage service and filesystem/index ports under `packages/workspace_service`, additive index storage through `packages/data_vault`, and thin authenticated API endpoints in `apps/api`. No editor, Node package, browser code, or workspace tab is included.

The service resolves a server-owned workspace root, maps opaque workflow ID to a validated slug, validates project/dataset limits and format versions, and uses same-directory staged writes followed by replacement. The index tracks metadata only and can be rebuilt from canonical files. Recovery moves the complete workflow directory to workspace-local `.deleted` storage.

## Constitution gate

Pass: typed modular ownership; offline-first (no new optional dependency); embedded file/SQLite storage; server-derived workspace identity; additive migrations; structured audit metadata. No exception requested.

## Source ownership

```text
packages/core/src/core/workflows/              neutral IDs, revisions, errors
packages/workspace_service/src/workspace_service/workflows/  commands, storage port, validation
packages/workspace_service/src/workspace_service/adapters/   confined atomic filesystem adapter
packages/data_vault/src/data_vault/            workflow metadata repository/migration
apps/api/src/api/routers/workflows.py           authenticated thin routes
tests/{contract,integration,security}/rivet/    slice evidence
```

## Verification

- Ruff, mypy, unit and contract tests for values, revision logic, malformed/oversized/version paths.
- Filesystem integration tests for cross-workspace isolation, traversal/symlink/race protection, atomic failure/restart, case-only rename, recovery and index rebuild.
- API schema snapshot and authentication/feature-disabled tests.
- Migration/rollback and no-Rivet/no-Node startup tests on Windows plus documented Linux/macOS behavior; this slice makes no native/Docker compatibility claim beyond its existing filesystem abstractions.

## Migration, packaging, rollback

Add one rebuildable metadata table/index only. Existing workspaces need no conversion; legacy files are discovered by rebuild. No Rivet asset or runtime is packaged. Disable routes via flag and retain files/index; re-enable/rebuild to roll forward.

## Risks and controls

Atomic replace and directory fsync semantics vary by platform: hide them behind a tested adapter and record limitations. Symlink races require descriptor/no-follow protections where available plus post-resolution containment. The conditional offline editor finding remains a later editor-package blocker, not a reason to loosen storage guarantees.

## Approval gate

Human approval is required before generating `tasks.md`, running Spec Kit analysis, or changing production code.
