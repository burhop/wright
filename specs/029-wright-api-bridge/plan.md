# Implementation Plan: Wright API Bridge Client

**Branch**: `029-wright-api-bridge` | **Date**: 2026-06-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from [spec.md](spec.md)

## Summary

The goal of this feature is to implement the API client bridge in `bridge.py` supporting communication between the Hermes plugin commands and the local FastAPI server. We will:
1. Export base address constants `WRIGHT_API_BASE` and `WRIGHT_UI_URL`.
2. Code path detection parsing `wrightgateway` args inside local YAML config profiles.
3. Code async methods using `httpx.AsyncClient` with a 30-second timeout, wrapping HTTP calls in safety boundaries that serialize errors instead of raising crashes.
4. Implement a comprehensive suite of unit tests in `test_bridge.py` mocking network routing via `respx` or similar tools.

## Technical Context

**Language/Version**: Python >= 3.11

**Primary Dependencies**: `httpx>=0.27`, `pyyaml>=6.0`, `pydantic>=2.0`

**Storage**: Local YAML profile parsing

**Testing**: `pytest`, `pytest-asyncio`, `respx` (or standard unittest mocks)

**Target Platform**: Linux server

**Project Type**: library/plugin

**Performance Goals**: File argument parsing in < 2ms; network timeouts strictly enforced at 30 seconds.

**Constraints**: Must never log or expose raw credentials. All exceptions must be handled gracefully returning structured error results.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

* **Structured Logging Compliance**: Warnings or failures from connection timeouts are logged structured without exposing payloads. Verified.
* **Offline-First Mandate**: The client communicates strictly with localhost (`127.0.0.1`), requiring no external endpoints. Verified.
* **Architecture Integrity**: No tool process logic resides in this client; all operations delegate directly to the FastAPI endpoints. Verified.

## Project Structure

### Documentation (this feature)

```text
specs/029-wright-api-bridge/
├── plan.md              # This file
├── research.md          # Technology decisions
├── data-model.md        # API models mapping
├── quickstart.md        # Quickstart invocation guide
├── contracts/
│   └── bridge_interface.md  # Client class contracts
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (repository root)

```text
hermes-plugin-wright/
├── pyproject.toml       # Updated to include respx (or test deps)
├── plugin.yaml
├── __init__.py
├── catalog.yaml
├── schemas.py
├── catalog.py
├── bridge.py            # [NEW] Exposes get_mcp_servers, check_api_health, etc.
├── tests/
│   ├── conftest.py
│   ├── test_catalog.py
│   └── test_bridge.py   # [NEW] Network mock tests
└── README.md
```

**Structure Decision**: Exposing all methods under the root package namespace as specified in `docs/wright-hermes-plugin-plan.md` Section 5.1.

## Complexity Tracking

No violations of project constitution are introduced. Network configurations use the default localhost values.
