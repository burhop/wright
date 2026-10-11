# SteveCAD saved process in Wright

Actual isolated workspace; inspection only. No engineering acceptance.

## 2026-10-11T17:13:30.116Z UTC — 00
URL: http://wright.localhost:8891/dashboard
Action/control/value: Open Wright and unlock it with the existing private local access token. Do not share the token.
Expected: Normal local access succeeds without exposing credentials
Actual: locator.waitFor: Timeout 30000ms exceeded.
Call log:
[2m  - waiting for getByTestId('card-workspace-225aca34-3ae9-4557-85d6-0d8defd90a86') to be visible[22m

Diagnostics: [{"kind":"http","path":"/api/mcp/servers","status":401,"expected":true},{"kind":"console","text":"Failed to load resource: the server responded with a status of 401 (Unauthorized)","expected":true},{"kind":"console","text":"{\"timestamp\":\"2026-10-11T17:12:59.680Z\",\"level\":\"error\",\"message\":\"Failed to fetch MCP servers\",\"component\":\"McpService\",\"traceId\":null,\"metadata\":{\"status\":401}}","expected":true},{"kind":"http","path":"/api/mcp/tools","status":401,"expected":true},{"kind":"console","text":"Failed to load resource: the server responded with a status of 401 (Unauthorized)","expected":true},{"kind":"console","text":"{\"timestamp\":\"2026-10-11T17:12:59.680Z\",\"level\":\"error\",\"message\":\"Failed to fetch MCP tools\",\"component\":\"McpService\",\"traceId\":null,\"metadata\":{\"status\":401}}","expected":true},{"kind":"http","path":"/api/agent/sessions","status":401,"expected":true},{"kind":"console","text":"Failed to load resource: the server responded with a status of 401 (Unauthorized)","expected":true},{"kind":"console","text":"Failed to sync sessions with backend, falling back to localStorage Error: Failed to list sessions: Unauthorized\n    at Object.listSessions (http://wright.localhost:8891/assets/index-BHYKQogG.js:4223:28591)\n    at async http://wright.localhost:8891/assets/index-BHYKQogG.js:4224:12537","expected":true},{"kind":"http","path":"/api/settings","status":401,"expected":true},{"kind":"console","text":"Failed to load resource: the server responded with a status of 401 (Unauthorized)","expected":true}]
Raw: screenshots/raw/00-stopped.png
Annotated: screenshots/annotated/00-stopped.png
Status: STOPPED
