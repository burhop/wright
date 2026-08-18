# Windows MCP Qualification: brep-mcp

- Result: **failed**
- Observed: 2026-08-14T03:13:43.976756Z
- Safety decision: approved
- Evidence ID: `brep-mcp-windows-20260814T031343Z`

## Qualification boundaries

| Boundary | Result | What was established | Recovery |
|---|---|---|---|
| Source | passed | The pinned source identity passed recipe validation. |  |
| Package or registration | passed | The pinned MCP package installed in the disposable root. |  |
| Startup | passed | The MCP server completed initialization. |  |
| Protocol | passed | Initialization and tool discovery completed through MCP. |  |
| Host or backend | failed | The approved BREP call reached an upstream entry-point defect before the deterministic geometry result was produced. | Upstream must resolve its data-URL/file-URL entry-point handling; do not patch the installed third-party package during qualification. |
| Wright setup | not_tested | This stage was not attempted. | Review prerequisites and rerun qualification. |
| Wright gateway | not_tested | This stage was not attempted. | Review prerequisites and rerun qualification. |
| Cleanup | passed | Disposable server root was removed. |  |

## Audit proof

- Attempted identity: `brep-mcp`
- Non-allowlist actions: 0
- Installed items recorded: 1
- Cleanup events recorded: 2
