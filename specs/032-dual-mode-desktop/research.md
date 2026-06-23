# Research: Dual-Mode Desktop Integration

**Feature**: 032-dual-mode-desktop | **Date**: 2026-06-23

## R1: Electron Preload/contextBridge Pattern

**Decision**: Use Electron `contextBridge.exposeInMainWorld()` in a custom preload script to inject `window.wrightDesktop`.

**Rationale**: This is the Hermes Desktop's own pattern (see `electron/preload.cjs` which exposes `window.hermesDesktop`). It provides full `contextIsolation` security while enabling typed IPC from the renderer. No `nodeIntegration` needed.

**Alternatives considered**:
- `nodeIntegration: true` — rejected, security risk, deprecated pattern
- `postMessage()` between webview and host — too loose, no type safety
- Shared worker with MessageChannel — overcomplex for this use case

## R2: BrowserView vs webview Tag vs iframe

**Decision**: Use `BrowserView` for embedding Wright in Electron.

**Rationale**: `BrowserView` is Electron's recommended way to embed web content with full preload support. It runs in its own renderer process, has full access to Electron APIs via preload, and doesn't require the host renderer to load Wright's React bundle. Hermes Desktop already uses `BrowserView` for session windows.

**Alternatives considered**:
- `<webview>` tag — deprecated in newer Electron, requires `webviewTag: true` which weakens security
- `<iframe>` — no access to Electron APIs, CORS complications with `file://`, no preload support
- Direct React component import — tight coupling to Hermes Desktop's build (TailwindCSS v4, Zustand, React Query), maintenance burden

## R3: Router Strategy for file:// Protocol

**Decision**: Use `HashRouter` when `window.wrightDesktop` is detected; `BrowserRouter` otherwise.

**Rationale**: Electron loads renderer content via `file://` protocol when using `loadFile()`. `BrowserRouter` relies on `history.pushState()` which doesn't work with `file://` — the browser can't resolve paths like `file:///path/to/dist/workspace/123`. `HashRouter` keeps state in the URL hash fragment (`#/workspace/123`) which works with any protocol.

**Alternatives considered**:
- Always use `HashRouter` — rejected, ugly URLs in browser mode
- `MemoryRouter` — works but loses URL-based navigation/bookmarking

## R4: IPC Proxy vs Direct HTTP for API Calls

**Decision**: In desktop mode, proxy Wright API requests through Electron IPC (renderer → main process → HTTP → FastAPI).

**Rationale**: This is how Hermes Desktop handles all its API calls (via `window.hermesDesktop.api()`). The Electron main process makes the HTTP request, avoiding CORS issues with `file://` origins. The main process can also add auth headers, retry logic, and connection management.

**Alternatives considered**:
- Direct `fetch()` from renderer to `localhost:8000` — fails with CORS from `file://` origin; requires `app.commandLine.appendSwitch('disable-web-security')` which is a security hole
- Service worker proxy — overcomplex for this use case

## R5: Desktop Build Configuration

**Decision**: Use Vite's `--mode desktop` flag to produce a `dist-desktop/` build with `base: './'`.

**Rationale**: Vite's `base` option controls asset URL resolution. Setting `base: './'` produces relative paths (`./assets/index-xxx.js`) instead of absolute (`/assets/index-xxx.js`). This is necessary for `file://` loading where there's no server to resolve absolute paths. Hermes Desktop uses the same pattern.

**Alternatives considered**:
- Post-build path rewriting — fragile, error-prone
- Single build with relative paths for all modes — changes browser behavior, can break FastAPI static serving

## R6: node-pty Terminal Integration

**Decision**: Expose terminal capabilities through the `wrightDesktop.terminal` IPC namespace, using `node-pty` from the Electron main process.

**Rationale**: Hermes Desktop already bundles `node-pty` and uses it for its terminal. The integration package can reuse it if available, or degrade gracefully if not installed.

**Alternatives considered**:
- WebSocket-based terminal (xterm.js + ws) — requires a separate server
- Shipping node-pty inside the integration package — native dependency, platform-specific builds

## R7: Theme Synchronization Mechanism

**Decision**: Listen for `wright:theme-changed` IPC events from the Electron main process and update CSS custom properties / `data-theme` attribute.

**Rationale**: Wright already uses `data-theme` attribute on `<html>` for theming. The desktop adapter registers an IPC listener that receives theme changes from the host and updates this attribute. This is exactly how Hermes Desktop syncs its renderer theme.

**Alternatives considered**:
- CSS `prefers-color-scheme` media query — doesn't work for custom themes, only dark/light
- Polling the host for theme state — wasteful, laggy
