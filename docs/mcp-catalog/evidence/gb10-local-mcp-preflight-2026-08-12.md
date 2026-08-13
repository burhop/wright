# GB10 Local MCP Preflight Evidence - 2026-08-12

Environment:

- Host: NVIDIA GB10 Linux ARM64 (`aarch64`)
- Driver: NVIDIA 590.48.01, CUDA 13.1
- Docker: 27.5.1 with NVIDIA runtime available
- Node/npm: Node 22.22.0, npm 11.10.1
- Python tooling: uv 0.9.17, Poetry 2.4.1

This is local-host preflight evidence, not a clean-container pass. Do not mark
catalog entries fully validated until the clean-container process in
`docs/mcp-catalog/mcp-server-testing-process.md` runs and records gateway
evidence where required.

## NVIDIA Omniverse USD Code MCP

- Source: `https://github.com/NVIDIA-Omniverse/kit-usd-agents`
- Commit: `c7ac8c6931b40bc48de84e8d808ed89d51d924da`
- Local source path: `.local-run/mcp/src/kit-usd-agents`
- Result: local build preflight passed.

Steps:

- Installed `git-lfs` on the host.
- Cloned the source repository.
- Fetched Git LFS data needed by the USD Code MCP.
- Ran `./build-wheels.sh usd` from `source/mcp`.

Artifacts:

- `source/aiq/usd_code_fns/dist/usd_code_aiq-0.3.0-py3-none-any.whl`
  (`398798247` bytes)
- `source/mcp/usd_code_mcp/dist/usd_code_mcp-1.0.0-py3-none-any.whl`
  (`10138` bytes)

Remaining:

- Docker image build/startup not yet run.
- MCP `initialize`, `tools/list`, and read-only USD search calls not yet run.
- Recommended NVIDIA-hosted deployment needs `NVIDIA_API_KEY`.

## NVIDIA Elements MCP

- Package: `@nvidia-elements/cli@2.1.10`
- Command: `npx -y @nvidia-elements/cli@2.1.10 mcp`
- Result: local protocol preflight passed.

Evidence:

- `--help` returned the `nve mcp` command help.
- Wright `StdioRunner` initialized the MCP server.
- `tools/list` returned 18 tools.
- Read-only `skills_list` returned Elements design-system skill metadata.

Tool names observed:

- `api_list`
- `api_get`
- `api_template_validate`
- `api_imports_get`
- `api_tokens_list`
- `api_icons_list`
- `cli_upgrade`
- `examples_list`
- `examples_get`
- `examples_render`
- `project_create`
- `project_setup`
- `project_validate`
- `packages_list`
- `packages_get`
- `packages_changelogs_get`
- `skills_list`
- `skills_get`

Remaining:

- Clean Linux ARM64 container validation was later recorded in
  `docs/mcp-catalog/evidence/gb10-clean-container-mcp-validation-2026-08-12.md`.
- Gateway proxy validation.

## Ansys PyFluent MCP

- Package: `ansys-fluent-mcp`
- Command: `uvx --from ansys-fluent-mcp ansys-fluent-mcp`
- Result: local protocol preflight passed with expected missing-live-session
  boundary.

Evidence:

- `--help` printed options for `--transport`, `--host`, `--port`, `--backend`,
  and `--log-level`.
- Wright `StdioRunner` initialized the MCP server.
- `tools/list` returned 25 tools.
- Read-only `session_status` returned `connected:false`,
  `backend_kind:"pyfluent"`, and no error.

Remaining:

- Clean-container protocol/status validation was later recorded in
  `docs/mcp-catalog/evidence/gb10-clean-container-mcp-validation-2026-08-12.md`.
- Live Ansys Fluent validation on a licensed local or remote Fluent session.

## Ansys MCP Server Community

- Package: `ansys-mcp-server`
- Result: startup failed before MCP initialization.

Observed on Python 3.13 and Python 3.12:

```text
ImportError: cannot import name 'InitializationCapabilities' from 'mcp.server.models'
```

Remaining:

- Upstream dependency/API fix or a confirmed working MCP SDK pin.

## COMSOL Multiphysics MCP - Suzy-Sa

- Source: `https://github.com/Suzy-Sa/COMSOL-Multiphysics-MCP`
- Commit: `3735fb3276ec6ad44163a55763dad45932367ffe`
- Result: package tests passed, MCP startup failed.

Evidence:

- `uv run pytest -q` passed 76 tests.
- MCP startup failed before initialization:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

Remaining:

- Upstream dependency/API fix or MCP SDK pin.
- Licensed COMSOL/mph validation after stdio startup works.

## COMSOL MCP Server - wjc9011

- Source: `https://github.com/wjc9011/COMSOL_Multiphysics_MCP`
- Commit: `99172f8f43c6753c2442c406cd5c6055ea8c5bef`
- Result: install/test probe intentionally stopped.

Observed:

- Repository clone includes many COMSOL PDF manuals, `.mph` models, lock files,
  logs, and generated artifacts.
- Dependency resolution immediately began downloading a large
  `sentence-transformers`/PyTorch/CUDA stack, including multiple NVIDIA CUDA
  Python packages.

Remaining:

- Do not include in a redistributed image without a license/content review and a
  slim install path.
- Validate only from source in a disposable environment.
