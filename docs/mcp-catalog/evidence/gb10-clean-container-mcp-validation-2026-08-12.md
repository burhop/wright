# GB10 Clean Container MCP Validation - 2026-08-12

Environment:

- Host: NVIDIA GB10 Linux ARM64 (`aarch64`)
- Container image: `wright:standard-linux-arm64`
- Container OS: Debian GNU/Linux 13 (`trixie`)
- Container architecture: `aarch64`
- Container Python: 3.13.13
- Container uv: `/usr/local/bin/uv`

This evidence used disposable containers and installed only the selected MCP
server dependencies inside each container. It is still a partial validation
record because Wright/Hermes gateway proxy probes were not run.

## Ansys PyFluent MCP

Catalog ID: `ansys-fluent-mcp`

Command:

```bash
docker run --rm --entrypoint sh wright:standard-linux-arm64 -lc \
  'python3 <inline-probe> uv tool run --from ansys-fluent-mcp ansys-fluent-mcp'
```

Result: partial pass.

Protocol evidence:

- `initialize` passed.
- `notifications/initialized` was sent.
- `tools/list` passed.
- `session_status` passed.

Observed server info:

```json
{
  "name": "ansys-fluent-mcp",
  "version": "3.4.7"
}
```

Observed tools:

- `session_status`
- `connect`
- `disconnect`
- `list_named_objects`
- `find_named_object`
- `select_named_objects`
- `find_api`
- `get_state`
- `get_targeted_context`
- `get_help`
- `solver_status`
- `run_code`
- `validate_code`
- `screenshot`
- `manage_fluent`
- `summarize_setup`
- `simulation_report`
- `mesh_quality`
- `list_fields`
- `compare_files`
- `probe_path`
- `get_active_status`
- `get_allowed_values`
- `describe_named_object_template`
- `describe_path`

Safe backend/status probe:

```json
{
  "leaf": "solve",
  "connected": false,
  "backend": "Solve (PyFluent)",
  "backend_kind": "pyfluent",
  "endpoint": null,
  "capabilities": [],
  "notes": []
}
```

Remaining:

- Validate through Wright/Hermes gateway.
- Validate live Fluent attach/launch on a licensed local or remote Fluent
  session before enabling solver operations.

## NVIDIA Elements MCP

Catalog ID: `nvidia-elements-mcp`

Selected-server dependency install:

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends nodejs npm ca-certificates
```

Command:

```bash
npx -y @nvidia-elements/cli@2.1.10 mcp
```

Result: partial pass.

Runtime:

- Node: `v20.19.2`
- npm: `9.2.0`

Protocol evidence:

- `initialize` passed.
- `notifications/initialized` was sent.
- `tools/list` passed.
- `skills_list` passed.

Observed server info:

```json
{
  "name": "io.github.NVIDIA/elements",
  "version": "2.1.10",
  "description": "NVIDIA Elements UI Design System (nve-*), custom element schemas, APIs and examples. Use the \"elements\" skill for more guidance if available."
}
```

Observed tools:

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

Safe read-only probe:

- `skills_list` returned NVIDIA Elements design-system skill metadata.

Remaining:

- Validate through Wright/Hermes gateway before marking the catalog entry fully
  passed.
