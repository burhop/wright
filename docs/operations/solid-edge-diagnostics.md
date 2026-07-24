# Solid Edge diagnostics

Use this sequence when a Hermes/Wright Solid Edge request is slow or fails.

## Check ownership first

For Hermes-driven sessions, confirm `WRIGHT_API_MCP_AUTOSTART=0`. Wright status
polling must not start another SolidEdgeMCP process. A single Hermes-owned
process should serve the session.

## Interpret progress

- **Planning and preparing** means the agent has not begun a Solid Edge tool
  call yet.
- **Creating or building the Solid Edge design** means a provider operation is
  active.
- **Exporting or capturing views** identifies post-creation output work.
- Repeated elapsed messages are heartbeats and indicate that the turn is still
  alive.

If a completed tool is followed by a long final response, the heartbeat keeps
the completed operation label and does not claim that Solid Edge is still
creating geometry.

## Workspace and authentication failures

- A workspace rebind failure returns HTTP 503 and should be resolved before
  retrying the creation request.
- Protected Wright API calls require the Hermes bridge to receive
  `WRIGHT_API_TOKEN`.
- Output paths must be absolute, under the active workspace, and included in
  `CADMCP_SOLID_EDGE_ALLOWED_ROOTS`.

## Safe recovery

Do not inspect, save, close, or modify a document that was already open merely
to recover a failed creation request. Correct the reported authentication,
workspace, path, recipe, or provider error and then submit a fresh
new-document request.

The current branch preserves existing redacted gateway audit and subprocess
logs. The separately proposed phase-attribution diagnostics service and
percentage-based 20-trial benchmark are follow-up work and are not claimed by
this release.
