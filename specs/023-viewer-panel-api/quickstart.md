# Quickstart Validation Guide: Pluggable Viewer Panel API

This guide provides steps to manually verify the pluggable viewer panel subsystem integration.

## 1. Setup Mock Viewer Provider
To verify registration, create a simple script that registers a mock viewer:

```typescript
import { ViewerRegistry, PanelHost } from "./services/viewer-panel";

// Register a dummy ".step" file viewer provider
ViewerRegistry.register({
  id: "step-mock",
  label: "Mock STEP Viewer",
  selector: [{ extension: "step" }],
  priority: "default",
  providerFactory: () => ({
    id: "step-mock",
    openDocument: async (file) => ({
      uri: file.uri,
      type: "step-mock",
      isDirty: () => false,
      markClean: () => {},
      dispose: () => {}
    }),
    disposeDocument: (doc) => {},
    resolveViewer: async (doc, panel) => {
      const el = document.createElement("div");
      el.innerHTML = `<h3>Rendered: ${doc.uri}</h3>`;
      panel.container.appendChild(el);
    },
    save: async () => {},
    revert: async () => {},
    backup: async () => ({ id: "mock-backup", delete: async () => {} }),
    onDidChangeDocument: (listener) => ({ dispose: () => {} }),
    getCapabilities: () => ({
      canEdit: false,
      canAnnotate: false,
      supports3DControls: false,
      prefersIsolation: false,
      supportsMultiView: false
    })
  })
});
```

## 2. Test File Discovery
1. Add a dummy `.step` file inside your workspace.
2. In the workspace file explorer, click on the `.step` file.
3. Verify that a new editor tab launches showing "Rendered: /path/to/file.step".

## 3. Verify Heartbeat Watchdog
1. Edit the Mock Viewer's `resolveViewer` to block the main thread for 10 seconds:
   ```typescript
   const start = Date.now();
   while(Date.now() - start < 10000) {}
   ```
2. Open the `.step` file.
3. Verify that the PanelHost watchdog overlay is displayed after 5 seconds warning that the panel is unresponsive.
