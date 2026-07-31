# Workspace Surfaces Quickstart

> This is the target post-implementation quickstart and an acceptance-test source. Commands and APIs here must be shipped, package-tested, and kept synchronized with the contracts before release.

## Five-Minute Graph

Create `graph.py` in a Wright workspace:

```python
import wright

wright.line(
    x=[0, 1, 2, 3, 4],
    y=[0, 1, 4, 9, 16],
    title="Load test",
    x_label="Time (s)",
    y_label="Deflection (mm)",
    description="Deflection rises from 0 to 16 millimetres over four seconds.",
)
```

Run the file using Wright's normal **Run Python** action. Wright opens a graph surface next to chat. No port, server, HTML, JavaScript or plotting-package setup is required. Change a number and rerun: Wright updates the logical result. Because this is a durable display, it remains visible after Python exits.

If you ask Wright to “make a bar chart from this data,” it should generate the same public API rather than inventing private browser code.

### Display an existing figure

Optional packages add richer adapters without changing the surface workflow:

```python
import wright
import plotly.express as px

figure = px.scatter(x=[1, 2, 3], y=[2, 1, 4], labels={"x": "Trial", "y": "Force"})
wright.display(figure, title="Force by trial", display_id="force-trials")
```

Supported baseline results are text, typed tables, PNG/JPEG, SVG, sanitized HTML, and Wright's typed graph data. Optional adapters include Matplotlib, Plotly, pandas and PIL. Interactive Plotly uses Wright's bundled renderer and works offline.

### HTML safety

```python
wright.display("<strong>Result:</strong> 42", title="Summary")
```

Ordinary HTML is sanitized and cannot run scripts. If a trusted workflow truly needs active HTML, `active_html=True` must be explicit; Wright displays it on an isolated unprivileged origin without file, tool, credential, WebMCP or MCP App access. A full interactive application should normally use a managed live app instead.

## Open BREP or Another Web Application

A declared application can be launched by an MCP integration, a workspace command, or the surface API. When its surface is ready, choose:

- **Open in workspace** to embed the full JavaScript UI beside chat.
- **Open in browser** to use the system browser.
- **Open both** when the app declares a shareable instance.

Both presentations address the same authorized instance unless the declaration says it requires isolation. Closing a tab does not necessarily stop the app. Use **Stop application** for that. If the declaration omits a lifetime, Wright keeps the app until the workspace closes.

Wright remembers the valid presentation preference for the current user, workspace and source. If an app refuses framing or the current deployment cannot provide an isolated preview origin, Wright explains why and offers the browser without weakening the app's security headers.

## Focus Mode

With a surface selected, choose **Focus surface**. The surface expands into all non-chat workspace space while chat remains visible and resizable. Use the keyboard-accessible separator or its arrow-key controls to resize. On narrow screens, use the explicit **Chat / Surface** switcher. Escape or **Exit focus** restores the prior layout without reloading a retained live app.

## Minimal Managed App

Create `.wright/apps/demo.surface.json`:

```json
{
  "$schema": "https://wright.local/schemas/live-app-manifest-v1.json",
  "schemaVersion": 1,
  "id": "demo.fastapi",
  "version": "1.0.0",
  "title": "Demo live graph",
  "ownershipPolicy": "wright-owned",
  "launch": {
    "mode": "command",
    "argv": ["python", "app.py", "--host", "${WRIGHT_BIND_HOST}", "--port", "${WRIGHT_PORT}"],
    "workingDirectory": "."
  },
  "readiness": {"path": "/health", "expectedStatus": 200, "timeoutMs": 10000},
  "presentation": {"panel": true, "browser": true, "sharing": "shared"},
  "transports": {"http": true, "websocket": true, "sse": true},
  "lifetime": {"policy": "workspace"},
  "capabilities": []
}
```

The command is an argv array, never a shell command. Wright chooses the loopback port, injects the exact public origin/base-path settings, waits for `/health`, owns the process tree, and exposes only opaque presentation URLs. Application code must use relative URLs or the injected base path for nested assets, redirects, WebSockets and SSE. Use `ownershipPolicy: "approved-attach"` only with launch mode `attach`; it requires administrator eligibility plus explicit target approval.

For real integration, validate the declaration against [live-app-manifest.schema.json](./contracts/live-app-manifest.schema.json) and run the conformance suite:

```powershell
uv run pytest tests/contract/workspace_surfaces -k live_app
```

Framework templates under `examples/workspace-surfaces/` show FastAPI, Panel, Streamlit, Gradio and Dash settings. Those frameworks are optional application dependencies, not Wright core dependencies. BREP uses this same manifest/lifecycle contract unless it publishes a packaged MCP App.

## Attach an Existing App

Use manifest launch mode `attach` with an exact declared URL only when Wright did not start the server. Wright shows the normalized target, network class and requested capabilities for explicit approval, pins the validated target, and applies the same presentation policy. An arbitrary URL entered by a user is different: it is direct-navigation/view-only, is never proxied, receives no credentials or bridge, and must be approved for that instance.

## MCP App Integration

An MCP server associates a tool with a packaged UI resource using the stable MCP Apps metadata:

```json
{
  "name": "show_design",
  "description": "Show the current design; returns a text summary when UI is unavailable.",
  "inputSchema": {"type": "object", "properties": {}},
  "_meta": {
    "ui": {"resourceUri": "ui://brep/current-design"}
  }
}
```

The server must return `ui://brep/current-design` from `resources/read` as `text/html;profile=mcp-app` and include useful fallback content in tool results. Wright negotiates `io.modelcontextprotocol/ui`, renders the View through the official distinct-origin sandbox, and permits only declared/granted same-server app-visible operations. The URI may be absent from `resources/list`; exact read must still work.

Do not use MCP Apps metadata merely to point at a conventional server URL. Declare that server as a managed app.

## WebMCP-Aware App

Use the shipped Wright surface SDK as the stable path. It registers a tool only within the current workspace/session/surface/origin and removes it on abort/navigation:

```javascript
const registration = await wrightSurface.registerTool({
  name: "select_part",
  description: "Select a visible part in this surface",
  inputSchema: {
    type: "object",
    properties: { partId: { type: "string" } },
    required: ["partId"]
  },
  handler: async ({ partId }) => selectVisiblePart(partId),
  signal: controller.signal
});
```

The SDK feature-detects the current `document.modelContext` draft and may dual-register when the host proves support. Code must not depend on native WebMCP; Wright's scoped adapter is the portable contract. Global `window` broadcasts and wildcard `postMessage` are unsupported.

## Permissions

Declarations state what an app could request; they do not grant it. Wright evaluates RBAC and deployment/workspace policy, then asks when user consent is applicable. Low-risk capability choices can be remembered only for the exact user, workspace, source and source version. Mutating/high-risk capabilities default to the current operation or instance. Revocation takes effect immediately for new operations and cancels pending work where safe.

An app never receives Wright's auth cookie/token. Panel/browser access uses a separate short-lived presentation credential scoped to the isolated hostname and instance. Its one-time token is carried in a URL fragment, exchanged by a bootstrap POST, and removed before app navigation so request tracing, logs and Referer cannot capture it.

## Diagnostics and Recovery

Open **Surface diagnostics** to see safe identity/provenance, lifecycle and health history, current presentation, declared/granted capabilities, recent stable error codes, and trace/correlation IDs. Secrets, raw credentials, sensitive queries and protected content are redacted.

Typical recovery:

- **Starting timed out**: inspect redacted logs and readiness path; fix the app and choose **Restart**.
- **Cannot embed**: upstream framing policy or host isolation does not allow a panel; choose **Open in browser**.
- **App stopped**: choose **Restart** to create a new runtime generation; Wright does not trust a stale PID/URL.
- **Permission denied**: inspect the exact source/version/operation and policy reason; change policy or grant only if appropriate.
- **Display unavailable**: run through Wright so the execution-scoped display endpoint is injected; install an optional adapter only when the error names it.

Every reported error includes a correlation ID for local structured logs/traces.

## Definition of Done for These Examples

- The beginner example runs from an installed wheel in a clean environment and visibly updates in under the success target.
- Every manifest validates and launches without a source checkout or CDN.
- HTTP, nested assets, deep links, redirects, WebSocket and SSE examples pass through the real preview route.
- Panel/browser presentations, focus mode, keyboard paths, frame fallback and diagnostics have automated Playwright coverage.
- MCP and WebMCP examples include authorized and denied operations plus teardown.
- Windows/macOS/Linux native and Docker smoke runs record cleanup evidence with zero leaked owned processes, ports, credentials or instance grants.
