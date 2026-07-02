# Contract: Wright Gateway Protocol

## Purpose

The Wright gateway is the generic agent-facing MCP gateway. Hermes and future OpenClaw integrations consume the same MCP gateway protocol through provider-specific profiles.

## Generic MCP Protocol Surface

The Wright gateway must support:

- `initialize`
- `notifications/initialized`
- `ping`
- `tools/list`
- `tools/call`
- `notifications/tools/list_changed`

## Gateway Profile Fields

```text
profile_name
server_name
command
args
supports_tool_list_changed
workspace_context_writer
```

## Naming Rules

- Use "Wright gateway" for generic architecture.
- Keep `wrightgateway` only as a Hermes-compatible MCP server key where required by existing Hermes config.
- Do not use `.hermes.md` as the generic workspace context contract.

## Hermes Compatibility

Hermes may continue to receive:

```text
mcp_servers.wrightgateway.command = uv
mcp_servers.wrightgateway.args = run --project <repo> python -m tool_registry.gateway
terminal.cwd = <repo>
```

Hermes-specific config file paths stay behind the Hermes gateway sync adapter.

## OpenClaw Seam

OpenClaw work in this feature is limited to contract/stub coverage. The stub must prove the generic gateway contract does not require Hermes config paths.

## Required Tests

- Fake gateway adapter contract tests.
- Hermes gateway profile compatibility tests.
- Future-runtime stub test proving no Hermes paths are touched.
- Wright gateway list/call behavior remains compatible with existing API gateway tests.

