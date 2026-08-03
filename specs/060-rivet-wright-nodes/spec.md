# Rivet Wright Nodes

Expose a narrow, default-off Rivet external-call bridge to Wright engineering
operations. Every invocation must be server-bound to run/node/workspace/session
and pass GatewayService policy, approval, artifacts, audit, and redaction.
Direct MCP, arbitrary plugins, credentials in graphs, raw network/file/code
authority, and client-trusted approvals are excluded.

Acceptance: read-only and mutating calls follow identical policy; approval
deny/revoke/replay is rejected; cross-workspace calls fail; artifacts preserve
provenance; logs/files contain no secrets.
