# Implementation Plan: Wright Slash Commands

**Branch**: `030-wright-slash-commands` | **Date**: 2026-06-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/030-wright-slash-commands/spec.md`

## Summary

Implement the `/wright` slash command interface within the `hermes-plugin-wright` plugin to control and monitor the Wright API gateway and explore/install engineering tools from the catalog.

## Technical Context

**Language/Version**: Python >= 3.11

**Primary Dependencies**: `httpx`, `pyyaml`, `pydantic`, `structlog`

**Storage**: Local JSON files (Hermes config) and text/log files (PID, log outputs)

**Testing**: `pytest` and `pytest-asyncio`, utilizing `unittest.mock` for filesystem, process spawning, and browser opening checks.

**Target Platform**: Linux (appliance and development environments)

**Project Type**: Hermes Plugin module

**Performance Goals**: Sub-second dispatch times; async non-blocking execution of background subprocesses.

**Constraints**: Zero exposure of plain text credentials in diagnostic/status outputs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: Command routes will be decoupled from core application logic and call the client API bridge exclusively. (Pass)
- **Zero-Server Databases**: The slash commands do not introduce database dependencies, checking the active SQLite files in-place during diagnostics. (Pass)
- **Structured Logging**: Commands use `structlog` for command dispatch trace logs. (Pass)

## Project Structure

### Documentation (this feature)

```text
specs/030-wright-slash-commands/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    └── command_contracts.md
```

### Source Code (repository root)

```text
hermes-plugin-wright/
├── __init__.py          # Modified: registers slash command callback
├── commands.py          # [NEW] Implements all subcommand dispatches and formatting
├── bridge.py            # Existing API client bridge
├── pyproject.toml       # Modified: force-include commands.py and test_commands.py
└── tests/
    └── test_commands.py # [NEW] Test suite for commands routing and execution
```

**Structure Decision**: Add `commands.py` and `tests/test_commands.py` directly to the `hermes-plugin-wright` module.

---

## Proposed Changes

### hermes-plugin-wright

#### [MODIFY] [__init__.py](file:///home/burhop/repos/wright/hermes-plugin-wright/__init__.py)
- Import `register_commands` from `.commands`.
- Wire `register(ctx)` to load catalog and register the `/wright` command router.

#### [NEW] [commands.py](file:///home/burhop/repos/wright/hermes-plugin-wright/commands.py)
- Export `register_commands(ctx, catalog)`.
- Parse arguments for start, stop, open, doctor, status, catalog, info, and install.
- Implement `/wright start`:
  - Check health via bridge.
  - Auto-detect repo path.
  - Verify if React assets are stale (scan `apps/web/src` modification times vs `apps/web/dist` newest file).
  - Launch `uvicorn` as a detached process, redirecting output to `repo/tmp/wright-api.log` and writing `repo/tmp/wright-api.pid`.
  - Poll API health up to 15s.
  - Open URL in browser via `webbrowser.open()`.
- Implement `/wright stop`:
  - Read PID from file.
  - Propagate `SIGTERM`.
  - Poll for exit up to 5s.
  - Clean up PID file.
- Implement `/wright open`:
  - Check health and open browser or warn user.
- Implement `/wright doctor`:
  - Check repository, uvicorn server, database, secret file permissions, active credential definitions, and server count.
- Implement `/wright status`:
  - Dashboard output formatting for active workspace, active tools, and credential status list.
- Implement `/wright catalog`, `/wright info`, `/wright install`:
  - Query loader instances and bridge calls to list, query, show info, and trigger installation of cataloged items.

#### [MODIFY] [pyproject.toml](file:///home/burhop/repos/wright/hermes-plugin-wright/pyproject.toml)
- Add `"commands.py" = "hermes_plugin_wright/commands.py"` to Hatch force-include.

#### [NEW] [test_commands.py](file:///home/burhop/repos/wright/hermes-plugin-wright/tests/test_commands.py)
- Verify subcommand routing callback.
- Mock subprocess execution, PID reads/writes, signal propagation, and API client calls.
- Assert stdout/stderr formatting matches layout contracts.

---

## Verification Plan

### Automated Tests
- Run complete test suite:
  ```bash
  pytest hermes-plugin-wright
  ```

### Manual Verification
- Load python interpreter and import the commands registration method to verify import path resolution.
- Verify entry point loads and runs.
  ```bash
  python hermes-plugin-wright/verify_plugin.py
  ```
