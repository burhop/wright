# Implementation Plan: State Migrations and Recovery

**Branch**: `codex/044-state-migrations-and-recovery` | **Date**: 2026-07-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/044-state-migrations-and-recovery/spec.md`

## Summary

Replace API-owned boot mutation with a data-vault-owned, numbered and checksummed migration service. Each migration and its ledger entry commit in one transaction; pre/post integrity checks, a stable lifecycle lock, consistent snapshots, versioned manifests, and atomic restore protect state. The API keeps a one-release `run_migrations()` compatibility wrapper, then performs catalog reconciliation separately. An internal operator CLI exposes `db status`, `backup`, `upgrade`, and `restore` without adding private dependencies to the public `wright-engineering` distribution.

## Technical Context

**Language/Version**: Python 3.11-3.13; Markdown for operator documentation

**Primary Dependencies**: Standard-library `sqlite3`, `hashlib`, `json`, `argparse`, and filesystem primitives; existing `data_vault`, FastAPI lifespan, and tool-registry catalog

**Storage**: One local SQLite state database in WAL mode; snapshot database and JSON manifest files beside or under an operator-selected backup directory

**Testing**: pytest migration fixtures/failure injection, CLI subprocess tests, API lifespan tests, Ruff, package build checks, full dev merge gate

**Target Platform**: Windows and Linux local development, air-gapped Linux OCI appliance, Docker Desktop Linux containers

**Project Type**: Modular monorepo web appliance with internal Python packages and a local operator CLI

**Performance Goals**: Status completes within two seconds for a healthy local database; backup/restore supports a 1 GiB database within five minutes on supported development hardware

**Constraints**: Offline-only operation; no external migration service; fail closed before runtime construction; no row contents or credentials in output; one-release API wrapper; no reverse migrations

**Scale/Scope**: Current Wright schema (MCP catalog/tools, workspaces/sessions, contexts/messages, settings), the unversioned Feature 043 baseline and representative partial historical shapes, four lifecycle commands

## Constitution Check

*GATE: Pass before Phase 0 research; re-checked after Phase 1 design.*

- **Modular Monorepo Boundaries**: Pass. Schema, connection, ledger, backup, and restore ownership moves into `data_vault`; the API wrapper only delegates and catalog code remains in `tool_registry`.
- **Offline-First Mandate**: Pass. All lifecycle work uses local SQLite and files.
- **Container Strategy**: Pass. State remains in the documented Wright data volume; no image/tool expansion is needed.
- **Agent Abstraction**: Pass. No agent-provider behavior changes.
- **Zero-Server Databases**: Pass. SQLite remains the only relational store.
- **Security & Identity**: Pass. Existing admin/control-plane protection remains; lifecycle CLI is local and never prints row values.
- **Engineering Tooling Protocol**: Pass. No MCP host software is introduced.
- **UI & Testing**: Pass. No UI contract changes; startup and CLI behavior receive executable fixtures.
- **Observability & Tracing**: Pass with scoped exception. Lifecycle diagnostics are structured result objects/JSON; Feature 051 owns full telemetry wiring.
- **Branch Discipline and Manual Gating**: Pass. Work is isolated on Feature 044 and will stop at review after the authoritative dev gate.

## Project Structure

### Documentation (this feature)

```text
specs/044-state-migrations-and-recovery/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── database-lifecycle-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
packages/data_vault/src/data_vault/
├── state_store.py           # SQLite connection policy
├── migrations.py            # immutable definitions, runner, status, ledger repository
├── backup.py                # snapshot/manifest validation and atomic restore
├── lifecycle_lock.py        # cross-platform operation serialization
└── cli.py                   # db status/backup/upgrade/restore

apps/api/src/api/database/
└── migrate.py               # one-release delegation wrapper plus catalog reconciliation call site

packages/data_vault/tests/
├── fixtures/                # fresh/current/partial/future/corrupt state builders
├── test_migrations.py
├── test_backup_restore.py
└── test_cli.py

apps/api/tests/
├── test_database_startup.py
└── test_mcp_catalog_seed.py  # catalog reconciliation remains behaviorally compatible

docs/operations/database-recovery.md
```

**Structure Decision**: `data_vault` becomes the single owner of state lifecycle mechanics and exposes typed results used by its internal CLI and the API composition root. Existing domain SQL callers remain compatibility consumers until Feature 045 moves use cases and enforces the full package graph; they do not own or mutate schema after this feature.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/database-lifecycle-contract.md](contracts/database-lifecycle-contract.md), and [quickstart.md](quickstart.md).

## Constitution Check - Post-Design

All gates remain passing. The design adds no server, network dependency, public package dependency, agent coupling, reverse migration, or startup best-effort mode. Catalog reconciliation is explicitly outside migration transactions, and restore activation is atomic only after manifest and database verification.

## Complexity Tracking

No constitution violations identified.
