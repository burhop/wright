# Feature Specification: README Overhaul & Branding

**Feature Branch**: `012-readme-branding`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "follow the instructions in docs/community-features/012-readme-branding.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Visual Identity and Branding (Priority: P1)

A developer or user visits the Wright GitHub repository. They are immediately struck by a professional visual identity. At the top of the README, they see a clean, high-quality project logo that combines mechanical engineering elements (e.g., gears, tools) with AI/neural themes. The logo works well both as a high-resolution image and a vector asset. When the repository link is shared on Slack or social media, a rich social preview card displays the logo, a clear tagline, and key features.

**Why this priority**: Branding creates immediate credibility and visual recognition. A professional logo and social preview distinguish Wright as an established project rather than a loose collection of scripts, encouraging adoption and sharing.

**Independent Test**:
* Open `docs/images/wright-logo.svg`, `docs/images/wright-logo.png`, and `docs/images/social-preview.png` in a web browser and confirm they render correctly.
* Inspect the repository settings mock-up in the metadata guide to verify the social preview upload steps are clear.

**Acceptance Scenarios**:
1. **Given** the visual assets, **When** they are loaded in a browser, **Then** `wright-logo.svg` displays sharp vector curves, and `social-preview.png` has exact dimensions of 1280×640px.
2. **Given** the social preview image, **When** it is displayed on sharing platforms, **Then** it clearly shows the tagline "Actuating deterministic tools for designers, engineers, and product managers" alongside key feature icons.

---

### User Story 2 — README Hero and "Why Wright?" Narrative (Priority: P1)

A visitor lands on the repository home page and wants to understand what Wright is and why they should care within 30 seconds. They see a centered hero header with the logo, a concise tagline, and a neat row of status badges (Build, License, Docker Pulls, Python, Node, Stars) using shields.io. Below this, a compelling "Why Wright?" section describes the vision of bringing software developer productivity to traditional engineering, and how Wright acts as a powerful design and engineering agent orchestrator that runs on-prem, local, or with hybrid cloud tools.

**Why this priority**: The hero and core narrative form the landing page copy. It directly drives developer conversion by answering "What is this?" and "Why does it matter?" immediately.

**Independent Test**: View the top section of the updated `README.md` on GitHub or a markdown previewer, and confirm that the tagline, shields.io badges, and orchestrator-driven narrative are present and visually aligned.

**Acceptance Scenarios**:
1. **Given** the updated README, **When** a user reads the top section, **Then** all 6 badges (Build, License, Docker, Python, Node, Stars) load dynamic statuses from shields.io.
2. **Given** the "Why Wright?" section, **When** read by a visitor, **Then** it highlights the agent orchestrator capabilities, the range of tools integrated (commercial, startup, university, open source), and flexible deployment options (local or hybrid cloud).

---

### User Story 3 — Feature Cards & UI Showcases (Priority: P2)

A developer scrolling down the README wants to see the specific capabilities of Wright and what the user interface looks like. They find a grid-like or list layout of feature cards (with emojis) detailing CAD generation, FEA, manufacturing, local LLM adapters, and Docker setups. Below this, they see actual UI screenshots embedded directly with captions, showing the chat transcript, the tool registry, and the file vault.

**Why this priority**: Developers expect to see the product in action. Visual highlights and screenshots back up the claims in the narrative and prove that the software exists and is functional.

**Independent Test**: Verify that the README embeds the 4 screenshots located in `docs/images/` and that the links resolve correctly.

**Acceptance Scenarios**:
1. **Given** the README features section, **When** viewed, **Then** it presents 6 distinct feature highlights (CAD, FEA, Manufacturing, Multi-Agent, Local, Docker) with standard icons.
2. **Given** the screenshot image embeds in the README, **When** clicked, **Then** they point to valid paths inside the `docs/images/` folder and render correctly.

---

### User Story 4 — Setup and Architecture Diagrams (Priority: P2)

A technical user wants to understand the internals of Wright and get it running locally. They find a simplified, copy-pasteable Quick Start block showing the exact docker compose and make commands needed. Below this, they find a Mermaid diagram showing the flow of components: from the API, through agent adapters, down to the tool registries and MCP tools.

**Why this priority**: Simplifies the entry point for technical execution while providing visual architectural context for engineers wanting to contribute to the code.

**Independent Test**: Render the Mermaid diagram in a markdown editor to check for syntax errors, and copy-paste the Quick Start commands to verify they represent the actual running stack commands.

**Acceptance Scenarios**:
1. **Given** the Quick Start section, **When** a user follows the command block, **Then** they can copy and run the commands directly to build and start the Docker containers.
2. **Given** the Mermaid diagram, **When** rendered on GitHub, **Then** it displays a clean flowchart depicting the `FastAPI API -> BaseAgentEngine (Hermes) -> ToolRegistry -> MCP Tools (OpenSCAD/FEA)` relationship.

---

### Edge Cases

* **What happens if a user views the README on a registry like npm?** The image paths for the logo and screenshots must use absolute paths or raw GitHub URLs if relative paths fail to render. We should use standard relative paths (which GitHub handles natively) and ensure they are clean.
* **What happens if a shields.io badge service goes down?** The badges will display a fallback "offline" style or fail to load. The README links should be robust and use standard shields.io templates.
* **What happens if a developer edits the screenshots locally?** Any screenshots generated by Playwright are saved in the root and ignored. The static ones committed to `docs/images/` will not be affected unless explicitly copied over, keeping version control clean.

## Requirements *(mandatory)*

### Functional Requirements

* **FR-001**: The repository MUST include a professional vector logo in SVG format saved at `docs/images/wright-logo.svg`.
* **FR-002**: The repository MUST include a high-resolution logo in PNG format saved at `docs/images/wright-logo.png`.
* **FR-003**: The repository MUST include a social preview image (1280x640px) saved at `docs/images/social-preview.png`, containing the tagline, logo, and core feature icons.
* **FR-004**: The `README.md` MUST include a Hero section with a centered logo, tagline, and shields.io badge row (Build, License, Docker Pulls, Python, Node, Stars).
* **FR-005**: The `README.md` MUST include a "Why Wright?" section presenting how Wright orchestrates agentic tools to bring software developer productivity gains to traditional engineering roles.
* **FR-006**: The `README.md` MUST include emoji-prefixed feature highlight cards for Agent Orchestration, Modular Tool Integration, Software Developer-Level Productivity, Flexible Deployment, and Docker Deployment.
* **FR-007**: The `README.md` MUST embed the 4 UI screenshots (`screenshot_initial.png`, `screenshot_agent_chat.png`, `screenshot_tool_registry.png`, `screenshot_file_vault.png`) relocated to `docs/images/` with clear captions.
* **FR-008**: The `README.md` MUST contain a simplified Quick Start block specifying the absolute minimum steps to clone, configure, build, and run via Docker compose.
* **FR-009**: The `README.md` MUST include a Mermaid architecture diagram showing the component hierarchy and request flows.
* **FR-010**: The `README.md` MUST contain a contributing callout linking to `CONTRIBUTING.md` and a footer including license info and a star-history.com graph.
* **FR-011**: None of the changes made by this feature may modify application code, configuration files (other than README/images), or Docker compose files.

### Key Entities

* **Visual Asset**: A graphic file (SVG or PNG) representing the logo or social preview card.
* **Badges**: Shields.io dynamically generated SVG status indicator badges.
* **Architecture Diagram**: A Mermaid diagram representing the modular monorepo and API flow.

## Success Criteria *(mandatory)*

### Measurable Outcomes

* **SC-001**: 100% of the 3 new visual assets (wright-logo.svg, wright-logo.png, social-preview.png) exist in `docs/images/` and are high-quality, non-placeholder images.
* **SC-002**: The `README.md` contains the centered logo, badges, core sections, quickstart, Mermaid diagram, and footer without breaking any existing formatting.
* **SC-003**: 100% of the links in the README (badges, CONTRIBUTING.md link, star history, licenses) resolve successfully (no 404s).
* **SC-004**: The Mermaid diagram renders successfully on GitHub with zero syntax warnings.
* **SC-005**: The repository root directory contains zero `screenshot_*.png` files.

## Assumptions

* The Docker Hub repository path for badges is assumed to be `burhop/wright`. If this repository is not yet published, the badge will show a placeholder or "offline" until published.
* The shields.io build status badge points to the main CI workflow in the repository (`.github/workflows/ci.yml` or equivalent).
* The logo will be created using professional design guidelines, utilizing a cohesive local-first mechanical/AI theme (such as a gear interlaced with neural network paths).
