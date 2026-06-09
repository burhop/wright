# Research: Pluggable Viewer Panel API

This document details the architectural decisions, design patterns, and research findings for the Pluggable Viewer Panel API.

## Decisions & Rationale

### 1. Registry Architecture & Resolution Strategy
- **Decision**: Implement the `ViewerRegistry` as a singleton in the web frontend store.
- **Rationale**: File selection, tab state, and panel rendering are purely client-side routing and UI state concerns in the single-page React application. Matches VS Code's Custom Editor contribution registry.
- **Alternatives Considered**: Resolving viewers via backend API endpoints. Rejected because it adds unnecessary network latency (50-100ms) to tab rendering and breaks the offline-first fast rendering target (<50ms).

### 2. GPU/3D Resource Management in Three.js Viewer
- **Decision**: Implement explicit teardown functions in the WebGL adapter that traverse the scene, dispose of all geometries, materials, and textures, and call `renderer.dispose()` and `renderer.forceContextLoss()`.
- **Rationale**: WebGL contexts are limited per browser page. Failing to release context resources upon tab disposal causes memory leaks and eventually crashes WebGL on subsequent tab creations.
- **Alternatives Considered**: Relying on garbage collection. Rejected because the browser does not reliably garbage collect GPU-allocated memory contexts.

### 3. Editor Isolation Model (IFrame & CSP Sandbox)
- **Decision**: Wrap untrusted or external HTML/JS editors inside an `<iframe>` configured with `sandbox="allow-scripts"` and a strict local Content Security Policy (CSP) header.
- **Rationale**: Prevents malicious scripts loaded from user workspace files from accessing local storage, tokens, or parent window APIs.
- **Alternatives Considered**: Rendering directly in the host DOM. Rejected due to critical security risks (Cross-Site Scripting / token theft).

### 4. Background Web Workers for Large Files
- **Decision**: Offload heavy parsing (e.g. converting a raw STEP text file into WebGL triangles) to standard Web Workers.
- **Rationale**: Keeps the browser main thread free (60 FPS rendering) while loading larger datasets (>10MB).

## Best Practices

- **Atomic Design Compliance**: Center panel tabs (`EditorTabs`) are defined as *Components*, and the container panel (`WorkspacePanel` or `ViewerPanelHost`) is a *Pattern*. All colors and margins flow through established design tokens.
- **Testability**: Every panel container, tab button, and custom input must declare `data-testid` (e.g. `data-testid="viewer-tab-step"`, `data-testid="viewer-iframe-sandbox"`).
- **Graceful Failure**: If a viewer provider throws an error during `resolveViewer`, the host catches it and displays a standard error boundary card with log trace details.
