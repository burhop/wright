# Solid Edge diagnostics

Use this sequence when a Hermes/Wright Solid Edge request is slow or fails.

## Check ownership first

For Hermes-driven sessions, confirm `WRIGHT_API_MCP_AUTOSTART=0` and that Hermes
is configured with `wrightgateway`. Do not configure a second direct child
entry for the same executable. A Wright-managed child should have one process
owned by the gateway lifecycle.

## Interpret progress

- **Planning request** means the agent has not reported a child tool call yet.
- A server-authored message is relayed as-is with its advertised server, tool,
  title, progress, total, and correlation fields when available.
- A tool-name fallback means the server supplied no title or message; it does
  not prove what the desktop application is doing.
- Repeated elapsed messages marked as heartbeats indicate only that the turn is
  still alive.

After a terminal tool event, later heartbeats return to "Working on request"
and do not claim that the completed operation is still active.

## Workspace and authentication failures

- A workspace rebind failure returns HTTP 503 and should be resolved before
  retrying the creation request.
- Protected Wright API calls require the Hermes bridge to receive
  `WRIGHT_API_TOKEN`.
- Output paths must be absolute, under the active workspace, and included in
  `CADMCP_SOLID_EDGE_ALLOWED_ROOTS`.
- An `invalid_launch_template` error means the trusted record contains an
  unsupported placeholder, uses a placeholder in a string command, or lacks a
  bound workspace. Only `{workspace.path}` is supported.

## Safe recovery

Do not inspect, save, close, or modify a document that was already open merely
to recover a failed creation request. Correct the reported authentication,
workspace, path, recipe, or provider error and then submit a fresh
new-document request.

Gateway audit and subprocess logs remain redacted and provider-neutral. For a
rollback, restore the prior server record and matching Wright build; do not
delete the additive database columns. A live Windows compatibility smoke is
optional and must be recorded as skipped when the matching external server or
desktop application is unavailable.
