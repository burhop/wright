# Feature Specification: Documentation Site

**Feature Branch**: `016-docs-site`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Build the plan using docs/community-features/016-docs-site.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adopt MkDocs Material & Organization (Priority: P1)

As a new user or contributor, I want a professional, searchable, and responsive documentation site with structured navigation (Getting Started, User Guide, Architecture, Contributing, API Reference, MCP Tools Catalog) and default dark mode, so that I can easily find information about Wright.

**Why this priority**: Essential first step. Users need a centralized, organized, and searchable documentation base to understand the project architecture and deploy the platform.

**Independent Test**:
* Run MkDocs server locally, navigate to `http://localhost:8000`, and confirm navigation items are laid out correctly.
* Search for a specific keyword (e.g. "Hermes") using the search bar and verify that relevant pages are returned.

**Acceptance Scenarios**:
1. **Given** a user loading the docs homepage, **When** they look at the theme, **Then** it defaults to dark mode with Wright branding colors.
2. **Given** the search bar, **When** a keyword is entered, **Then** matching topics are listed instantly.

---

### User Story 2 - Automated GitHub Pages Deployment (Priority: P1)

As a maintainer, I want every merge to `main` to automatically build the MkDocs site and deploy it to GitHub Pages, so that the documentation site is always up-to-date with the code.

**Why this priority**: Eliminates the manual overhead of building and hosting documentation site files on every code update.

**Independent Test**:
* Push a commit to `main` and verify that `.github/workflows/docs-deploy.yml` starts, builds, and pushes files to the `gh-pages` branch.

**Acceptance Scenarios**:
1. **Given** a merge to `main`, **When** GHA completes, **Then** the updated site is live on the GitHub Pages URL.

---

### User Story 3 - Historical Content Migration & Consolidation (Priority: P2)

As a developer, I want existing design analysis, technical architecture, and MCP tools discovery docs to be consolidated into the new documentation structure, so that I don't have to look through scattered files in the repo.

**Why this priority**: Clean repository organization. Prevents duplication and stale copies of design specs.

**Independent Test**:
* Check pages under User Guide and Architecture sections and confirm they match contents of the legacy `technical_analysis.md` and `agent-docker-architecture.md` files.

**Acceptance Scenarios**:
1. **Given** a developer looking for architectural blueprints, **When** they click on the Architecture section, **Then** they find system overview diagrams and monorepo structure guidelines.

---

### User Story 4 - Formatting Callouts & Admonitions (Priority: P3)

As a reader, I want important notes, warnings, and tips to be styled with clean, scannable callout blocks (admonitions), so that key details stand out.

**Why this priority**: Low priority styling refinement. Enhances user experience and scannability.

**Independent Test**:
* Verify callouts are rendered with clean colors and descriptive icons on local MkDocs Material server.

**Acceptance Scenarios**:
1. **Given** a warning block, **When** rendered, **Then** it displays inside a styled callout box with a warning icon.

---

### Edge Cases

- **FastAPI API Reference Offline**: Since the API reference auto-generation relies on a running instance, the static docs should explain how to run FastAPI locally to access the interactive Swagger UI `/docs` endpoint, alongside providing static OpenAPI summaries.
- **Merge Conflicts in gh-pages**: Git history mismatch on `gh-pages` may block deployments. The deployment action must force-push to `gh-pages` to prevent build queues from getting blocked.

## Requirements *(mandatory)*

### Functional Requirements

* **FR-001**: The project MUST configure a MkDocs Material site at `mkdocs.yml` at the repository root.
* **FR-002**: The documentation website MUST feature a default dark mode theme matching the Wright branding palette and an enabled search bar.
* **FR-003**: The documentation structure MUST be partitioned into Getting Started, User Guide, Architecture, Contributing, API Reference, and MCP Tools Catalog.
* **FR-004**: The project MUST deploy the built documentation site to GitHub Pages (`gh-pages` branch) automatically on every push or merge to the `main` branch using a workflow at `.github/workflows/docs-deploy.yml`.
* **FR-005**: Existing documentation files (`docs/technical_analysis.md`, `docs/agent-docker-architecture.md`, `docs/Engineering MCP Tools Discovery.md`) MUST be migrated and consolidated into their respective sections in the new docs directory.
* **FR-006**: The documentation site MUST use standard Material admonition extensions for warnings, notes, tips, and guidelines.
* **FR-007**: None of the changes made by this feature may modify application code or Docker runtime configurations.
* **FR-008**: All workflow files MUST use pinned action versions for security.

### Key Entities

- **MkDocs Project**: Config file `mkdocs.yml` and markdown sources in `docs/` folder.
- **Deployment Workflow**: GHA script building and force-pushing to `gh-pages` branch.
- **API reference**: FastAPI OpenAPI documentation pointers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

* **SC-001**: `mkdocs.yml` exists in root and contains correct Material configuration.
* **SC-002**: Auto-deploy workflow `.github/workflows/docs-deploy.yml` triggers on pushes to `main` and successfully builds the static site.
* **SC-003**: All migrated content is accessible via the structured documentation pages under `docs/`.
* **SC-004**: Admonitions and navigation linkages are active and format correctly.
* **SC-005**: Static API documentation points to local FastAPI Swagger interface parameters.

## Assumptions

- The repository owner enables GitHub Pages in repository settings and maps it to the `gh-pages` branch.
- The hosting path resolves to `https://burhop.github.io/wright/`.
