# Feature Specification: Dual-Mode Wright UI (Standalone + Hermes Desktop)

**Feature Branch**: `032-dual-mode-desktop`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "Add a Host Adapter abstraction layer to the Wright web frontend so the same React codebase runs both as a standalone browser app and embedded inside Hermes Desktop's Electron shell via a webview with a custom preload bridge. Includes native file dialogs, system notifications, Node.js filesystem, and terminal integration. Do NOT modify NousResearch/hermes-agent."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browser Standalone Experience Unchanged (Priority: P1)

A developer opens Wright at `http://localhost:5173` (dev) or `http://localhost:8000` (production) in their browser. The application behaves exactly as it does today — all pages load, API calls succeed, file listing works, chat composer works, MCP status is visible. No regressions from the adapter refactoring.

**Why this priority**: Any refactoring that breaks the primary use case is a showstopper. The existing standalone browser experience must remain byte-for-byte identical in behavior.

**Independent Test**: Start the Vite dev server, open in a browser, exercise every existing page and feature. All current Vitest and Playwright tests pass without modification.

**Acceptance Scenarios**:

1. **Given** Wright is running in Vite dev mode, **When** a developer opens `http://localhost:5173`, **Then** the dashboard loads, API calls hit `localhost:8000`, and the BrowserRouter produces clean URL paths like `/workspace/123`.
2. **Given** Wright is built and served by FastAPI, **When** a user opens `http://localhost:8000`, **Then** all SPA routes work, static assets load, and the application functions identically to the dev-served version.
3. **Given** no `window.wrightDesktop` is present in the browser, **When** the app initializes, **Then** the BrowserHostAdapter is selected and all services use standard fetch() to communicate with the API.

---

### User Story 2 - Wright Loads Inside Hermes Desktop (Priority: P1)

A Hermes Desktop user (or integrator) loads Wright's desktop build into an Electron BrowserView using the `hermes-wright-panel` package. Wright detects the Electron environment, switches to the DesktopHostAdapter, uses HashRouter for `file://` compatibility, and communicates with the Wright FastAPI backend through the Electron IPC bridge.

**Why this priority**: This is the core deliverable — if Wright doesn't actually work inside Electron, the feature has no value.

**Independent Test**: Load `dist-desktop/index.html` in a test Electron shell with the preload script injecting `window.wrightDesktop`. Verify the app loads, API calls are proxied through IPC, and the UI renders correctly.

**Acceptance Scenarios**:

1. **Given** Wright's desktop build is loaded in an Electron BrowserView with the `hermes-wright-panel` preload, **When** the app initializes, **Then** it detects `window.wrightDesktop`, selects the DesktopHostAdapter, and uses HashRouter (URLs appear as `#/workspace/123`).
2. **Given** the desktop adapter is active, **When** the UI requests workspace data via the API client, **Then** the request is routed through `window.wrightDesktop.api()` IPC to the Electron main process, which proxies it to Wright FastAPI on `localhost:8000`, and the response is returned to the UI.
3. **Given** the Wright FastAPI backend is not running, **When** the desktop-embedded Wright tries to make an API call, **Then** the adapter surfaces a clear error message rather than silently failing.

---

### User Story 3 - Native File Dialog in Desktop Mode (Priority: P2)

When running inside Hermes Desktop, a user wants to upload files to the file vault or select workspace files. Instead of the browser's limited file picker, the system opens a native OS file dialog (via Electron's `dialog.showOpenDialog`) that has full access to the local filesystem.

**Why this priority**: Native file dialogs are a significant UX improvement over browser file pickers, but the feature works without them (browser fallback exists).

**Independent Test**: In desktop mode, trigger a file selection action. Verify that the native dialog appears, files can be selected, and their paths are returned to the application.

**Acceptance Scenarios**:

1. **Given** Wright is running in desktop mode, **When** the user clicks a file upload or file selection button, **Then** a native OS file dialog opens (not the browser's `<input type="file">` dialog).
2. **Given** the user selects files in the native dialog, **When** they confirm the selection, **Then** the file paths are returned to the Wright UI and the selected files are processed.
3. **Given** Wright is running in browser mode, **When** the user clicks a file selection button, **Then** the standard browser file picker is used (graceful fallback).

---

### User Story 4 - System Notifications for Long Operations (Priority: P2)

When running inside Hermes Desktop, long-running operations (CAD generation, agent tasks, file processing) can send native OS notifications so the user is alerted even when the Wright panel is not in focus.

**Why this priority**: Improves usability for background tasks but is not critical for core functionality.

**Independent Test**: Trigger a simulated notification in desktop mode. Verify the OS notification appears with the correct title and body.

**Acceptance Scenarios**:

1. **Given** Wright is running in desktop mode, **When** a long-running operation completes, **Then** a native OS notification is displayed with the operation result.
2. **Given** Wright is running in browser mode, **When** a notification is triggered, **Then** the browser Notification API is used (or the notification is displayed in-app if permissions are denied).

---

### User Story 5 - Direct Filesystem Access in Desktop Mode (Priority: P2)

When running inside Hermes Desktop, workspace file listing and file preview use direct Node.js filesystem access (via Electron IPC) instead of HTTP API calls, providing faster response times for large workspaces.

**Why this priority**: Performance improvement for desktop users, but the HTTP fallback works fine.

**Independent Test**: In desktop mode, navigate to a workspace. Verify file listing returns results and that the underlying mechanism uses IPC (not HTTP).

**Acceptance Scenarios**:

1. **Given** Wright is running in desktop mode with a workspace open, **When** the file browser requests a directory listing, **Then** the request is handled by `window.wrightDesktop.listDirectory()` using Node.js `fs` via the Electron main process.
2. **Given** a file is selected for preview, **When** the UI requests file contents, **Then** the file is read directly from disk via `window.wrightDesktop.readFile()` without an HTTP round-trip.

---

### User Story 6 - Desktop Build Produces Electron-Compatible Output (Priority: P1)

A developer runs `npm run build:desktop` and gets a `dist-desktop/` directory with all assets using relative paths (no leading `/`), suitable for loading via Electron's `file://` protocol. This build is separate from the standard `dist/` build.

**Why this priority**: Without a correct desktop build, the Electron integration cannot work at all.

**Independent Test**: Run `npm run build:desktop`, then open `dist-desktop/index.html` in a browser via `file://` protocol. Verify all assets load (no 404s from absolute paths).

**Acceptance Scenarios**:

1. **Given** a developer runs `npm run build:desktop`, **Then** a `dist-desktop/` directory is created with `index.html` and all assets using relative paths (`./assets/...`).
2. **Given** the desktop build exists, **When** `index.html` is opened via `file://` in a browser, **Then** CSS and JS load without errors (no failed requests for `/assets/...` absolute paths).
3. **Given** a developer runs the standard `npm run build`, **Then** the regular `dist/` output is unchanged (existing behavior preserved).

---

### User Story 7 - Theme Synchronization with Hermes Desktop (Priority: P3)

When running inside Hermes Desktop, Wright automatically matches the host application's theme (dark/light). When the user changes the Hermes Desktop theme, Wright's theme updates in real-time without requiring a page reload.

**Why this priority**: Visual polish — important for a seamless experience but not functionally blocking.

**Independent Test**: Change the Hermes Desktop theme while Wright is visible. Verify Wright's theme updates to match.

**Acceptance Scenarios**:

1. **Given** Wright is embedded in Hermes Desktop in dark mode, **When** the app loads, **Then** Wright renders in dark mode to match the host.
2. **Given** the user switches Hermes Desktop to light mode, **When** the theme change event fires, **Then** Wright's theme updates to light mode without a page refresh.

---

### User Story 8 - Integration Package for Hermes Desktop (Priority: P1)

A developer who wants to embed Wright in an Electron app installs the `hermes-wright-panel` npm package. It provides a preload script, a main-process panel manager, and TypeScript types. The package requires no modifications to the Hermes Desktop source code — it is a standalone, opt-in integration.

**Why this priority**: This is the delivery vehicle for the entire desktop integration. Without it, there's no way for Hermes Desktop to load Wright.

**Independent Test**: Import `hermes-wright-panel` in a minimal Electron app, create a WrightPanel, and verify the BrowserView loads Wright's desktop build with working IPC.

**Acceptance Scenarios**:

1. **Given** a developer installs `hermes-wright-panel`, **When** they import it in their Electron main process, **Then** they can create a `WrightPanel` instance that opens Wright in a BrowserView.
2. **Given** the `hermes-wright-panel` package is installed, **When** the developer inspects its contents, **Then** it contains `preload.cjs`, `panel.cjs`, `types.d.ts`, and `README.md` with clear integration instructions.
3. **Given** no changes are made to `NousResearch/hermes-agent`, **When** the integration package is loaded by a custom Electron app, **Then** it functions correctly as a standalone addition.

---

### Edge Cases

- What happens when the Wright FastAPI backend is not running but the desktop adapter tries to proxy API calls? → The adapter surfaces a connection error with a clear retry/diagnostic message.
- What happens if `window.wrightDesktop` is partially injected (some methods missing)? → The DesktopHostAdapter validates the bridge on initialization and falls back to BrowserHostAdapter for missing capabilities, logging warnings.
- What happens when the desktop build is loaded via `http://` instead of `file://`? → The adapter still detects `window.wrightDesktop` and works correctly; the router choice (Hash vs Browser) is determined by the adapter, not the protocol.
- What happens during hot-reload in development when `window.wrightDesktop` is not present? → The BrowserHostAdapter is selected; no desktop-specific code paths execute.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST detect the host environment at startup by checking for `window.wrightDesktop` and select the appropriate adapter without user intervention.
- **FR-002**: The system MUST provide a `HostAdapter` interface with implementations for browser (BrowserHostAdapter) and desktop (DesktopHostAdapter) environments.
- **FR-003**: The BrowserHostAdapter MUST preserve the exact current behavior of all API calls, file operations, and routing.
- **FR-004**: The DesktopHostAdapter MUST route all API requests through the `window.wrightDesktop.api()` IPC bridge to the Electron main process.
- **FR-005**: The system MUST use BrowserRouter in standalone mode and HashRouter in desktop mode, selected automatically by the adapter.
- **FR-006**: The system MUST produce two build targets: `dist/` (standard, for browser/FastAPI serving) and `dist-desktop/` (relative paths, for Electron `file://` loading).
- **FR-007**: The integration package (`hermes-wright-panel/`) MUST provide a preload script that injects `window.wrightDesktop` via Electron's `contextBridge`.
- **FR-008**: The integration package MUST provide a main-process panel manager that creates a BrowserView, registers IPC handlers, and proxies HTTP requests to Wright's FastAPI backend.
- **FR-009**: The DesktopHostAdapter MUST support native file dialogs for file selection via Electron's `dialog.showOpenDialog`.
- **FR-010**: The DesktopHostAdapter MUST support native OS notifications for alerting users about completed operations.
- **FR-011**: The DesktopHostAdapter MUST support direct filesystem access (read/write/list) via Electron's Node.js integration, bypassing HTTP for file operations.
- **FR-012**: The DesktopHostAdapter MUST support terminal integration via Electron IPC, enabling `node-pty` terminal sessions from the Wright UI.
- **FR-013**: The integration package MUST NOT require any modifications to the `NousResearch/hermes-agent` codebase.
- **FR-014**: The system MUST support theme synchronization between the Electron host and Wright's UI, responding to theme change events from the host.
- **FR-015**: All existing Vitest and Playwright tests MUST continue to pass after the refactoring.

### Key Entities

- **HostAdapter**: The abstraction that mediates between Wright's services and the host environment (browser or Electron). Determines routing strategy, API communication method, and available capabilities.
- **WrightPanel**: The main-process Electron module (in `hermes-wright-panel/`) that manages a BrowserView, handles IPC, and proxies requests to the Wright backend.
- **Preload Bridge**: The Electron preload script that injects `window.wrightDesktop` into the renderer context, providing the IPC surface for the DesktopHostAdapter.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing tests (Vitest unit tests and Playwright integration tests) pass without modification after the refactoring, demonstrating zero regression.
- **SC-002**: The desktop build (`dist-desktop/`) loads successfully via `file://` protocol with zero asset 404 errors.
- **SC-003**: Wright running inside an Electron BrowserView with the integration package can complete a full user workflow (navigate to workspace, list files, view file details, use chat composer) — matching the browser experience feature-for-feature.
- **SC-004**: API response times in desktop mode (through IPC proxy) are within 50ms of direct HTTP access for typical requests.
- **SC-005**: File listing in desktop mode via direct filesystem access is at least 2x faster than the HTTP-based approach for workspaces with 100+ files.
- **SC-006**: The integration package weighs under 50KB (excluding Wright's dist-desktop/ build), ensuring it's lightweight to consume.
- **SC-007**: A developer can integrate Wright into a new Electron app using the `hermes-wright-panel` package in under 10 lines of main-process code.

## Assumptions

- Hermes Desktop uses Electron with `contextIsolation: true` and `nodeIntegration: false`, which is the security-hardened default. The preload bridge uses `contextBridge.exposeInMainWorld()` accordingly.
- The Wright FastAPI backend (`localhost:8000`) is running independently — the integration package does not manage the Wright backend lifecycle.
- The integration package targets Electron 30+ (matching Hermes Desktop's Electron version).
- `node-pty` is available in the Electron app's dependencies for terminal integration. If not present, terminal features degrade gracefully (unavailable indicator in the UI).
- The desktop build is a superset of the browser build — all browser features work, plus desktop-only capabilities are enabled when the adapter detects them.
- Browser mode remains the default and primary development target; desktop mode is an additive capability.
