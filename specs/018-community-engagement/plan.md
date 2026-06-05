# Implementation Plan: Community Engagement Infrastructure

**Branch**: `018-community-engagement` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/018-community-engagement/spec.md`

## Summary

Establish the outward-facing community building blocks for Wright by documenting Discord channel configurations, integrating communication channels across core project entry points (README, docs, support guides), implementing three self-contained example projects under `examples/` running against the Docker deployment, draft marketing assets (launch blog post, demo video script, curated issues, awesome list submissions), and initializing automated contributor recognition tool configurations.

## Technical Context

**Language/Version**: Python 3.11+ (for example scripts), Markdown (for document templates/scripts/posts), JSON (for all-contributors configuration)

**Primary Dependencies**: `all-contributors-cli` (v8.x or compatible npm package for contributor badge rendering)

**Storage**: Local files for example configurations and outputs

**Testing**: Local verification of example project execution against the running Wright API container

**Target Platform**: GitHub, Discord, Local workstation running Docker

**Project Type**: Documentation, community scaffolding, developer relations assets

**Performance Goals**: Each example script must connect, execute its core agent workflow, and generate/save the output artifacts in under 2 minutes.

**Constraints**:
- Do not modify any application source code (`apps/` or `packages/`), docker files, or CI/CD pipelines.
- Examples must run offline-first against the local API endpoint.
- Discord server details must be written as instructions (no active API creation).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Framework (FastAPI)**: Compliant. Example projects will interact with the existing FastAPI endpoints.
- **Architecture (Modular Monorepo)**: Compliant. No internal backend app logic is touched.
- **Offline-First Mandate**: Compliant. All example scripts will target `http://localhost:8000` or local docker host endpoints and can run completely local without internet dependencies.
- **Container Strategy (Thick Base / Thin Code)**: Compliant. Example scripts will consume the running docker deployment.
- **Zero-Server Databases**: Compliant.
- **Local Authentication**: Compliant.
- **Engineering Tooling Protocol**: Compliant.
- **UI & Testing**: Compliant. Example scripts will have their own unit tests/validations.
- **Observability**: Compliant.
- **Autonomous Agent Workflow Rules**: Compliant. Feature planning occurs on the isolated `018-community-engagement` branch.
- **Governance**: Compliant.

## Project Structure

### Documentation (this feature)

```text
specs/018-community-engagement/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Decision log for community templates and examples
├── data-model.md        # all-contributors configuration schema
└── quickstart.md        # How to execute examples locally
```

### Source Code (repository root)

```text
examples/
├── quickstart/
│   ├── README.md        # Run instructions for quickstart
│   └── main.py          # Python script to hit wright agent API
├── bracket-design/
│   ├── README.md        # Run instructions for bracket design CAD
│   └── main.py          # Python script to run bracket design CAD agent
└── bolt-analysis/
    ├── README.md        # Run instructions for bolt analysis
    └── main.py          # Python script to execute calculations via wright API

docs/
├── community/
│   └── discord-admin.md # Admin documentation for Discord setup
├── blog/
│   └── introducing-wright.md # Launch blog post draft
├── demo-script.md       # Scene-by-scene script for demo video
├── good-first-issues.md # 5-10 curated starter tasks
└── awesome-list-submissions.md # Submissions for curated lists

.all-contributorsrc      # All contributors config file
```

**Structure Decision**: Place runnable example projects under `examples/`, community admin guides under `docs/community/`, marketing and developer-facing scripts/blog drafts under `docs/`, and `.all-contributorsrc` configuration in the project root.

## Complexity Tracking

> *No violations of the Constitution Check.*
