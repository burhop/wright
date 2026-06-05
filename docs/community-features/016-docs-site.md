# Feature Brief: Documentation Site

Create a dedicated documentation website for Wright using MkDocs Material, deployed to GitHub Pages. This replaces the scattered markdown files and PDF with a searchable, versioned, professional documentation site — the single most important signal of project maturity, as demonstrated by every popular agentic framework (OpenHands has docs.openhands.dev, CrewAI has docs.crewai.com, OpenClaw has docs.openclaw.ai).

## What to build

### Docs Framework Setup

1. **MkDocs Material project** — Set up MkDocs with the Material theme in a `docs/` directory (or a dedicated docs config):
   - `mkdocs.yml` configuration at the repo root
   - Material theme with Wright branding colors and logo
   - Search plugin enabled
   - Navigation organized by audience (users vs. contributors vs. API reference)
   - Dark mode support (default to dark, matching engineering tooling aesthetics)

2. **GitHub Pages deployment** (`.github/workflows/docs-deploy.yml`) — Auto-deploy docs on every merge to `main`:
   - Build MkDocs site
   - Deploy to GitHub Pages (gh-pages branch)
   - The site should be available at `https://burhop.github.io/wright/` (or a custom domain if configured)

### Documentation Structure

Organize the docs site with these top-level sections:

3. **Getting Started** — The first thing new users see:
   - What is Wright? (elevator pitch + screenshot)
   - Prerequisites (hardware, software)
   - Quick Start with Docker (3-step copy-paste)
   - Quick Start without Docker (local development)
   - First steps after installation (what to try first)

4. **User Guide** — For operators running Wright:
   - Docker deployment guide (full version of the README's Docker section)
   - Environment configuration reference (all env vars with descriptions and defaults)
   - Makefile targets reference
   - Backup and restore procedures
   - Recovery runbook (migrate from docs/agent-docker-architecture.md)
   - Health checking and monitoring
   - Updating Wright (pulling new images, migration notes)

5. **Architecture** — For developers understanding the system:
   - System overview with Mermaid diagram
   - Monorepo structure explanation (apps/, packages/)
   - Agent adapter pattern
   - Tool registry and MCP integration
   - Data storage model (SQLite + LanceDB + File Vault)
   - Observability and tracing (OpenTelemetry + Jaeger)
   - Migrate and consolidate content from: `docs/technical_analysis.md`, `docs/agent-docker-architecture.md`, `constitution.md`

6. **Contributing** — For people who want to help:
   - Development environment setup (detailed version)
   - Spec-kit workflow guide (specify → plan → tasks → implement)
   - Code style and conventions
   - Testing guide (pytest, Playwright, smoke tests)
   - PR submission guide
   - Architecture decision records (link to specs/ directory)

7. **API Reference** — Auto-generated from FastAPI:
   - Embed or link to the FastAPI auto-generated OpenAPI docs (Swagger UI at /docs)
   - Document how to access the API reference from a running instance
   - If feasible, generate static API docs from the OpenAPI schema

8. **MCP Tools Catalog** — Reference for available engineering tools:
   - List of all MCP tool servers with descriptions
   - How to add a custom MCP tool
   - Tool online/offline fallback behavior
   - Migrate relevant content from `docs/Engineering MCP Tools Discovery.md`

### Content Migration

9. **Migrate existing docs** — Move content from scattered locations into the docs site:
   - `docs/technical_analysis.md` → Architecture section
   - `docs/agent-docker-architecture.md` → User Guide (Docker) + Architecture
   - `docs/Engineering MCP Tools Discovery.md` → MCP Tools Catalog
   - `docs/virtual_engineer_architecture.pdf` → Keep as downloadable but summarize key points in Architecture
   - `constitution.md` → Referenced from Architecture and Contributing (keep original file, link to it)

### Polish

10. **Navigation and cross-linking** — Ensure all pages are properly linked in the nav, with breadcrumbs and next/previous page navigation.

11. **Admonitions and callouts** — Use Material's admonition blocks (note, warning, tip, danger) for important information throughout the docs.

## Constraints

- Use MkDocs Material (Python-based, consistent with the project's tech stack) — not Docusaurus or other JS-based doc generators
- Do not delete original source docs — the docs site should reference or migrate content, but original files can remain for backwards compatibility
- The docs site must build and deploy without requiring any application code to be running
- Keep the docs site lightweight — no heavy JavaScript, no complex build steps
- The documentation must be maintainable by contributors who know Markdown (no custom templating languages)
- Do not modify any application source code or Docker configuration
