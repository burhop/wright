# Pluggable Viewer Panel API Specification (VS Code–Style)

## 1. Goals and Scope

This specification defines a **pluggable viewer panel API** for a web application, inspired by Visual Studio Code’s Custom Editor and Webview APIs.[web:31][web:32]

The goal is to allow independent components (“viewers”) to render and edit heterogeneous content types (3D models, Python files, PDFs, Markdown, plain text, forms, iframes, etc.) inside a **single central panel** with a consistent lifecycle, messaging, and resource-management model.

Out of scope:

- A full VS Code–compatible extension host.
- Language server integration, debugging, SCM, etc. (can be added later as separate systems).


## 2. Core Concepts

### 2.1 Viewer

A **Viewer** is a pluggable component that knows how to present and optionally edit a specific kind of resource, similar to VS Code’s Custom Editors.[web:31]

Examples:

- `Step3DViewer` – WebGL/Three.js-based STEP/IGES/3MF viewer.
- `PythonCodeEditor` – code editor (Monaco/CodeMirror) for Python files.
- `PdfViewer` – adapter around an existing PDF viewer.
- `MarkdownViewer` – live preview (or split editor) for Markdown.
- `TextViewer` – plain text viewer/editor.
- `IframeViewer` – sandboxed external content.
- `FormViewer` – renders form schemas as interactive forms.

### 2.2 Viewer Document

A **ViewerDocument** represents the underlying content model (file, stream, or composite asset), similar in spirit to VS Code’s `CustomDocument`.[web:31][web:32]

Responsibilities:

- Hold URI and any in-memory state.
- Provide methods for save/revert/backup.
- Support dirty tracking and undo/redo by exposing edit events.

### 2.3 Panel Host

The **PanelHost** is the center-panel instance that embeds the viewer UI, similar to VS Code’s `WebviewPanel`.[web:31][web:44][web:48]

Responsibilities:

- Provide a DOM container for the viewer UI.
- Manage lifecycle (open, visible/hidden, dispose).
- Provide a messaging channel between viewer UI and the core application.

### 2.4 Viewer Registry

The **ViewerRegistry** maps `(file, mode)` → `ViewerProvider` using metadata (selectors, priority), analogous to VS Code’s `customEditors` contribution point and `registerCustomEditorProvider`.[web:31][web:32]


## 3. Type System and Interfaces

All interfaces below are expressed in TypeScript-like notation, but the concepts are language-agnostic.

### 3.1 FileDescriptor

```ts
interface FileDescriptor {
  id: string;                  // internal ID
  uri: string;                 // canonical URI (URL, repo path, etc.)
  name: string;                // display name
  extension: string;           // e.g. "py", "step", "pdf", "md"
  mimeType: string;            // e.g. "application/step", "text/markdown"
  size?: number;               // bytes, optional
  metadata?: Record<string, unknown>; // domain-specific metadata
}
```

### 3.2 ViewerMode

```ts
type ViewerMode = "preview" | "edit" | "compare";
```

Modes may affect which viewer is chosen and what capabilities are exposed.

### 3.3 ViewerCapabilities

```ts
interface ViewerCapabilities {
  canEdit: boolean;              // supports editing & saving
  canAnnotate: boolean;          // supports annotations/markup
  supports3DControls: boolean;   // provides orbit/pan/zoom, etc.
  prefersIsolation: boolean;     // needs iframe/webview-like isolation (e.g. untrusted HTML)
  supportsMultiView: boolean;    // safe to open multiple views per document
}
```

### 3.4 ViewerDocument

```ts
interface ViewerDocument {
  readonly uri: string;
  readonly type: string;     // logical document type ("python", "3d-step", "pdf", etc.)
  isDirty(): boolean;
  markClean(): void;
  dispose(): void;
}
```

Domain documents can extend this interface for internal state.

### 3.5 ViewerEdit and Events

```ts
interface ViewerEdit {
  label?: string;
  undo(): void | Promise<void>;
  redo(): void | Promise<void>;
}

interface ViewerDocumentChangeEvent {
  document: ViewerDocument;
  edit?: ViewerEdit;         // if provided, participates in undo/redo
}

type Event<T> = (listener: (e: T) => void) => Disposable;

interface Disposable {
  dispose(): void;
}
```

### 3.6 PanelHost

```ts
interface PanelHost {
  readonly id: string;
  title: string;
  readonly container: HTMLElement;   // DOM node for mounting viewer UI

  readonly active: boolean;
  readonly visible: boolean;

  onDidChangeViewState: Event<{ active: boolean; visible: boolean }>;
  onDidDispose: Event<void>;

  postMessage(message: unknown): void;
  onDidReceiveMessage: Event<unknown>;
}
```

`PanelHost` abstracts the center panel instance (a tab or split view). When disposed, any viewer-specific resources must be released.

### 3.7 ViewerProvider

```ts
interface ViewerProvider<TDocument extends ViewerDocument = ViewerDocument> {
  readonly id: string;    // unique viewer type ID

  // Document lifecycle
  openDocument(file: FileDescriptor, context: OpenContext): Promise<TDocument>;
  disposeDocument(doc: TDocument): void;

  // View lifecycle: called once per panel instance
  resolveViewer(
    document: TDocument,
    panel: PanelHost,
    mode: ViewerMode,
    token: CancellationToken
  ): Promise<void>;

  // Persistence
  save(document: TDocument, token: CancellationToken): Promise<void>;
  saveAs(
    document: TDocument,
    destination: FileDescriptor,
    token: CancellationToken
  ): Promise<void>;
  revert(document: TDocument, token: CancellationToken): Promise<void>;
  backup(
    document: TDocument,
    context: BackupContext,
    token: CancellationToken
  ): Promise<BackupHandle>;

  // Change events (dirty + undo/redo)
  readonly onDidChangeDocument: Event<ViewerDocumentChangeEvent>;

  // Capability description
  getCapabilities(file: FileDescriptor, mode: ViewerMode): ViewerCapabilities;
}
```

This mirrors VS Code’s `CustomEditorProvider` and related interfaces.[web:31][web:32]

### 3.8 ViewerSelector and Registration

```ts
interface ViewerSelectorRule {
  extension?: string;           // ".py", ".step", ".pdf"
  mimeType?: string;            // content type match
  pattern?: string;             // glob pattern, e.g. "**/*.step"
  predicate?: (file: FileDescriptor, mode: ViewerMode) => boolean;
}

interface ViewerContribution {
  id: string;                    // ViewerProvider.id
  label: string;                 // displayed in UI
  selector: ViewerSelectorRule[];
  priority: "default" | "option";
  providerFactory: () => ViewerProvider;
}

interface ViewerRegistry {
  register(contribution: ViewerContribution): Disposable;
  getViewersFor(file: FileDescriptor, mode: ViewerMode): ViewerContribution[];
  getDefaultViewer(file: FileDescriptor, mode: ViewerMode): ViewerContribution | undefined;
}
```

The registry is analogous to VS Code’s `customEditors` contribution point and the `registerCustomEditorProvider` call.[web:31][web:32]


## 4. Lifecycle and State Management

### 4.1 Opening a File in the Panel

1. User selects a file; host resolves it to a `FileDescriptor`.
2. Host asks `ViewerRegistry.getViewersFor(file, mode)` and chooses a `ViewerContribution` based on priority or explicit user choice.
3. Host obtains a `ViewerProvider` instance via `providerFactory()`.
4. Host calls `openDocument(file, context)` on the provider.
5. Host creates a `PanelHost` instance for this tab and calls `resolveViewer(document, panel, mode, token)`.
6. Viewer mounts its UI into `panel.container`, registers message handlers, and initializes state.

This mirrors the `openCustomDocument` → `resolveCustomEditor` flow in VS Code.[web:31]

### 4.2 Multiple Views per Document

If `ViewerCapabilities.supportsMultiView` is true, the host may:

- Share the same `ViewerDocument` instance across multiple `PanelHost` instances.
- Call `resolveViewer` once per panel while reference-counting views.
- Call `disposeDocument` only when the last view is closed.

This is equivalent to VS Code’s `supportsMultipleEditorsPerDocument` option.[web:31]

### 4.3 Closing and Disposal

When the user closes a tab:

- Host triggers `panel.onDidDispose`.
- Viewer cleans up DOM/event listeners/3D resources.
- Host checks if this was the last view for the document; if so, calls `disposeDocument` and then `document.dispose()`.

This mirrors `WebviewPanel.dispose` and `CustomDocument.dispose` semantics.[web:31][web:44][web:48]

### 4.4 Dirty State and Undo/Redo

- Viewers emit `onDidChangeDocument` events whenever:
  - An edit that supports undo/redo is applied (with a `ViewerEdit`).
  - Content changes in a way that affects dirtiness (without explicit edit object).
- Host uses these events to:
  - Mark the associated document and tab as dirty.
  - Push edits onto a per-document undo stack.
- Global undo/redo commands delegate into the document’s edit history.

The pattern is modeled on `CustomDocumentEditEvent` and VS Code’s undo/redo integration.[web:31]


## 5. Viewer Implementations for Target Content Types

This section outlines recommended strategies for specific viewer types, emphasizing **adapters around existing tools**.

### 5.1 3D Graphics Viewer (STEP, 3MF, etc.)

**Goal:** Embed a WebGL-based 3D viewer (Three.js, Babylon.js, `<model-viewer>`, or an existing STEP viewer) into a `PanelHost`.[web:15]

Design:

- Implement `ViewerProvider<ThreeDDocument>`.
- `openDocument`:
  - Load model or stream.
  - Create `ThreeDDocument` with model references, optional precomputed metadata.
- `resolveViewer`:
  - Mount a 3D canvas into `panel.container`.
  - Initialize camera, controls, and scene.
  - Wire user interactions to edits if editing is supported (e.g., transformation, annotation).
- `getCapabilities`:
  - `canEdit: false` for pure viewer; `true` if model editing is allowed.
  - `supports3DControls: true`, `prefersIsolation: false` (unless security requires iframes).

Where possible, use an **adapter** around existing 3D viewers (e.g., online STEP viewer widgets) to satisfy the `ViewerProvider` contract while delegating actual rendering.[web:9][web:15]

### 5.2 Python Code Editor

**Goal:** Wrap a code editor (Monaco, CodeMirror) inside the panel.

Design:

- Implement `ViewerProvider<TextDocumentLike>` for `.py` (and potentially other code types).
- Use a **text-based document** type for easy diff, undo, and language tooling.
- `resolveViewer` mounts a code editor instance into `panel.container` and syncs changes with the document model.
- Integrate with a separate language/intellisense subsystem (out of scope for this spec), analogous to how VS Code exposes language features via its extension APIs.[web:32]

### 5.3 PDF Viewer

**Goal:** Use a standard PDF viewer (e.g., PDF.js, browser-native) via an adapter.

Design:

- Implement `ViewerProvider<PdfDocument>` with `canEdit: false`, `prefersIsolation: false | true` depending on security.
- `openDocument` returns a lightweight `PdfDocument` with URI.
- `resolveViewer` either:
  - Mounts a PDF.js viewer component into `panel.container`; or
  - Embeds an `<iframe>` pointing to a hosted PDF viewer route that implements the viewer UI.

Prefer the adapter pattern: your provider just creates the right container and passes the resource URI/config into the existing PDF viewer.

### 5.4 Markdown Viewer/Editor

**Goal:** Provide preview or split view for `.md` files.

Design:

- Implement `ViewerProvider<TextDocumentLike>` or two providers: `MarkdownPreviewViewer` (preview only) and `MarkdownEditorViewer` (edit + preview).
- `getCapabilities` for preview: `canEdit: false`; for editor: `canEdit: true`.
- `resolveViewer` may:
  - Show rendered HTML on one side and editable text on the other; or
  - Show only rendered content in preview mode.

### 5.5 Plain Text Viewer

**Goal:** Generic fallback for unknown text-like files.

Design:

- `ViewerProvider<TextDocumentLike>`; `selector` matches `text/*` MIME types or unknown extensions.
- `getCapabilities`: `canEdit: true`.

### 5.6 IFrame Viewer

**Goal:** Sandbox external content or embedded tools.

Design:

- Implement `ViewerProvider<IframeDocument>` with `prefersIsolation: true` in `getCapabilities`.
- `openDocument` resolves a URL and config.
- `resolveViewer` creates an `<iframe>` inside `panel.container` with:
  - `sandbox` attribute.
  - CSP or URL constraints as needed.
- Messaging can optionally be proxied via `window.postMessage` if the iframe cooperates.

Security: this viewer must treat content as untrusted and run with maximum isolation.


## 6. Adapter Pattern for Existing Tools

To reuse existing viewers/editors (PDF viewer, STEP viewer, code editor widgets), implement **adapters** that map their APIs into `ViewerProvider` and `PanelHost` interactions:

- Map their lifecycle (`init`, `destroy`) to `resolveViewer` and `panel.onDidDispose`.
- Map their change events to `onDidChangeDocument`.
- Map their internal save/export functions to `save` / `saveAs`.
- Wrap any messaging they require into `PanelHost.postMessage` / `onDidReceiveMessage` or local callbacks.

The adapter should be thin; the goal is to keep your core API stable while allowing tool replacement.


## 7. Error Handling, Timeouts, and Killing Misbehaving Panels

### 7.1 Isolation Model

VS Code isolates extensions in a separate **extension host process** so crashes do not take down the UI.[web:52] For the web app:

- Run heavy logic (parsing, large computations, 3D processing) in **Web Workers** or backend services.
- Keep viewer UI code responsive and treat workers/services as failure-isolated components.

### 7.2 Panel-Level Watchdog

- Track heartbeat or responsiveness per panel.
  - Panels send periodic `ping` messages through the messaging channel.
  - If no response within a configurable timeout, mark the panel as unresponsive.
- Provide user options:
  - “Reload panel” – dispose and recreate the viewer.
  - “Close panel” – dispose the panel.

### 7.3 Disposal and Cleanup

- When `PanelHost` is disposed:
  - Immediately stop timers, animation loops (e.g., `requestAnimationFrame`), and event listeners.
  - Release GPU resources (WebGL contexts) and large buffers.
- Enforce maximum memory/resource usage by tracking viewer allocations where possible.

Similar to `WebviewPanel.dispose`, disposal must guarantee the viewer releases resources and cannot continue executing logic in the main UI.[web:44][web:48]


## 8. Testing Strategy

### 8.1 Unit Testing

- Wrap the viewer API and host API behind interfaces to enable mocking, similar to how VS Code extension tests often wrap the `vscode` module.[web:54]
- Unit test `ViewerProvider` implementations in isolation:
  - `openDocument` behavior for various files.
  - `save/revert/backup` logic.
  - `getCapabilities` decisions.

### 8.2 Integration Testing

- Use browser-based integration tests (e.g., Playwright, WebdriverIO) to:
  - Open files of various types.
  - Verify the expected viewer is chosen.
  - Exercise interactions (editing, 3D navigation, scrolling, toolbar actions).

This is analogous to running extension tests in a dedicated VS Code host as described in extension testing guides.[web:49][web:51]

### 8.3 E2E and Regression Testing

- Maintain representative sample projects with diverse file types.
- Automate regression test runs on every change to viewer infrastructure.


## 9. API Documentation

- Document the viewer API in a **developer-facing guide** similar in spirit to VS Code’s extension documentation.[web:43]
- Include:
  - Conceptual overview (Viewer, Document, PanelHost, Registry).
  - Reference for interfaces (`ViewerProvider`, `ViewerDocument`, `PanelHost`).
  - “Hello World” sample viewer implementation.
  - Cookbook for common tasks (3D viewer adapter, PDF adapter, code editor integration).
- Provide versioned docs and changelog to keep implementers informed of API changes.


## 10. Debugging Support for Viewers

- Expose a “Developer Tools” entry point for viewer panels:
  - Allow opening browser DevTools focused on the panel container.
  - For iframes/webviews, provide a route to inspect the inner frame (similar to webview debugging in VS Code).[web:53][web:40]
- Provide diagnostic overlays:
  - Show document URI, viewer type, capabilities, and last error.


## 11. Security and Sandboxing

- For viewers that render untrusted content:
  - Use `IframeViewer` with `sandbox` attributes and strict CSP.
  - Disallow direct DOM injection from untrusted sources.
- Restrict access to sensitive APIs (filesystem, network) to trusted viewers only, via explicit capabilities and server-side enforcement.


## 12. Extensibility and Versioning

- The core viewer API should be **semver-versioned**.
- Provide a feature-flag or capability negotiation mechanism so viewers can adapt to new APIs without breaking.
- Use adapter/wrapper modules to maintain backward compatibility as APIs evolve.


## 13. Summary for Implementation

Implementation teams should:

1. Implement the **ViewerRegistry**, **PanelHost**, and base interfaces (`ViewerProvider`, `ViewerDocument`).
2. Provide a **runtime mechanism** to:
   - Register viewer contributions.
   - Resolve a viewer for a given file and mode.
   - Manage lifecycle, dirty state, save/revert/backup.
3. Build initial viewer adapters for:
   - 3D (STEP, etc.).
   - Python/editor (Monaco/CodeMirror).
   - PDF (PDF.js or equivalent).
   - Markdown and plain text.
   - Iframe-based external content.
4. Implement **watchdog and disposal** logic for misbehaving panels.
5. Set up **testing infrastructure** (unit + integration) around the viewer APIs.
6. Produce **developer documentation** and examples for building new viewers.