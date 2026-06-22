# Implementation Plan: Engineering Tool Catalog

**Branch**: `028-wright-tool-catalog` | **Date**: 2026-06-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from [spec.md](spec.md)

## Summary

The goal of this feature is to implement a robust, validated catalog registry containing ~30 engineering MCP tool definitions. We will:
1. Define Pydantic validation schemas in `schemas.py` (`CatalogEntry`, `EnvVarDefinition`, `DependencySpec`) matching the main `tool_registry` database requirements exactly.
2. Build the `catalog.yaml` dataset containing ~30 engineering MCP entries categorized by domains.
3. Write `catalog.py` with the `CatalogLoader` class handling loading, parsing, search, and domain taxonomy filtering.
4. Implement comprehensive unit tests in the `tests/` directory to ensure catalog parser validity and search correctness.

## Technical Context

**Language/Version**: Python >= 3.11

**Primary Dependencies**: `pyyaml>=6.0`, `pydantic>=2.0`, `httpx>=0.27`

**Storage**: YAML file (`catalog.yaml`)

**Testing**: `pytest`

**Target Platform**: Linux server

**Project Type**: library/plugin

**Performance Goals**: Catalog load and initial validation in < 20ms. Substring search query resolving in < 5ms.

**Constraints**: Strict compliance with the existing `tool_registry.models.EnvVarDefinition` schema to facilitate direct database import. No database queries inside the catalog loader (must remain purely filesystem-based).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

* **Structured Logging Compliance**: Uses `structlog` for loader warnings if malformed entries occur. Verified.
* **Offline-First Mandate**: The loader runs completely locally, parsing files in-process without network lookups. Verified.
* **Architecture Integrity**: Keep catalog definitions fully decoupled from execution logic. Verified.

## Project Structure

### Documentation (this feature)

```text
specs/028-wright-tool-catalog/
├── plan.md              # This file
├── research.md          # Technology decisions
├── data-model.md        # Pydantic schemas
├── quickstart.md        # Load and verify examples
├── contracts/
│   └── catalog_interface.md  # Loader class contracts
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (repository root)

```text
hermes-plugin-wright/
├── pyproject.toml
├── plugin.yaml
├── __init__.py
├── catalog.yaml         # [NEW] Contains 30+ catalog entries
├── schemas.py           # [NEW] Contains CatalogEntry, EnvVarDefinition schemas
├── catalog.py           # [NEW] Contains CatalogLoader
├── tests/
│   ├── conftest.py
│   └── test_catalog.py  # [NEW] Loader and search unit tests
└── README.md
```

**Structure Decision**: Option 1 (Single project), maintaining code directly in `hermes-plugin-wright/`.

## Complexity Tracking

No violations of the project constitution are introduced. All catalog data fits in memory and queries are performed locally.
