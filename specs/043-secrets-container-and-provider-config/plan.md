# Implementation Plan: Secrets, Container, and Provider Configuration

**Branch**: `codex/043-secrets-container-and-provider-config` | **Date**: 2026-07-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/043-secrets-container-and-provider-config/spec.md`

## Summary

Close SEC-03, SEC-04, and CTR-01 by introducing one provider-neutral credential boundary for API, Git, MCP, and integration secrets; migrating plaintext settings with backup-first fail-closed behavior; using atomic fallback storage and Git askpass; redacting logs and protocol diagnostics; and running the appliance without default credentials, sudo, excess capabilities, or broad system-volume persistence.

## Technical Context

**Language/Version**: Python 3.12/3.13; Bash/YAML/Dockerfile for appliance configuration; Markdown for operator guidance.

**Primary Dependencies**: Existing FastAPI/Pydantic API, `core`, `tool_registry`, SQLite settings, structured logging, Docker Compose, and standard-library filesystem/process primitives. No network-only secret service is introduced.

**Storage**: Provider environment or mounted secret files first; owner-only atomic JSON fallback for air-gapped hosts; SQLite contains non-secret status/configuration only; restricted migration backups.

**Testing**: pytest unit/integration/concurrency/leak tests, API contracts, process-argument characterization, Dockerfile/Compose static contracts, Docker smoke where available, Ruff, frontend/doc gates, and `scripts/check-dev-merge.sh`.

**Target Platform**: Local Windows and Linux development; Linux OCI appliance; air-gapped installations; Docker Desktop Linux containers.

**Project Type**: Modular monorepo web appliance with shared Python packages, HTTP API, local subprocess integrations, and OCI deployment.

**Performance Goals**: 100 concurrent fallback-store updates without lost writes; normal credential status reads complete within existing API expectations; redaction remains linear in logged payload size.

**Constraints**: Secrets never cross normal read APIs; no credentials in argv/URLs/logs; configuration writes are atomic and merge-only; migration is backup-first and fail-closed; container remains non-root and offline-capable; no publication or Feature 044 migration framework work.

**Scale/Scope**: Global provider keys, per-workspace Git credentials, per-server MCP credentials, Wright/Hermes integration auth, production Dockerfile/supervisor/entrypoint, two current Compose files, one temporary legacy Compose migration path, and associated docs/tests.

## Constitution Check

*GATE: Pass before Phase 0 research; re-checked after Phase 1 design.*

- **Modular Monorepo Boundaries**: Pass. Shared provider/redaction contracts live in `core`; API routes delegate; `tool_registry` consumes the shared boundary.
- **Offline-First Mandate**: Pass. Environment, mounted-file, and local atomic fallback providers require no network.
- **Container Strategy**: Pass with security refinement. The thick appliance remains; only privilege, credential, and persistence posture changes.
- **Agent Abstraction**: Pass. Credential references are provider-neutral and do not hardcode Hermes.
- **Zero-Server Databases**: Pass. No new database or daemon is introduced.
- **Security & Identity**: Pass. Feature 042 admin authentication protects management surfaces; secret reads return status only.
- **Engineering Tooling Protocol**: Pass. No host application is added to the base image.
- **UI & Testing**: Pass. Existing response compatibility is preserved through masked status fields; frontend changes are limited to consuming that contract if required.
- **Observability & Tracing**: Pass. Redaction occurs before structured log or trace export.
- **Branch Discipline and Manual Gating**: Pass. Work is isolated on Feature 043 and will stop at review.

## Project Structure

### Documentation (this feature)

```text
specs/043-secrets-container-and-provider-config/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── credential-and-container-contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
packages/core/src/core/
├── secrets.py                 # provider contracts, references, composite lookup
├── atomic_secret_store.py     # lock-file transaction, temp/fsync/replace fallback
├── redaction.py               # shared structured/text redaction
└── workspace.py               # Git operations adopt askpass credentials

packages/tool_registry/src/tool_registry/
├── secrets.py                 # compatibility adapter over shared provider
└── runners/                   # protocol and subprocess logs redact by default

apps/api/src/api/
├── routers/settings.py        # non-secret settings plus credential status only
├── schemas/settings.py        # masked write/status contract
├── routers/logs.py            # authenticated redacted output
└── database/migrate.py        # idempotent backup-first credential extraction seam

docker/
├── Dockerfile                 # no sudo/default secret; non-root runtime
├── entrypoint.sh              # safe config generation and fail-closed validation
├── supervisord.conf           # no universal key
└── .env.example               # generated/required secret guidance

docker-compose.yml
docker-compose.minimal.yml      # narrow data volumes, restricted privileges
docker-compose.legacy.yml       # one-release migration-only volume layout

tests/ and package test trees   # leak, concurrency, migration, argv, container contracts
docs/security/                  # credential migration, rotation, recovery, container guide
```

**Structure Decision**: Reuse existing packages and deployment surfaces. `core` owns the cross-cutting provider/redaction primitives because API, Git, MCP, and integrations already depend on it; route and registry compatibility adapters keep public contracts stable while removing secret values.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design & Contracts

See [data-model.md](data-model.md), [contracts/credential-and-container-contracts.md](contracts/credential-and-container-contracts.md), and [quickstart.md](quickstart.md).

## Constitution Check - Post-Design

All pre-design gates remain passing. The design adds no external identity provider, hosted secret service, background database, agent-specific core dependency, or MCP host application. The temporary legacy Compose file is explicitly migration-only and cannot be the documented default.

## Complexity Tracking

No constitution violations identified.
