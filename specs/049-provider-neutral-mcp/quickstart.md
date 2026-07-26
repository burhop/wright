# Quickstart: Provider-Neutral MCP Integration

## 1. Configure two synthetic servers

Create two trusted local STDIO server records with unrelated names. Give both the same command-array workspace binding:

```text
python synthetic_mcp.py --allowed-root {workspace.path}
```

Use a second case with the placeholder in `launch_env`. Include workspace paths containing spaces and shell-significant characters.

Expected result: each subprocess receives the exact canonical path as one literal value; an unbound server receives no changes.

## 2. Verify discovery neutrality

Have both servers advertise the same tool title, input/output schemas, and annotations under different server IDs. Activate each for a workspace and list gateway tools.

Expected result: both tools appear, retain their advertised metadata, and differ only by collision-safe gateway identity/provenance.

## 3. Verify progress relay

Call a synthetic long-running tool through the Wright gateway with a progress token. Emit several standard child progress notifications, then return structured content.

Expected result: the outer client receives monotonic progress on its original token, sees server-authored messages, and receives no update after the final result.

Repeat with malformed, decreasing, unknown-token, cancellation, and timeout cases.

## 4. Verify chat progress

Feed generic Hermes progress events with and without titles/messages into the agent stream.

Expected result: Wright preserves supplied messages, produces a generic fallback when missing, correlates events to one session, emits generic heartbeats, and closes terminal state once.

## 5. Verify the migration boundary

Search runtime source for provider-specific Solid Edge identifiers and tool names. Ordinary documentation or catalog data may mention the integration; runtime branches and prompts may not.

Run required tests without installing or launching Solid Edge or checking out SolidEdgeMCP.

## 6. Optional Windows compatibility smoke

On a prepared Windows workstation, configure the external server's current allowed-root environment setting through `launch_env` using `{workspace.path}`. Invoke its advertised high-level creation tool with an explicit output path under the selected workspace.

Current compatibility record:

```yaml
command:
  - C:\path\to\SolidEdgeMCP.exe
launch_env:
  CADMCP_SOLID_EDGE_ALLOWED_ROOTS: "{workspace.path}"
```

Expected result: the exact file exists, the call reports success, no blocking save dialog appears, and Wright uses the same launch/progress path as the synthetic servers.

Record any missing external contract capability as an external compatibility limitation, not as a reason to restore provider-specific Wright code.

Rollback restores the previous trusted server record and compatible Wright
build. The additive database columns remain in place and require no data loss.

## 7. Merge gate

Run focused suites during implementation, then execute `scripts/check-dev-merge.sh`. If the local live-browser phase is blocked by occupied ports or host runtime constraints, document the exact limitation and rely on an isolated exact-commit GitHub Playwright run as required by repository policy.
