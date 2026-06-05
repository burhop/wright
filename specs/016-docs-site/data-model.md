# Data Model & Configuration Schemas: Documentation Site

**Branch**: `016-docs-site` | **Date**: 2026-06-05

This document defines the folder layouts, file mappings, and navigation structures for the documentation site.

## 1. Directory Structure Layout

The documentation source files reside under `docs/` matching this structure:

```text
docs/
├── index.md                        # Site Homepage
├── getting-started/
│   ├── overview.md                 # What is Wright
│   ├── prerequisites.md            # Hardware/Software
│   ├── quickstart-docker.md        # Docker deployment
│   └── quickstart-local.md         # Local deployment
├── user-guide/
│   ├── docker.md                   # Docker details
│   ├── env-vars.md                 # Configuration reference
│   ├── makefile.md                 # CLI command reference
│   ├── maintenance.md              # Backups, restores, and updates
│   └── recovery.md                 # Recovery runbook
├── architecture/
│   ├── system-overview.md          # Systems overview & Mermaid
│   ├── project-structure.md        # Monorepo directory map
│   ├── agent-adapters.md          # Hot-swappable agent profiles
│   ├── tool-registry.md            # MCP tool orchestration
│   ├── data-storage.md             # SQLite, LanceDB, File vault
│   └── observability.md            # OTEL + Jaeger tracing
├── contributing/
│   ├── dev-setup.md                # Development environment setup
│   ├── spec-kit.md                 # Spec-driven methodology
│   ├── code-style.md               # Ruff + eslint guidelines
│   ├── testing.md                  # Testing pyramid
│   └── pull-requests.md            # Checklist and submissions
├── api/
│   └── api-reference.md            # FastAPI interactive swagger guides
└── mcp-catalog/
    ├── tools-list.md               # Available 34 MCP servers
    ├── custom-tools.md             # BaseTool inheritance
    └── offline-cache.md            # Write-through offline caching
```

---

## 2. Navigation Menu Structure (`mkdocs.yml`)

The `nav` parameter in `mkdocs.yml` maps menus to markdown paths:

```yaml
nav:
  - Home: index.md
  - Getting Started:
      - Overview: getting-started/overview.md
      - Prerequisites: getting-started/prerequisites.md
      - Quick Start (Docker): getting-started/quickstart-docker.md
      - Quick Start (Local): getting-started/quickstart-local.md
  - User Guide:
      - Docker Deployment: user-guide/docker.md
      - Environment Variables: user-guide/env-vars.md
      - Makefile Targets: user-guide/makefile.md
      - Maintenance & Updates: user-guide/maintenance.md
      - Recovery Runbook: user-guide/recovery.md
  - Architecture:
      - System Overview: architecture/system-overview.md
      - Project Structure: architecture/project-structure.md
      - Agent Adapters: architecture/agent-adapters.md
      - Tool Registry: architecture/tool-registry.md
      - Data Storage: architecture/data-storage.md
      - Observability: architecture/observability.md
  - Contributing:
      - Development Setup: contributing/dev-setup.md
      - Spec-Kit Workflow: contributing/spec-kit.md
      - Code Style: contributing/code-style.md
      - Testing Guidelines: contributing/testing.md
      - Pull Requests: contributing/pull-requests.md
  - API Reference: api/api-reference.md
  - MCP Tools Catalog:
      - Tool Directory: mcp-catalog/tools-list.md
      - Custom MCP Tools: mcp-catalog/custom-tools.md
      - Offline Caching: mcp-catalog/offline-cache.md
```
