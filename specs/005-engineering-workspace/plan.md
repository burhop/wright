# Implementation Plan: Engineering Workspace

**Branch**: `005-engineering-workspace` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-engineering-workspace/spec.md`

## Summary

Implement the "Engineering Workspace" feature, providing an isolated local directory for each chat session that is automatically initialized as a local Git repository. Integrate a file tree explorer modeled after VS Code inside the Workspace Panel. Enable workspace file operations (create file/folder, rename, move, delete) and direct final agent MCP tool outputs there (while saving temporary solver files in `/tmp`). Add full local version control functionality (revert, diff, local commit, history timeline) and remote sync actions (push/pull with remote authentication options).

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 6.0 (frontend)

**Primary Dependencies**: FastAPI >=0.115, Pydantic v2, three >=0.170.0 (frontend), Git CLI (system path)

**Storage**: SQLite with WAL mode for workspace credentials and local paths. Git repository database (.git) inside each session directory.

**Testing**: pytest (backend API/subprocesses), Vitest (frontend components), Playwright (E2E file selection and tree updates)

**Target Platform**: Linux local host (offline-first execution)

**Project Type**: Web application (modular monorepo)

**Performance Goals**: Workspace tree rendering <150ms. File actions <100ms. Local Git commits <500ms.

**Constraints**: Bounded to standard Git operations. Graceful local fallback if offline or git remote is not configured. High-security token usage for push/pull.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | FastAPI backend, zero business logic in routes | ✅ Pass | All workspace CRUD and Git CLI logic is isolated inside `WorkspaceManager` class in `packages/core/src/core/workspace.py`. |
| 2 | Modular Monorepo with strict boundaries | ✅ Pass | UI and workspace configurations in `apps/web/`, endpoints in `apps/api/`, files and Git logic in `packages/core/`. |
| 3 | Offline-first mandate | ✅ Pass | Local Git initialized inside workspace by default on local GB10 host. No external API calls are executed unless user configures remote push/pull. |
| 4 | Agent Abstraction (Adapter Pattern) | ✅ Pass | MCP executors interact with the workspace using general file system commands. No model-specific code is introduced. |
| 5 | Zero-server databases | ✅ Pass | All workspace records stored in existing SQLite database. No standalone database servers required. |
| 6 | Local authentication | ✅ Pass | Options credentials and tokens are checked against local session ID parameters. |
| 7 | Template Method for tools | ✅ Pass | Tool execution targets workspace folders based on session parameters. |
| 8 | Atomic design (Tokens → Primitives → Components) | ✅ Pass | VS Code styled tree elements, badges, and diff containers styled via design tokens. |
| 9 | Tier 1/2/3 testing pyramid | ✅ Pass | Pytest API unit tests, Vitest tree checks, Playwright file CRUD checks. |
| 10 | OpenTelemetry tracing + structured JSON logging | ✅ Pass | Every workspace operation and git subprocess execution logs trace spans with the active `trace_id`. |
| 11 | Phase isolation + branch discipline | ✅ Pass | Current feature branch `005-engineering-workspace` is active. Spec completed and checklists validated. |

## Project Structure

### Documentation (this feature)

```text
specs/005-engineering-workspace/
├── plan.md              # This file
├── research.md          # Git subprocess decisions and status mapping
├── data-model.md        # SQLite schema and WorkspaceNode model
├── quickstart.md        # Setup guide for local run and test
└── contracts/
    └── api-contracts.md # API endpoints routes design
```

### Source Code (repository root)

```text
packages/core/
└── src/core/
    └── workspace.py           # [MODIFY] Add CRUD, git init, status, diff, commit, and sync helpers

apps/api/
├── src/api/
│   ├── main.py                # Mount workspace router changes
│   ├── database/
│   │   └── migrate.py         # [MODIFY] Migration scripts to create engineering_workspaces SQLite table
│   └── routers/
│       └── workspace.py       # [MODIFY] Implement file CRUD and Git status/diff/revert/commit/sync routes
└── tests/
    └── test_workspace_api.py  # [MODIFY] Extend tests to assert CRUD, git status porcelain, and traversal protection

apps/web/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   └── WorkspacePanel.tsx # [MODIFY] Add sidebar panel tabs: FILES, VERSION CONTROL, OPTIONS
│   │   └── common/
│   │       ├── FileTree.tsx       # [MODIFY] Add status badges (U, M), rename/create input box, context menu
│   │       └── DiffViewer.tsx     # [NEW] View side-by-side or inline code diffs
│   └── services/
│       └── workspace-service.ts   # [MODIFY] Add client side API calls for CRUD and Git integration
```

**Structure Decision**: Exposes file actions and git processes inside `packages/core/src/core/workspace.py` keeping the business logic out of API routes. Exposes API endpoints under `apps/api/src/api/routers/workspace.py`. Implements VS Code Explorer visual styles in `WorkspacePanel.tsx` and custom context menus inside the tree node components.

## Complexity Tracking

No constitution violations. Complexity is tracked cleanly under modular monorepo packages.
