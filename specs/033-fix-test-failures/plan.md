# Implementation Plan: Fix Test Validation Failures

**Branch**: `033-fix-test-failures` | **Date**: 2026-06-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/033-fix-test-failures/spec.md`

## Summary

Restore reliable local validation on Windows by fixing AppShell storage access, making the desktop build script cross-platform, and ensuring Python tests run inside a synchronized workspace environment. The implementation will keep existing browser behavior and tests intact while addressing the observed validation blockers.

## Technical Context

**Language/Version**: TypeScript 6.0 for `apps/web`; Python >=3.11 workspace managed by uv

**Primary Dependencies**: React 19, Vite 8, Vitest 4, npm workspaces, uv workspace packages, pytest

**Storage**: Browser `localStorage` for UI preferences; no new durable storage

**Testing**: `npm run test --workspace=apps/web`, `npm run build --workspace=apps/web`, `npm run build:desktop --workspace=apps/web`, `uv run pytest`

**Target Platform**: Windows developer environment, while preserving macOS/Linux compatibility

**Project Type**: Modular monorepo with React frontend, FastAPI backend, Python packages, and Hermes integration package

**Performance Goals**: No measurable runtime performance regression; AppShell preference reads stay synchronous and local

**Constraints**: Do not weaken or remove existing tests. Fix validation failures through robust code and portable scripts. Maintain offline-first local development.

**Scale/Scope**: Narrow validation bugfix across `apps/web`, root/package metadata, and Python workspace configuration if required

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: Changes remain inside existing frontend and workspace configuration boundaries. (Pass)
- **Offline-First Mandate**: Fixes use local tools and existing lockfile/dependencies only. (Pass)
- **UI Component Layers**: AppShell behavior change is limited to storage preference safety and does not introduce styling layer changes. (Pass)
- **3-Tier Testing**: The feature directly restores Tier 1/frontend and Python validation commands. (Pass)
- **Branch Discipline**: Work is on `033-fix-test-failures`. (Pass)
- **Manual Gating**: Implementation will wait for human approval after this plan. (Pass)

## Project Structure

### Documentation (this feature)

```text
specs/033-fix-test-failures/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- validation-commands.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
apps/web/
|-- package.json
|-- src/components/layout/AppShell.tsx
`-- tests/AppShell.spec.tsx

package.json
pyproject.toml
uv.lock
```

**Structure Decision**: Use the existing monorepo layout. No new runtime module is required unless Python validation proves the workspace metadata needs a small packaging correction.

## Complexity Tracking

No constitution violations detected.
