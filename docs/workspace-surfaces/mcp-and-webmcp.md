# MCP Apps and scoped WebMCP

Wright supports two different browser-facing MCP patterns. Choose based on who owns the UI:

| Need | Use |
|---|---|
| An MCP tool result carries a packaged, self-contained `ui://` view | Stable MCP Apps |
| A managed web page exposes a page-local tool to Wright | Wright scoped WebMCP SDK |
| BREP or another conventional server runs a full web application | Managed app, not MCP Apps |

MCP Apps use the stable `io.modelcontextprotocol/ui` contract dated 2026-01-26. Wright pins `@modelcontextprotocol/ext-apps` 1.7.5. WebMCP's `document.modelContext` remains experimental; Wright feature-detects it but does not rely on or polyfill it. Wright's protocol-version `1.0` scoped bridge is the stable compatibility route.

## Build a packaged MCP App

The complete reference is in `examples/workspace-surfaces/mcp_app_server`.

1. Associate a tool with a `ui://` resource using canonical metadata:

   ```json
   {
     "name": "show_design",
     "_meta": {
       "ui": {
         "resourceUri": "ui://wright.reference/design",
         "visibility": ["model", "app"]
       }
     }
   }
   ```

2. Return that exact URI from `resources/read` with `text/html;profile=mcp-app`. It may be absent from `resources/list`; Wright reads it by its server connection and exact URI.
3. Bundle all scripts and styles into the HTML resource. Do not depend on a CDN. The reference's `npm run build` produces one offline `dist/index.html` using the official `App` bridge.
4. Return useful text or structured content from the tool. Users must still receive a meaningful result if UI hosting is disabled, the resource changes, or rendering fails.
5. Mark operations the app may invoke with `_meta.ui.visibility: ["app"]` or `["model", "app"]`. Wright denies model-only and cross-server operations even if the page asks for them.

When enabled, Wright negotiates the extension, hashes and revalidates the exact resource, and runs it through an outer sandbox proxy and inner view on a distinct origin. The official App bridge carries JSON-RPC between the view and host. Wright then applies same-server visibility, workspace grants, input/output schemas, size/time limits, cancellation, and audit at the backend. Browser code is never the authority.

The app may call only granted bridge operations. Device and network requests default to denied; resource metadata must declare them, deployment policy must permit them, and the user or workspace must grant them. `ui/notifications/request-teardown` asks the host to close the view—it does not silently stop an unrelated managed server.

## Add scoped WebMCP to a managed page

The complete graph page and manifest are in `examples/workspace-surfaces/webmcp_app`. The essential shape is:

```javascript
const controller = new AbortController();
const sdk = new WrightSurfaceSdk();

const registration = await sdk.registerTool({
  name: "set_graph",
  description: "Replace the values in this page's visible graph.",
  inputSchema: {
    type: "object",
    properties: {
      values: {type: "array", minItems: 2, maxItems: 50, items: {type: "number"}}
    },
    required: ["values"],
    additionalProperties: false
  },
  signal: controller.signal,
  handler: ({values}) => {
    render(values);
    return {rendered: values.length};
  }
});

// Navigation/pagehide also disposes automatically.
controller.abort();
await registration.dispose();
```

Declare `wright.webmcp.register` in the managed-app manifest. Policy may deny it; declaring a capability is not a grant. The page connects to its same-origin `/__wright/webmcp` endpoint. The host-only presentation cookie authenticates that socket; the page receives no Wright bearer token and cannot choose its principal, workspace, session, surface, runtime generation, origin, or MCP server binding.

Registrations are keyed by all of those fields plus tool name. Two pages may therefore use `set_graph` simultaneously without collision. Origin changes, navigation, abort, surface disposal, workspace/session closure, runtime replacement, and disconnect unregister the exact tool and cancel pending work. Late, replayed, wrong-origin, wrong-generation, and wrong-socket results are ignored and audited.

Arguments and results must be bounded objects that satisfy the declared schema. Treat tool descriptions, arguments, and results as untrusted input. Do not place secrets in names, descriptions, schemas, results, URLs, browser storage, or logs.

## Optional native WebMCP

An integration may additionally register with native WebMCP only after feature and Permissions Policy checks:

```javascript
const register = document.modelContext?.registerTool;
if (typeof register === "function" &&
    document.permissionsPolicy?.allowsFeature?.("tools") !== false) {
  try {
    await register.call(document.modelContext, nativeDefinition);
  } catch {
    // Wright's scoped registration remains active.
  }
}
```

Never assign `document.modelContext`, infer support from the browser name, or make native invocation the sole path. Record the browser build, detected API members, draft date, and Permissions Policy result when producing compatibility evidence.

## Panel, browser, and teardown behavior

The same managed application instance can be shown in Wright, in the system browser, or both when its manifest uses shared presentation. Both authorized preview pages have distinct presentation authority, and each WebMCP registration remains tied to its own document identity. Closing a presentation unregisters its page tools. **Stop application** additionally revokes every presentation and ends the owned runtime generation.

Packaged MCP Apps are panel-hosted resources, not arbitrary server URLs. If an MCP server starts BREP, publish BREP as a managed-app surface and offer **Open in workspace** / **Open in browser**. Only use MCP Apps if the server actually publishes a packaged `ui://` resource.

## Verification

Run the focused conformance checks from the repository root:

```powershell
uv run pytest tests/e2e/workspace-surfaces/test_mcp_app.py
uv run pytest apps/api/tests/test_surface_webmcp.py apps/api/tests/test_surface_webmcp_security.py
npx playwright test tests/ui-integration/workspace-surfaces/webmcp.spec.ts --project=chromium
```

Expected failure behavior is fail-closed: UI absence preserves fallback content; denied operations remain denied; a broken native WebMCP path leaves the Wright bridge active; and stale/disconnected registrations have no authority.
