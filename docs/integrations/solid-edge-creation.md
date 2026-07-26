# Solid Edge creation through Hermes

SolidEdgeMCP remains an independently installed and versioned MCP server.
Wright reaches it through the same gateway, lifecycle, policy, discovery, and
progress contracts used for every other MCP server. Wright core contains no
Solid Edge tool allowlist, recipe prompt, workspace injection branch, or
progress-label mapping.

## Runtime configuration

Set `WRIGHT_API_MCP_AUTOSTART=0` for Hermes-driven sessions so API status
polling remains passive. Configure Hermes with `wrightgateway`; do not also
configure the same child server directly in Hermes. The Wright gateway's
generic lifecycle is the single owner of a Wright-managed child process.

Set the same `WRIGHT_API_TOKEN` for Wright and the Hermes bridge when Wright
authentication is enforced. Bridge requests include the bearer token but do
not log it.

For the current external server contract, place its allowed-root variable in
the ordinary trusted server record:

```yaml
launch_env:
  CADMCP_SOLID_EDGE_ALLOWED_ROOTS: "{workspace.path}"
```

Wright renders the authenticated canonical workspace exactly as it does for
any other server. The variable name is server-owned configuration data, not
Wright runtime logic.

## Creation contract

One representative external-server workflow creates a rectangular part with
`cad.create_part_from_recipe` and:

- `providerId=solid_edge`;
- an absolute `outputPath` under the active workspace;
- `mode=commit`, `units=mm`, and `document=new`;
- a centered rectangle on the top plane;
- an extrusion using `direction=positive_normal`;
- `visible=true` and `closeAfterSave=false`.

Wright no longer filters the server's advertised tool set or injects this
recipe into every agent request. Tool selection and modeling semantics come
from the server's advertised descriptions, schemas, annotations, structured
results, and optional server-specific operator guidance.

## Workspace changes

When the active Wright workspace changes, Wright updates Hermes' MCP binding.
If the binding changed, the next chat waits for a bounded Hermes gateway
restart and health check before beginning. A failure is returned as an
actionable service-unavailable error rather than silently using a stale
workspace.

## Progress behavior

Chat begins with a generic planning status. Wright relays standard MCP progress
tokens and server-authored messages when the child provides them, and emits
explicitly marked generic elapsed heartbeats while work continues. Titles fall
back to advertised tool metadata; Wright does not infer application state from
a tool name.

## Migration and rollback

1. Add `launch_env` to the trusted server record while retaining the existing
   command, credentials, ownership, and timeouts.
2. Rebind the workspace and verify discovery plus one explicit output under
   that workspace.
3. Remove any duplicate direct Hermes child-server entry after confirming
   `wrightgateway` owns the call path.
4. When a newer external server offers a neutral CLI option, replace the
   environment entry with that command-array option; no Wright code change is
   needed.

To roll back, restore the previous server record and compatible Wright build.
The additive `launch_env` and tool-metadata database columns are harmless to
older records and do not require destructive schema reversal.

See [Solid Edge diagnostics](../operations/solid-edge-diagnostics.md) for
triage and recovery.
