# Feature Specification: Rivet Editor Host Adapters

**Branch**: `058-rivet-editor-host-adapters`
**Base**: `1ce50ee`
**Prerequisites**: 055 compatibility spike; 056 workspace persistence

## Outcome

Provide a pinned Rivet editor distribution that Wright can host as an isolated
workspace surface. It reads and writes persisted workflows and datasets through
authenticated Wright adapters, never browser-profile storage or direct native
file APIs.

## User stories

### US1 — Open a workspace-bound editor (P1)

An engineer opens a selected workflow. Wright returns only a selected
workspace/workflow/revision capability; different-workspace or expired-session
bootstraps are rejected.

### US2 — Save authored content through Wright (P1)

The isolated editor loads/saves workflows and datasets using narrow Wright
adapters. A stale revision conflicts without overwriting the authoritative file.

### US3 — Operate safely when unavailable (P2)

Disabled, missing, or incompatible editor assets leave normal Wright workspaces
healthy and return a typed diagnostic.

## Functional requirements

- FR-001: Serve one exact checksum-verified local editor manifest from an
  isolated surface origin; no Rivet React module enters Wright's React tree.
- FR-002: Bind each bootstrap/request to server-derived workspace, session,
  workflow, and revision identity.
- FR-003: Provide constrained read/save/list and dataset operations through
  slice-056 workspace-authoritative persistence.
- FR-004: Reject IndexedDB, browser-picked files, direct native/debugger/tool/
  MCP APIs, secrets, and arbitrary network use as authoritative paths.
- FR-005: Return typed disabled/missing/incompatible/expired/conflict states.
- FR-006: Pin source version, patch metadata, licenses, and checksums; runtime
  requires no source checkout or network.
- FR-007: Never expose cross-workspace data, paths, session identity, or creds.

## Success criteria

- SC-001: Open/save/reopen with exact revisions is automated.
- SC-002: 100 cross-workspace/expired-session bootstrap attempts are rejected.
- SC-003: Supported browser journey observes no external network or client
  authoritative persistence.
- SC-004: Unavailable states preserve normal startup and show a diagnostic.
- SC-005: Installed local asset manifest/version/license/checksum verifies.

## Exclusions

The Workflows tab/retained lifecycle is slice 059. Graph execution, debugger,
gateway nodes, and workflow operations are separate slices. The known Windows
offline upstream cache gap prohibits claiming a production editor bundle.
