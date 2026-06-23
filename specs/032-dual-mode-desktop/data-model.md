# Data Model: Dual-Mode Desktop Integration

**Feature**: 032-dual-mode-desktop | **Date**: 2026-06-23

## Entities

### HostAdapter (Interface)

The central abstraction that mediates between Wright's service layer and the host environment.

| Field / Method | Type | Description |
|:---|:---|:---|
| `mode` | `'browser' \| 'desktop'` | Read-only identifier of the active host |
| `fetch<T>()` | method | Proxied HTTP request (browser: native fetch, desktop: IPC) |
| `readFile()` | method | Read file content (browser: API, desktop: Node.js fs) |
| `writeFile()` | method | Write file content (browser: API, desktop: Node.js fs) |
| `listDirectory()` | method | List directory entries (browser: API, desktop: Node.js fs) |
| `selectFiles()` | method | Open file picker (browser: `<input>`, desktop: `dialog.showOpenDialog`) |
| `getApiBaseUrl()` | method | Resolve the Wright API base URL |
| `getRouterType()` | method | `'browser'` or `'hash'` for router selection |
| `notify()` | method | Send notification (browser: Notification API, desktop: Electron Notification) |
| `hasTerminal()` | method | Whether terminal integration is available |
| `dispose()` | method | Cleanup listeners and resources |

**Relationships**: Consumed by all service modules (`api-client.ts`, `workspace-service.ts`, etc.). Singleton instance created at app startup.

### BrowserHostAdapter (Implementation)

Wraps the current browser-native behavior. No state beyond the API base URL.

| Field | Type | Description |
|:---|:---|:---|
| `mode` | `'browser'` | Always `'browser'` |
| `apiBaseUrl` | `string` | Computed from `window.location` (current behavior from `getApiUrl()`) |

### DesktopHostAdapter (Implementation)

Delegates to the `window.wrightDesktop` IPC bridge injected by the Electron preload.

| Field | Type | Description |
|:---|:---|:---|
| `mode` | `'desktop'` | Always `'desktop'` |
| `bridge` | `WrightDesktopBridge` | Reference to `window.wrightDesktop` |
| `themeUnsubscribe` | `() => void` | Cleanup function for theme change listener |

**State transitions**: Created at startup → Active → Disposed (on app teardown)

### WrightDesktopBridge (Window Interface)

The shape of `window.wrightDesktop` injected by the Electron preload.

| Method | Signature | Description |
|:---|:---|:---|
| `api` | `(request: WrightApiRequest) => Promise<T>` | Proxy HTTP to Wright API |
| `readFile` | `(path: string) => Promise<string>` | Read file via Node.js fs |
| `writeFile` | `(path: string, content: string) => Promise<void>` | Write file via Node.js fs |
| `listDirectory` | `(path: string) => Promise<FileEntry[]>` | List directory via Node.js fs |
| `selectFiles` | `(options?: SelectOptions) => Promise<string[]>` | Native file dialog |
| `notify` | `(payload: NotifyPayload) => Promise<boolean>` | OS notification |
| `terminal.start` | `(options?) => Promise<TerminalSession>` | Start node-pty session |
| `terminal.write` | `(id, data) => Promise<void>` | Write to terminal |
| `terminal.resize` | `(id, size) => Promise<void>` | Resize terminal |
| `terminal.dispose` | `(id) => Promise<boolean>` | Dispose terminal |
| `terminal.onData` | `(id, callback) => () => void` | Subscribe to terminal output |
| `terminal.onExit` | `(id, callback) => () => void` | Subscribe to terminal exit |
| `getConfig` | `() => Promise<WrightConfig>` | Get Wright/Electron config |
| `onThemeChange` | `(cb) => () => void` | Subscribe to theme changes |

### WrightPanel (Electron Main Process)

Main-process module in the `hermes-wright-panel` package.

| Field | Type | Description |
|:---|:---|:---|
| `mainWindow` | `BrowserWindow` | The host Electron window |
| `view` | `BrowserView` | The BrowserView hosting Wright |
| `wrightApiPort` | `number` | Port of the Wright FastAPI backend (default 8000) |
| `distPath` | `string \| null` | Path to Wright's `dist-desktop/` build |
| `terminalSessions` | `Map<string, IPty>` | Active node-pty terminal sessions |

**State transitions**: Constructed → View Created → Active → Destroyed

### FileEntry

| Field | Type | Description |
|:---|:---|:---|
| `name` | `string` | File or directory name |
| `path` | `string` | Full path |
| `isDirectory` | `boolean` | Whether this entry is a directory |
| `size` | `number?` | File size in bytes (files only) |

### SelectOptions

| Field | Type | Description |
|:---|:---|:---|
| `title` | `string?` | Dialog window title |
| `filters` | `FileFilter[]?` | File type filters |
| `multiple` | `boolean?` | Allow multiple selection |
| `directory` | `boolean?` | Select directories instead of files |
