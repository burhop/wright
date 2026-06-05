# Implementation Plan: Repo Hygiene & Legal Foundation

**Branch**: `011-repo-hygiene` | **Date**: 2026-06-05 | **Spec**: [spec.md](file:///home/burhop/repos/wright/specs/011-repo-hygiene/spec.md)

**Input**: Feature specification from `/specs/011-repo-hygiene/spec.md`

## Summary

Create and configure the necessary community health, licensing, contribution, and metadata guidelines to establish a professional open-source foundation for Wright. This includes creating LICENSE, CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md, CONTRIBUTING.md, and `.github/CODEOWNERS`, as well as cleaning up loose log, test output, database, and screenshot files in the repository root, updating `.gitignore` to prevent tracking of such files, and documenting the repository's GitHub metadata configuration.

## Technical Context

**Language/Version**: N/A (Documentation/Configuration only; repository targets Python 3.11+ and Node.js 22+)

**Primary Dependencies**: None (No code dependencies; compliance with GitHub Community Profile checklist)

**Storage**: N/A (Excluding local SQLite state database `state.db` from version control)

**Testing**: N/A (Manual validation of community health checklists and file locations)

**Target Platform**: GitHub (Community Profile checklist compliance)

**Project Type**: Open-source repository configuration

**Performance Goals**: N/A

**Constraints**: Do not modify existing source code, Docker files, CI/CD configurations, or README.md.

**Scale/Scope**: 7 health files and metadata documentation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Framework (FastAPI): N/A
- Architecture (Modular Monorepo): N/A
- Offline-First Mandate: N/A
- Container Strategy: N/A
- Agent Abstraction: N/A
- Databases (Zero-Server): N/A
- State & Memory: N/A
- Vector RAG: N/A
- File Vault: N/A
- Security & Identity: N/A
- Engineering Tooling Protocol: N/A
- UI & Testing (3-Tier Pyramid): N/A
- Observability & Tracing: N/A
- Autonomous Agent Workflow Rules: Complies with Branch Discipline (working on branch `011-repo-hygiene`) and Phase Isolation (planning approved by operator before implementation).

## Project Structure

### Documentation (this feature)

```text
specs/011-repo-hygiene/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
.github/
└── CODEOWNERS           # Reviewer mapping

docs/
├── images/              # Relocated screenshots
│   ├── screenshot_agent_chat.png
│   ├── screenshot_file_vault.png
│   ├── screenshot_initial.png
│   └── screenshot_tool_registry.png
└── metadata-guide.md    # Guide for GitHub repo metadata (About + topics)

LICENSE                  # MIT License
CODE_OF_CONDUCT.md       # Contributor Covenant v2.1
SECURITY.md              # Security reporting instructions
SUPPORT.md               # User support channels guide
CONTRIBUTING.md          # Developer setup & guidelines
.gitignore               # Cleaned & updated git exclusion rules
```

**Structure Decision**: Files will be placed in the repository root and `.github/` folder as required by GitHub's layout conventions. Screenshots will be moved to `docs/images/` and the metadata guide will be placed at `docs/metadata-guide.md`.

## Complexity Tracking

> *No violations of the Constitution Check.*
