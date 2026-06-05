# Implementation Plan: README Overhaul & Branding

**Branch**: `012-readme-branding` | **Date**: 2026-06-05 | **Spec**: [spec.md](file:///home/burhop/repos/wright/specs/012-readme-branding/spec.md)

**Input**: Feature specification from `/specs/012-readme-branding/spec.md`

## Summary

Transform the Wright repository presentation by generating a professional visual identity and restructuring the `README.md` into a high-converting landing page. This will involve creating a project logo (SVG + PNG) and a social preview image (1280x640px) under `docs/images/`, and rewriting `README.md` to include a centered Hero, Shields.io badges, vision and orchestration narrative, feature cards, UI screenshots, simplified quick start, a Mermaid architecture diagram, and footer links.

## Technical Context

**Language/Version**: N/A (Markdown and visual assets only)

**Primary Dependencies**: Shields.io (for dynamic badges), Mermaid.js (for architectural diagram rendering on GitHub), Star-History.com (for sidebar star-history graphs)

**Storage**: N/A

**Testing**: N/A (Manual visual verification of README rendering, link validation, and SVG/PNG clarity)

**Target Platform**: GitHub Repo Landing Page (Desktop and Mobile)

**Project Type**: Documentation and Branding

**Performance Goals**: N/A

**Constraints**: Do not modify existing application source code (Python, TypeScript), configuration files, or Docker scripts. The README must remain a single file.

**Scale/Scope**: 1 README restyle, 3 visual assets, 1 Mermaid diagram.

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
- Autonomous Agent Workflow Rules: Fully compliant. The plan is created on feature branch `012-readme-branding` and is submitted to the operator before code modifications.

## Project Structure

### Documentation (this feature)

```text
specs/012-readme-branding/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code & Assets

```text
docs/
├── images/
│   ├── wright-logo.svg      # [NEW] Vector logo
│   ├── wright-logo.png      # [NEW] High-res raster logo
│   ├── social-preview.png   # [NEW] Shared link preview image (1280x640)
│   ├── screenshot_initial.png
│   ├── screenshot_agent_chat.png
│   ├── screenshot_tool_registry.png
│   └── screenshot_file_vault.png
README.md                    # [MODIFY] Restructured landing page
```

**Structure Decision**: Place all static visual assets in `docs/images/` to maintain repository clean layouts. Modify the root `README.md` directly.

## Complexity Tracking

> *No violations of the Constitution Check.*
