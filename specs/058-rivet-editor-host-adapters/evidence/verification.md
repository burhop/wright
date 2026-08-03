# Slice 058 verification evidence

**Branch:** `058-rivet-editor-host-adapters`
**Umbrella base:** `1ce50ee`
**Recorded:** 2026-08-03

## Passing checks

- Editor asset/grant contract and feature-gate tests: `10 passed` (one existing
  FastAPI/TestClient deprecation warning).
- Broader regression: workspace-service tests plus workspace API tests:
  `241 passed, 5 skipped`.
- Ruff and focused mypy pass for the new editor/core modules and changed API
  files.

## Requirement traceability

| Requirement | Evidence |
|---|---|
| Isolated local asset boundary | `EditorAssetCatalog` accepts only a local manifest and checksum-verified entrypoint |
| No runtime download/source checkout | catalog has no network client or fallback; missing manifest returns typed state |
| Workspace/session/revision scope | grant contract tests reject another workspace, stale revision, and expiry |
| Authoritative persistence | adapter delegates solely to `WorkspaceWorkflowUseCases` |
| Feature-disabled health | API feature-gate test rejects before workspace resolution |
| Missing/tampered asset safety | catalog tests return `missing` or `incompatible` |

## Limits, rollback, and follow-up

- The manifest deliberately declares Rivet 1.25.0 as **not installed**. Slice
  055's Windows offline upstream cache issue is still unresolved, so no real
  upstream editor is shipped, served, or represented as available.
- This slice supplies the adapter contract, not the retained `LiveAppSurface`
  tab. Slice 059 must consume it without importing Rivet into Wright's React
  tree.
- Roll back by setting `WRIGHT_RIVET_EDITOR_ENABLED=0`; existing ephemeral
  grants become unusable after process restart and workspace files are intact.
- A whole-repository mypy run remains pre-existing-red for unrelated modules
  and missing third-party stubs; focused changed-module checks pass.

## Cross-artifact analysis

The spec, plan, research, data model, contract, quickstart, tasks, and four
checklists agree on one conditional fact: an adapter can be implemented now,
but an installed production Rivet editor must remain unavailable until offline
package evidence is supplied. No later tab, runner, gateway, or catalog work is
required for this boundary to function correctly.
