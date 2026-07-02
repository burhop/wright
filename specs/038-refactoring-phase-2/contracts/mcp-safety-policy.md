# Contract: MCP Safety Policy

## Operations

```text
can_install(server, approval_context) -> PolicyDecision
can_start(server, workspace_context, approval_context) -> PolicyDecision
can_call_tool(server, tool_name, workspace_context, approval_context) -> PolicyDecision
```

## Decision Fields

- `allowed`
- `operation`
- `reason`
- `required_approvals`
- `missing_credentials`
- `network_required`
- `blocked_by_catalog`
- `diagnostics`

## Required Enforcement

- `blocked` and `non_working` entries deny install/start/call.
- Required credential names deny start/call when missing.
- High-risk and safety-critical entries with approval gates deny install/start/call until approved.
- Remote network servers require explicit metadata and workspace enablement.
- Package-manager use alone is not an approval gate.

## Error Translation

Policy denials surface as typed package errors. API routes translate them to `400` responses for current compatibility.
