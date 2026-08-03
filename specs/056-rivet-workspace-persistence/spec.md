# Feature Specification: Rivet Workspace Persistence

**Feature Branch**: `056-rivet-workspace-persistence`  
**Base**: `b38942f` (`054-rivet-workflow-integration`)  
**Prerequisite**: slice 055 conditional-go evidence  
**Status**: Planned; implementation requires human approval

## Scope

Create Rivet-independent, workspace-authoritative storage for authored workflow projects and dataset sidecars. The feature flag `rivet_workflows_enabled` defaults off; when off or when Rivet/Node is absent, all existing Wright behavior remains healthy and no editor/runtime is loaded.

In scope: canonical `workflows/<slug>/workflow.rivet-project` and dataset paths; stable IDs and revisions; optimistic concurrency; atomic writes; workspace/path/symlink/size validation; list/create/read/save/save-as/rename/delete/recover operations; additive metadata index; migration and rollback.

Excluded: Rivet editor bundle, UI tab, Node runner, graph execution, tool calls, approvals, or direct MCP.

## User Stories

### P1 — Workspace-owned workflow files

A workspace member can create, save, reopen, rename, delete, and recover a workflow and its dataset sidecars. The ordinary workspace files remain authoritative.

**Independent test**: create a workflow in two workspaces with the same slug, perform concurrent saves, and prove no content or metadata crosses the workspace boundary.

### P1 — Safe conflict and recovery behavior

An author with a stale revision receives a typed conflict and can reopen the current revision; a failed atomic write leaves either the old valid file or the complete new valid file, never a partial file.

### P2 — Clean absence and rollback

An operator can disable the feature or remove the optional Rivet dependencies without losing authored files. Additive metadata can be ignored or rebuilt from workspace files.

## Requirements

- FR-001: Workspace files MUST be the authoritative durable representation of projects and datasets.
- FR-002: Every operation MUST bind to the Wright workspace and reject traversal, symlink escape, malformed slug, unsupported project version, and oversized content.
- FR-003: Writes MUST stage, flush, and replace atomically with revision/ETag comparison.
- FR-004: Projects, datasets, revisions, delete/recovery state, and timestamps MUST be indexed additively without duplicating authoritative content.
- FR-005: Operations MUST preserve existing workspace files and support migration-safe index rebuild.
- FR-006: APIs MUST return typed unavailable, conflict, validation, and not-found outcomes without requiring Rivet or Node.
- FR-007: Feature-disabled behavior MUST leave normal Wright startup and workspace operations unchanged.
- FR-008: Audit-safe metadata MUST not include secrets, session authority, or executable runtime state.
- FR-009: Delete MUST be recoverable; no authored workflow is silently permanently removed.
- FR-010: The slice MUST record rollback, migration, cross-workspace, crash/restart, and supported-platform evidence.

## Success Criteria

- SC-001: 100 concurrent/stale-save trials never produce partial content or cross-workspace access.
- SC-002: 100 traversal and symlink-escape attempts are rejected before reads/writes.
- SC-003: A metadata index can be rebuilt from files without loss of project/dataset contents.
- SC-004: Disabled and missing-Rivet/Node test paths start and operate normally.
- SC-005: Recovery restores a deleted workflow with its last immutable revision and dataset sidecars.

## Edge Cases

Moved/deleted/read-only workspace; filesystem replace interruption; two processes save simultaneously; UTF-8/binary/malformed Rivet content; case-only rename on Windows; duplicate slugs; legacy/unindexed files; disk-full; unsupported version; symlink introduced after validation.

## Rollback

Disable the flag and stop exposing the workflow API. Preserve all `workflows/` files; retain or rebuild additive metadata on re-enable. No delete migration is permitted.
