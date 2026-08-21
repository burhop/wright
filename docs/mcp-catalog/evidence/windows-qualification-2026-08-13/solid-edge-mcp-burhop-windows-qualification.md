# Windows MCP Qualification: solid-edge-mcp-burhop

- Result: **failed**
- Observed: 2026-08-14T03:14:37.293030Z
- Safety decision: approved
- Evidence ID: `solid-edge-mcp-burhop-windows-20260814T031437Z`

## Qualification boundaries

| Boundary | Result | What was established | Recovery |
|---|---|---|---|
| Source | passed | The pinned source identity passed recipe validation. |  |
| Package or registration | passed | The reviewed MCP source built in the disposable root. |  |
| Startup | passed | The MCP server completed initialization. |  |
| Protocol | passed | Initialization and tool discovery completed through MCP. |  |
| Host or backend | failed | The approved status call returned structured content that violated the server's published output schema. | Upstream must emit the required nullable activeDocument property when Solid Edge has no active document. |
| Wright setup | not_tested | This stage was not attempted. | Review prerequisites and rerun qualification. |
| Wright gateway | not_tested | This stage was not attempted. | Review prerequisites and rerun qualification. |
| Cleanup | passed | Disposable server root was removed. |  |

## Audit proof

- Attempted identity: `solid-edge-mcp-burhop`
- Non-allowlist actions: 0
- Installed items recorded: 2
- Cleanup events recorded: 2
