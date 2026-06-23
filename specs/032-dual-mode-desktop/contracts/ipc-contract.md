# IPC Contract: Wright Desktop Bridge

**Feature**: 032-dual-mode-desktop | **Date**: 2026-06-23

This contract defines the IPC channels between the Wright renderer (inside an Electron BrowserView) and the Electron main process, mediated by the preload script.

## Channel Namespace

All channels are prefixed with `wright:` to avoid collision with Hermes Desktop's `hermes:` namespace.

## Request/Response Channels (ipcMain.handle / ipcRenderer.invoke)

| Channel | Direction | Request Payload | Response Payload | Description |
|:---|:---|:---|:---|:---|
| `wright:api` | Renderer → Main | `{ path: string, method?: string, body?: object, timeoutMs?: number }` | `<T>` (JSON) | Proxy HTTP request to Wright FastAPI |
| `wright:readFile` | Renderer → Main | `string` (absolute path) | `string` (file content) | Read file via Node.js fs |
| `wright:writeFile` | Renderer → Main | `{ path: string, content: string }` | `void` | Write file via Node.js fs |
| `wright:listDirectory` | Renderer → Main | `string` (absolute path) | `FileEntry[]` | List directory contents |
| `wright:selectFiles` | Renderer → Main | `SelectOptions?` | `string[]` (selected paths) | Open native file dialog |
| `wright:notify` | Renderer → Main | `{ title: string, body: string }` | `boolean` | Show OS notification |
| `wright:getConfig` | Renderer → Main | `void` | `{ apiPort: number, workspacePath: string? }` | Get runtime config |
| `wright:terminal:start` | Renderer → Main | `{ cols?: number, rows?: number, cwd?: string }` | `{ id: string, pid: number }` | Start terminal session |
| `wright:terminal:write` | Renderer → Main | `{ id: string, data: string }` | `void` | Write to terminal |
| `wright:terminal:resize` | Renderer → Main | `{ id: string, cols: number, rows: number }` | `void` | Resize terminal |
| `wright:terminal:dispose` | Renderer → Main | `string` (session id) | `boolean` | Dispose terminal |

## Event Channels (ipcRenderer.on)

| Channel | Direction | Payload | Description |
|:---|:---|:---|:---|
| `wright:theme-changed` | Main → Renderer | `{ theme: 'dark' \| 'light' }` | Theme changed in host app |
| `wright:terminal:data:<id>` | Main → Renderer | `string` (terminal output) | Terminal stdout/stderr data |
| `wright:terminal:exit:<id>` | Main → Renderer | `{ exitCode: number, signal?: number }` | Terminal process exited |

## Error Handling

All `invoke` handlers reject with a structured error:

```typescript
{
  code: string;      // e.g., 'ENOENT', 'EACCES', 'FETCH_FAILED', 'TIMEOUT'
  message: string;   // Human-readable description
  details?: object;  // Optional additional context
}
```

## Security Constraints

- All file paths are validated against a configurable workspace root — reads/writes outside the workspace are rejected with `EACCES`.
- The `wright:api` proxy only connects to `localhost` on the configured port — no arbitrary URL proxying.
- Terminal sessions are limited to 10 concurrent instances.
