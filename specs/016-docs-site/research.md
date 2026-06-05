# Research: Documentation Site

**Branch**: `016-docs-site` | **Date**: 2026-06-05

## Technical Decisions & Rationale

### 1. Documentation Engine: MkDocs Material
* **Decision**: Set up MkDocs with the Material theme (`mkdocs-material`) via the project's Python dependencies.
* **Rationale**:
  - Python-native framework integrates natively with `pyproject.toml` and development environments.
  - Material theme offers premium aesthetic designs, highly customizable palettes, built-in search indexing, and admonitions.
* **Alternatives Considered**:
  - *Docusaurus*: Requires installing Node.js/npm dependencies in the root project space, which increases project build times and adds dependency complexity.

### 2. GitHub Pages Deployment via GitHub Actions
* **Decision**: Auto-build and deploy the static site files to the `gh-pages` branch using a workflow at `.github/workflows/docs-deploy.yml` triggered on push to `main`.
* **Rationale**:
  - Automatically synchronizes live documentation with the stable main code.
  - The `ghaction-github-pages` action handles git checkouts, python env caching, building, and publishing seamlessly.

### 3. Folder Structure & Layout Navigation
* **Decision**: Structure directories under `docs/` matching the main user flows (Getting Started, User Guide, Architecture, Contributing, API, MCP Catalog).
* **Rationale**:
  - Keeps source files organized and prevents folder nesting from getting cluttered.
  - Aligns navigation menus clearly with standard industry developer portals.

### 4. Legacy Content Consolidation
* **Decision**: Consolidate `technical_analysis.md`, `agent-docker-architecture.md`, and `Engineering MCP Tools Discovery.md` content into target directories in `docs/` while retaining original files for back-compatibility.
* **Rationale**:
  - Eliminates documentation sprawl.
  - Restructures technical content into standard web formats (markdown guides) with search visibility.
