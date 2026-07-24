# Solid Edge creation through Hermes

Wright supports a bounded Solid Edge creation workflow when Hermes owns the
local MCP connection. The goal is to create a new artifact quickly without
inspecting or altering a document that was already open.

## Runtime configuration

Set `WRIGHT_API_MCP_AUTOSTART=0` for Hermes-driven sessions. This leaves MCP
subprocess ownership with Hermes and makes Wright's API status and workspace
routes passive. Only one local component should start SolidEdgeMCP.

Set the same `WRIGHT_API_TOKEN` for Wright and the Hermes bridge when Wright
authentication is enforced. Bridge requests include the bearer token but do
not log it.

SolidEdgeMCP must allow the active workspace output directory through
`CADMCP_SOLID_EDGE_ALLOWED_ROOTS`.

## Creation contract

For a new rectangular part, the agent should call
`cad.create_part_from_recipe` once with:

- `providerId=solid_edge`;
- an absolute `outputPath` under the active workspace;
- `mode=commit`, `units=mm`, and `document=new`;
- a centered rectangle on the top plane;
- an extrusion using `direction=positive_normal`;
- `visible=true` and `closeAfterSave=false`.

The creation projection excludes document, feature, face, dimension, variable,
measurement, capability, and semantic inventory tools. If the creation call
fails, the agent reports the provider error and stops instead of inspecting an
existing document or trying unrelated recovery.

## Workspace changes

When the active Wright workspace changes, Wright updates Hermes' MCP binding.
If the binding changed, the next chat waits for a bounded Hermes gateway
restart and health check before beginning. A failure is returned as an
actionable service-unavailable error rather than silently using a stale
workspace.

## Progress behavior

Chat begins with a planning status. While work continues, Wright emits elapsed
heartbeats at no more than ten-second intervals. Solid Edge operations are
shown with user-facing labels such as "Creating a new Solid Edge part" instead
of only exposing an internal MCP tool name.

See [Solid Edge diagnostics](../operations/solid-edge-diagnostics.md) for
triage and recovery.
