# Quickstart: Gateway Service and MCP 2025-11-25

1. Create or select a Wright workspace and obtain its immutable workspace/session identifier through authenticated Wright setup.
2. Start the STDIO MCP entry point with the explicit workspace/session binding, or start the Wright API on loopback and connect to authenticated `/mcp`.
3. Initialize using MCP 2025-11-25, send `notifications/initialized`, list tools/resources, and invoke one safe read operation.
4. Change the bound workspace's tool configuration and observe the scoped list-change notification.
5. Start a second session on another workspace and prove each session's lists, calls, resources, and cancellations are disjoint.
6. Close the client and verify the session, requests, coordinator tasks, and child runners shut down within the configured bound.

Compatibility rollback: set `WRIGHT_LEGACY_GATEWAY=1` only for one migration release; callers still must provide explicit session identity. Return to the Feature 045 image/commit for full code rollback.
