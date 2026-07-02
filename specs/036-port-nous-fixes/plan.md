# Implementation Plan: Port Nous Fixes

**Branch**: `codex/port-nous-good-fixes` | **Date**: 2026-07-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/036-port-nous-fixes/spec.md`

## Summary

Extract reusable fixes from the `nous_hackathon` prototype branch into the current `dev`-based extraction branch without merging the prototype branch or carrying over payment, demo, hackathon stack, generated output, nemoclaw, or paid-demo expansion work. The implementation uses the existing `scratch/nous_hackathon_candidates/` review folder as a staging artifact, ports selected source/test changes in small groups, and validates touched backend/frontend areas with targeted tests.

## Technical Context

**Language/Version**: Python >=3.11 for backend/packages; TypeScript 6.0 and React 19 for frontend

**Primary Dependencies**: FastAPI, Pydantic, SQLite, structlog, pytest, React, Vite, Vitest, Playwright

**Storage**: Existing local SQLite state and workspace files; review-only copied files under `scratch/nous_hackathon_candidates/`

**Testing**: `uv run pytest` for targeted backend/package tests; `npm run test --workspace=apps/web` for targeted frontend tests when available

**Target Platform**: Local Wright monorepo branch; MCP validation remains bounded by the Ubuntu clean-container process

**Project Type**: Modular monorepo with FastAPI backend, Python adapter/registry packages, React frontend, and Docker validation support

**Performance Goals**: Preserve current runtime behavior; extracted UI changes must not introduce layout instability in touched views; review diffs must remain small enough for maintainers to inspect quickly

**Constraints**: Do not merge `nous_hackathon`; do not create another branch; do not port Stripe billing, nemoclaw-specific expansion, hackathon Docker/scripts, generated outputs, or paid-demo MCP files; do not add MCP-specific host software to the base Docker image for catalog validation

**Scale/Scope**: Candidate review covers 45 copied source/test/config/docs files. Implementation may accept, partially accept, or reject each candidate based on whether it stands alone from excluded prototype behavior.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: Accepted changes must stay within existing API, adapter, registry, core, and UI ownership boundaries. (Pass)
- **Offline-First Mandate**: No accepted change may require external cloud/payment services for core behavior. (Pass)
- **Container Strategy**: MCP validation changes must follow the clean-container process and must not preload MCP-specific host software into the base image. (Pass)
- **Agent Abstraction**: Hermes/agent changes must remain adapter-based and must not hardcode a specific prototype agent. (Pass)
- **UI Component Layers**: Frontend changes must preserve existing component/test structure and use current design conventions. (Pass)
- **3-Tier Testing**: Targeted unit/component tests must be run for accepted change areas where practical. (Pass)
- **Observability**: Backend changes must preserve structured logging/tracing conventions. (Pass)
- **Branch Discipline**: Work is already on a dedicated extraction branch; user explicitly requested no new branch. (Pass)
- **Manual Gating**: User explicitly requested `.specify`, `.plan`, `.tasks`, and `.implement` in this turn. (Pass)

## Project Structure

### Documentation (this feature)

```text
specs/036-port-nous-fixes/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- extraction-contract.md
|   `-- validation-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
scratch/nous_hackathon_candidates/
|-- MANIFEST.md
`-- <candidate files copied from nous_hackathon>

apps/api/
|-- src/api/
`-- tests/

apps/web/
|-- src/
`-- tests/

packages/
|-- agent_adapters/
|-- core/
`-- tool_registry/

docs/mcp-catalog/
```

**Structure Decision**: Use the existing monorepo structure. The candidate folder is review-only staging material; accepted changes are applied back into their normal source, test, or documentation locations.

## Complexity Tracking

No constitution violations detected.

## Phase 0 Research

See [research.md](research.md).

## Phase 1 Design

See [data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).

## Post-Design Constitution Re-Check

- **Modular Monorepo Boundaries**: Design maps each accepted change group to existing files and tests. (Pass)
- **Offline-First Mandate**: Exclusion rules explicitly block payment/demo/cloud-dependent prototype expansions. (Pass)
- **Container Strategy**: Validation contract preserves the clean-container MCP process. (Pass)
- **3-Tier Testing**: Quickstart defines targeted backend/frontend checks. (Pass)
- **Safety**: Exclusion contract blocks Stripe, nemoclaw, hackathon stack, generated outputs, and paid-demo MCP artifacts. (Pass)
