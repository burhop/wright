# Windows MCP Qualification: autodesk-product-help-mcp

- Result: **partial**
- Observed: 2026-08-14T03:14:38.809589Z
- Safety decision: approved
- Evidence ID: `autodesk-product-help-mcp-windows-20260814T031438Z`

## Qualification boundaries

| Boundary | Result | What was established | Recovery |
|---|---|---|---|
| Source | passed | The pinned source identity passed recipe validation. |  |
| Package or registration | not_applicable | This MCP has no separate local Windows package to install. |  |
| Startup | passed | The MCP server completed initialization. |  |
| Protocol | passed | Initialization and tool discovery completed through MCP. |  |
| Host or backend | passed | The approved bounded tool call completed. |  |
| Wright setup | partial | Wright's production install planner blocked registration because Autodesk service terms have not been independently completed. | Complete any applicable publisher terms outside Wright, record that independent completion, and create a fresh install plan. |
| Wright gateway | not_tested | This stage was not attempted. | Review prerequisites and rerun qualification. |
| Cleanup | passed | Disposable server root was removed. |  |

## Audit proof

- Attempted identity: `autodesk-product-help-mcp`
- Non-allowlist actions: 0
- Installed items recorded: 0
- Cleanup events recorded: 2
