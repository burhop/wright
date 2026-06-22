# Implementation Plan: Hermes Wright Plugin Skeleton & Registration

**Branch**: `027-wright-plugin-skeleton` | **Date**: 2026-06-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from [spec.md](spec.md)

## Summary

The goal of this feature is to establish the base codebase structure for the Hermes Agent plugin integration. We will create a new Python package named `hermes-plugin-wright` at the root of the repository. This package will define the metadata in `plugin.yaml`, implement the plugin entry point registration in `__init__.py` using structured logging (`structlog`), define the distribution/dependency specifications in `pyproject.toml` using the `hatchling` build backend, and bootstrap test configurations.

## Technical Context

**Language/Version**: Python >= 3.11

**Primary Dependencies**: `httpx>=0.27`, `pyyaml>=6.0`, `pydantic>=2.0`, `structlog`

**Storage**: N/A (State is managed by the main Wright API and Hermes runtime)

**Testing**: `pytest`

**Target Platform**: Linux server (integrated with the Docker appliance and local environments)

**Project Type**: library/plugin

**Performance Goals**: Load and register in < 50ms upon Hermes initialization.

**Constraints**: Must run entirely offline and log exclusively through structured JSON logs via `structlog`.

**Scale/Scope**: Skeleton setup phase only, with placeholders for subsequent features (catalog, bridge, slash commands).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

* **Structured Logging Compliance**: The plugin entry point must emit JSON logs using `structlog`. Verified (matches Section 7 of the Constitution).
* **Architecture Integrity**: The package is isolated in its own root directory `hermes-plugin-wright/`, preventing contamination of the main backend/frontend/packages.
* **Offline-First Mandate**: The plugin loading does not perform any network calls and functions fully air-gapped.

## Project Structure

### Documentation (this feature)

```text
specs/027-wright-plugin-skeleton/
├── plan.md              # This file
├── research.md          # Technology decisions
├── data-model.md        # Manifest & entry point schemas
├── quickstart.md        # Installation & validation guide
├── contracts/
│   └── plugin_interface.md  # Entry point & command namespace contract
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (repository root)

```text
hermes-plugin-wright/
├── pyproject.toml       # Build system & package metadata
├── plugin.yaml          # Hermes plugin manifest
├── __init__.py          # Entry point register(ctx) implementation
├── tests/
│   └── conftest.py      # Pytest setup
└── README.md            # Usage and structure overview
```

**Structure Decision**: A standalone, standard Python package directory structure at `/hermes-plugin-wright/`, enabling both PyPI distribution and local editable installation.

## Complexity Tracking

No violations of the project constitution or unnecessary complexities are introduced in this plan.
