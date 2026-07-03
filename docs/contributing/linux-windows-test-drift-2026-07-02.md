# Linux/Windows Test Drift Inventory - 2026-07-02

This inventory captures the problems observed after pulling `dev` to commit
`7f3f741` on Linux and running the current local quality/test gates. The goal is
to make the "fresh clone/pull should work" gaps explicit, especially where a
state produced on Windows does not reproduce cleanly on Linux.

## Executive Summary

The core workspace code is mostly healthy when each suite is invoked in the
context it currently expects:

- Frontend Vitest: 69 passed.
- Main workspace Python tests: 291 passed.
- Hermes plugin tests: 79 passed.
- FreeCAD MCP tests: 94 passed, with 2 integration tests deselected by marker.

## Remediation Applied

Follow-up fixes now make a fresh root checkout deterministic:

- Root Ruff, Ruff format, and MyPy warning checks use explicit Wright workspace paths instead of the broad `packages/` glob, so `packages/freecad_mcp` is opt-in.
- Root pytest has explicit `testpaths`, so it no longer discovers package-local or external tests outside the root environment.
- `make test` and `make check` still run Hermes plugin tests, but through `uv run --package hermes-plugin-wright`, matching that package layout.
- `make test-external-freecad` runs the external FreeCAD MCP suite in its own project context.
- Playwright tests tagged `@live` are excluded by default; set `PLAYWRIGHT_INCLUDE_LIVE=1` after starting the backend to include them.
- The mocked navigation Playwright test now stubs the workspace config/tools endpoints it exercises.
- CI Python quality uses the same explicit Wright workspace paths, and CI Playwright opts into `@live` because it starts the backend.

The original problems were in the glue around those suites:

- The documented one-command gate, `make check`, fails immediately on Ruff
  because it includes `packages/freecad_mcp`, which has lint violations.
- Root-level `uv run pytest` fails collection because it discovers packages
  that are not importable from the root workspace environment.
- Playwright UI integration tests assume a backend at `127.0.0.1:8000` for at
  least some flows; without that backend, 3 tests fail with Vite proxy 502s.
- `packages/freecad_mcp` needed a package-local dependency sync before tests
  could run, because it is not part of the root `uv` workspace.
- A FreeCAD helper script contains Windows-specific absolute paths, which is a
  clear portability hazard.

## Problem 1: `make check` Fails Before Running Tests

Command:

```bash
make check
```

Result:

```text
uv run ruff check apps/api/ packages/
Found 15 errors.
make: *** [Makefile:119: check] Error 1
```

Primary files:

- `packages/freecad_mcp/scripts/gui_step_export.py`
- `packages/freecad_mcp/src/freecad_mcp/fc_bridge.py`
- `packages/freecad_mcp/src/freecad_mcp/server.py`
- `packages/freecad_mcp/tests/test_cfd_configs.py`

Observed Ruff categories:

- `E401`: multiple imports on one line.
- `I001`: import block unsorted/unformatted.
- `F401`: unused imports.
- `E402`: imports after `sys.path` mutation.
- `RUF005`: list concatenation where unpacking is preferred.
- `E741`: ambiguous variable name `l`.
- `RUF012`: mutable class attributes not annotated as `ClassVar`.

Linux/Windows angle:

This is less about OS behavior and more about gate drift. `make check` lints
`packages/`, but `packages/freecad_mcp` appears to have been added without
being made compliant with the root Ruff gate. If this passed on Windows, it was
likely because the exact root gate was not run, Ruff was not installed/run the
same way, or `freecad_mcp` was tested in isolation.

Recommended prevention:

- Decide whether `packages/freecad_mcp` is governed by the root `make check`.
- If yes, fix the Ruff findings and add the root gate to CI on Linux and
  Windows.
- If no, narrow the root Ruff paths or give `freecad_mcp` a separate Makefile
  target with explicit documentation.

## Problem 2: Root `uv run pytest` Fails Collection

Command:

```bash
uv run pytest
```

Result:

```text
collected 293 items / 6 errors
ModuleNotFoundError: No module named 'hermes_plugin_wright'
ModuleNotFoundError: No module named 'freecad_mcp'
```

Failing collection paths:

- `hermes-plugin-wright/tests/test_bridge.py`
- `hermes-plugin-wright/tests/test_catalog.py`
- `hermes-plugin-wright/tests/test_commands.py`
- `packages/freecad_mcp/tests/test_cfd_configs.py`
- `packages/freecad_mcp/tests/test_fluidx3d_integration.py`
- `packages/freecad_mcp/tests/test_smoke.py`

What passed when invoked with explicit workspace paths:

```bash
uv run pytest apps/api packages/agent_adapters packages/core \
  packages/data_vault packages/tool_registry packages/workspace_service tests
```

Result:

```text
291 passed, 1 warning
```

What passed in package context:

```bash
uv run --package hermes-plugin-wright pytest hermes-plugin-wright/tests
```

Result:

```text
79 passed
```

```bash
cd packages/freecad_mcp
uv run pytest
```

Result after dependency sync:

```text
94 passed, 2 deselected
```

Root cause:

The root `pyproject.toml` declares a `uv` workspace with these members:

- `apps/api`
- `hermes-plugin-wright`
- `packages/core`
- `packages/agent_adapters`
- `packages/tool_registry`
- `packages/data_vault`
- `packages/workspace_service`

`packages/freecad_mcp` has its own `pyproject.toml`, local pytest config, and
`pythonpath = ["src"]`, but it is not a root workspace member. Root pytest
discovers its tests anyway, without applying the package-local project context.

`hermes-plugin-wright` is a workspace member, but its source layout is unusual:
root-level files are force-included into a built wheel package named
`hermes_plugin_wright`. Its tests import the built package name, so they pass
when run through `uv --package hermes-plugin-wright`, but fail under plain root
test discovery.

Linux/Windows angle:

This is very likely to vary by local environment. A Windows machine that already
had editable installs or local `PYTHONPATH` settings could pass while a clean
Linux checkout fails. That is exactly the reproducibility risk.

Recommended prevention:

- Make root `uv run pytest` deterministic by either:
  - adding root pytest `testpaths` that exclude package-local projects, or
  - making all discovered Python packages root workspace members and installable
    before collection.
- Avoid relying on ambient editable installs or shell-specific `PYTHONPATH`.
- Add a documented `make test-python` command that matches CI exactly.

## Problem 3: `packages/freecad_mcp` Dependencies Are Not Synced By Root Setup

Initial command:

```bash
cd packages/freecad_mcp
uv run pytest
```

Initial result:

```text
ModuleNotFoundError: No module named 'fastmcp'
```

Fix used:

```bash
uv sync --project packages/freecad_mcp --extra dev
```

After sync:

```text
94 passed, 2 deselected
```

Root cause:

`packages/freecad_mcp` is a standalone Python project with dependencies such as
`fastmcp==3.2.0`. Since it is not in the root `uv` workspace, root dependency
setup does not install its runtime/test dependencies.

Linux/Windows angle:

This can easily pass on a Windows development machine if `fastmcp` was installed
globally, in an activated environment, or as part of prior manual work. A clean
Linux environment exposes the missing setup step.

Recommended prevention:

- Either add `packages/freecad_mcp` to the root workspace, or document and
  automate its separate sync/test flow.
- Add CI coverage for a clean Linux environment and a clean Windows environment.
- Keep package-specific tests from being collected by root pytest unless root
  setup installs their dependencies.

## Problem 4: Windows-Specific Absolute Paths Checked Into FreeCAD Script

File:

```text
packages/freecad_mcp/scripts/gui_step_export.py
```

Examples:

```python
fc_bin = r"C:\Users\sandr\AppData\Local\Temp\freecad_extracted\FreeCAD_1.1.1-Windows-x86_64-py311\bin"
STEP = r"C:\Users\sandr\AppData\Local\Temp\raspbot_v2_step.STEP"
OUT = r"D:\Dev\repos\yahboom-mcp\webapp\public\assets\meshes"
```

Root cause:

The script appears to be a local Windows helper/prototype committed directly.
It mutates `sys.path` to point at a local extracted FreeCAD installation and
uses user-machine-specific input/output paths.

Linux/Windows angle:

This is a direct cross-platform break. It cannot run on Linux as written, and it
will not run on most Windows machines either unless they have the same username,
temp extraction path, drive layout, and repo path.

Recommended prevention:

- Convert the script to accept CLI arguments or environment variables for
  FreeCAD path, STEP path, and output path.
- Use `pathlib.Path`, avoid hard-coded drive letters, and document required
  FreeCAD discovery behavior.
- If this is only an experiment, move it under a clearly ignored scratch area or
  remove it from the root quality gate.

## Problem 5: Playwright UI Integration Needs Backend Or Better Mock Isolation

Command:

```bash
npx playwright test
```

Result:

```text
35 passed, 3 failed
```

Failing tests:

- `tests/ui-integration/dashboard-real.spec.ts`
- `tests/ui-integration/mcp-directory.spec.ts`
- `tests/ui-integration/navigation-redesign.spec.ts`

Dominant failure signal:

```text
Vite http proxy error: /api/...
Error: connect ECONNREFUSED 127.0.0.1:8000
502 Bad Gateway
```

Relevant config:

```ts
webServer: process.env.PLAYWRIGHT_BASE_URL
  ? undefined
  : {
      command: "npm run dev --prefix apps/web",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
    },
```

Root cause:

The Playwright config starts only the frontend dev server when
`PLAYWRIGHT_BASE_URL` is not set. Some tests are mocked enough to pass, but at
least three flows make real API calls through Vite's proxy to
`127.0.0.1:8000`. No backend was running during the local run.

Linux/Windows angle:

This is another environment-state problem. A Windows workstation with the API
already running on port 8000 can pass, while a clean Linux checkout fails. The
test command does not encode all services it requires.

Recommended prevention:

- Split mocked UI tests from live-backend UI tests.
- Make the default `npx playwright test` fully mocked, or make it start the API
  as part of `webServer`.
- Require `PLAYWRIGHT_BASE_URL` for live-backend tests and document the backend
  startup command.
- Add CI jobs that run both mocked and live flows with explicit service setup.

## Problem 6: Tooling/Sandbox Friction On Linux

Several read-only commands initially failed in the managed sandbox with:

```text
bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted
```

The commands succeeded when rerun outside the sandbox. This is not a repo code
failure, but it is part of the Linux developer experience observed during this
run.

**Root Cause**:
On Ubuntu 24.04+ (and newer kernels), AppArmor restricts unprivileged user namespaces by default (`kernel.apparmor_restrict_unprivileged_userns = 1`). Bubblewrap (`bwrap`) needs `net_admin` and `setpcap` to configure the loopback interface inside its network namespace. The kernel AppArmor profile `unprivileged_userns` denies these capabilities, causing `bwrap` setup to abort with the `Failed RTM_NEWADDR` error.

**Resolution**:
Define a custom AppArmor profile for `bwrap` to permit unprivileged user namespaces. Create `/etc/apparmor.d/bwrap-userns-restrict` with:

```text
abi <abi/4.0>,
include <tunables/global>

profile bwrap /usr/bin/bwrap flags=(unconfined) {
  userns,

  # Site-specific additions and overrides. See local/README for details.
  include if exists <local/bwrap>
}
```

Then reload the AppArmor profiles:
```bash
sudo apparmor_parser -r /etc/apparmor.d/bwrap-userns-restrict
```

Recommended prevention:

- Keep project test commands independent of sandbox-specific assumptions.
- If using Codex or another sandboxed workflow as part of validation, document
  which commands need elevated/network-capable execution.
- Maintain setup documentation for Linux developer environments pointing to the AppArmor profile fix.

## Suggested Clean-Gate Shape

To prevent this class of drift, define one exact command for each tier and run
the same commands in Linux and Windows CI:

```bash
make check-core
make test-python-packages
make test-frontend
make test-playwright-mocked
make test-playwright-live
```

Concrete behavior:

- `check-core`: lint/typecheck only packages governed by the root workspace.
- `test-python-packages`: either install every package and run all tests, or run
  each package in its own project context.
- `test-frontend`: `npm run test --workspace=apps/web`.
- `test-playwright-mocked`: no backend required.
- `test-playwright-live`: starts or requires backend explicitly.

The important invariant is that a fresh checkout should not rely on global
Python packages, already-running backend services, Windows-only paths, or
machine-specific environment variables.
