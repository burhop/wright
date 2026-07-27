# Implementation Plan: Package Boundaries and Workspace Use Cases

**Branch**: `codex/045-package-boundary-and-workspace-use-cases` | **Date**: 2026-07-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/045-package-boundary-and-workspace-use-cases/spec.md`

## Summary

Enforce the roadmap's one-way package graph with a machine-readable ownership manifest and an AST fitness test that detects static, local, relative, and dynamic imports. Split the current `core.workspace` and monolithic workspace facade into domain contracts, application use cases, and concrete adapters owned by `workspace_service`/`data_vault`; inject them through an API composition root and reduce workspace routes to transport translation. Preserve every HTTP/state/workspace contract, keep temporary delegators only for proven live callers, and put blocking host work behind a bounded async executor.

## Technical Context

**Language/Version**: Python 3.11-3.13; TOML, Markdown, and YAML for policy and documentation

**Primary Dependencies**: Standard-library protocols, dataclasses, AST, pathlib, sqlite3, subprocess, asyncio; existing FastAPI/Pydantic, `core`, `data_vault`, `agent_adapters`, `tool_registry`, and `workspace_service`

**Storage**: Existing Feature 044 SQLite schema and existing workspace filesystem layout; no schema or file-format change

**Testing**: pytest unit/contract/integration tests, synthetic AST boundary fixtures, route composition tests, Ruff, mypy evidence, package builds, full dev merge gate

**Target Platform**: Windows and Linux local development, air-gapped Linux OCI appliance, Docker Desktop Linux containers

**Project Type**: Modular Python monorepo and FastAPI web appliance

**Performance Goals**: Bounded host operations default to 30 seconds with operation-specific overrides; ordinary metadata/file operations preserve current response performance; timeout tests complete within twice their configured deadline

**Constraints**: Offline-first; existing HTTP/state/file compatibility; no migration; no secret regression; explicit workspace/session identity; no concrete provider selected in use cases; no lifecycle/catalog/frontend/release scope expansion

**Scale/Scope**: Six owned Python surfaces, approximately 2,400 lines of current workspace runtime behavior, 40+ workspace route/use-case operations, all production Python imports, and one-release compatibility seams only where live callers remain

## Constitution Check

*GATE: Pass before Phase 0 research; re-checked after Phase 1 design.*

- **Modular Monorepo Boundaries**: Pass and directly advanced. The plan establishes enforced ownership and translation-only routes. The constitution's wording that routes go directly to agent/tool packages is interpreted through the approved later roadmap: routes call `workspace_service`, which coordinates those packages without reverse dependencies.
- **Offline-First Mandate**: Pass. All adapters remain local and no network dependency is introduced.
- **Container Strategy**: Pass. No base-image or MCP host-software change is required.
- **Agent Abstraction**: Pass. Agent context is represented by a provider-neutral port; concrete Hermes/OpenClaw materializers are selected only in composition.
- **Zero-Server Databases**: Pass. Existing SQLite remains the only relational store and is accessed through `data_vault`-owned repositories.
- **Security & Identity**: Pass. Feature 042 authentication/confinement, Feature 043 secret handling, and immutable session identity remain mandatory invariants.
- **Engineering Tooling Protocol**: Pass. No MCP server behavior or host dependency changes.
- **UI & Testing**: Pass. Public API contracts remain stable and receive route plus direct-use-case tests; frontend behavior is unchanged.
- **Observability & Tracing**: Pass with scoped deferral. Existing structured logging and tracing hooks remain; Feature 051 owns full provider/exporter work.
- **Branch Discipline and Manual Gating**: Pass. Work is isolated on Feature 045 and will run the authoritative merge gate before review.

## Project Structure

### Documentation (this feature)

```text
specs/045-package-boundary-and-workspace-use-cases/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── package-boundary-contract.md
│   └── workspace-application-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md

docs/architecture/package-boundaries.md
```

### Source Code (repository root)

```text
architecture/
└── python-packages.toml              # authoritative ownership/edge policy

packages/core/src/core/
├── identifiers.py                    # domain identifiers/value objects
├── errors.py                         # shared error taxonomy
├── ports.py                          # side-effect-neutral protocol vocabulary
├── redaction.py
└── telemetry.py                      # contracts/context only

packages/data_vault/src/data_vault/
├── workspace_repository.py           # workspace/session/context/settings queries
└── secret_provider.py                # local secret-provider implementations

packages/workspace_service/src/workspace_service/
├── models.py                         # application commands/results
├── errors.py                         # typed application failures
├── ports.py                          # workspace-specific required capabilities
├── executor.py                       # bounded async blocking-work adapter
├── use_cases/
│   ├── lifecycle.py                  # CRUD, activation, sessions
│   ├── files.py                      # files, backups, preview/download, execution
│   ├── git.py                        # status/diff/revert/commit/sync/branch/merge
│   ├── context.py                    # context/settings/agent materialization
│   └── tools.py                      # workspace tool selection/status orchestration
├── adapters/
│   ├── filesystem.py                 # confined file/backups implementation
│   ├── git.py                        # credential-safe Git implementation
│   ├── process.py                    # bounded subprocess implementation
│   └── legacy.py                     # narrowly documented compatibility delegates
├── composition.py                    # default production service construction
└── service.py                        # thin public facade over use cases

apps/api/src/api/
├── composition.py                    # application adapter wiring
├── notifications.py                  # transport-independent notification publisher
└── routers/workspace.py              # HTTP translation only

tests/
└── test_import_boundaries.py         # manifest/source/metadata fitness checks
```

**Structure Decision**: Keep one `workspace_service` public facade for API compatibility while decomposing its implementation into command-oriented use cases and injected ports. Move state queries to `data_vault`, host behavior to workspace adapters, and domain-only vocabulary to `core`. The API constructs the graph once and routes never instantiate infrastructure. This is one service graph, not a parallel rewrite.

## Implementation Sequence

1. Add the policy manifest and AST/metadata fitness harness with seeded negative fixtures; initially allow only enumerated temporary violations.
2. Introduce core identifiers/errors/contracts and workspace application ports/results without changing callers.
3. Move workspace/session/context/settings SQL into a data-vault repository and preserve exact row/result semantics.
4. Move path/file/backup/Git/process behavior from `core.workspace` and the router into workspace adapters; retain confinement and secret-provider guarantees.
5. Add bounded execution and direct lifecycle/file/Git/context/tool use cases; make the facade delegate only.
6. Wire concrete implementations in the API composition root and translate every workspace route through the facade.
7. Remove route-to-route notification imports via an injected publisher; document post-commit best-effort notification semantics.
8. Search all callers, migrate supported imports, delete unused global activation/reverse-import paths, and drive the temporary violation set to empty.
9. Verify response compatibility, concurrency isolation, timeouts/cancellation, package builds, docs, and the complete dev merge gate.

## Migration and Rollback

- **Upgrade**: Code-only ownership migration. Existing SQLite and workspace files are opened unchanged through new repositories/adapters.
- **Existing data**: No row or file conversion. Feature 044 schema/version checks still run before use cases are constructed.
- **Compatibility**: Public HTTP paths and shapes stay stable. A facade or function shim is retained only for a repository-confirmed live caller and delegates to the same use case.
- **Failure**: Composition fails closed if required adapters cannot be constructed. Typed use-case errors map to existing HTTP status categories; secrets and raw commands remain redacted.
- **Rollback**: Stop the upgraded process and run the prior image/commit against the same compatible state. Use the existing `wright-db backup/restore` process for ordinary deployment rollback protection; no reverse migration exists or is needed.
- **Removal**: Compatibility shims include an explicit one-release removal note and are guarded against new callers by fitness tests.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/package-boundary-contract.md](contracts/package-boundary-contract.md), [contracts/workspace-application-contract.md](contracts/workspace-application-contract.md), and [quickstart.md](quickstart.md).

## Constitution Check - Post-Design

All pre-design gates remain passing. The design explicitly preserves local-only operation, SQLite state, agent abstraction, current security controls, and transport compatibility. It removes rather than introduces architecture exceptions. Full observability provider wiring and the constitution's separate governance amendment remain assigned to later roadmap features and are not falsely claimed here.

## Complexity Tracking

No constitution violations requiring an implementation exception are introduced.
