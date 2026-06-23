# hermes-wright-panel

Integration package for embedding the Wright web frontend as a panel inside the Hermes Desktop Electron shell. It exposes a custom BrowserView and maps Wright UI service requests (API fetch, local filesystem operations, notifications, terminal processes) to native Electron main-process capabilities via a secure preload bridge.

## Installation

Install the package directly into your Electron project's workspace:

```bash
npm install hermes-wright-panel
# or from local development:
npm install ../wright/hermes-wright-panel
```

## Quickstart

Add the following to your Electron main process file:

```javascript
const { app, BrowserWindow } = require('electron');
const { WrightPanel } = require('hermes-wright-panel');

app.whenReady().then(() => {
  const mainWindow = new BrowserWindow({ width: 1200, height: 800 });
  
  // Initialize the panel
  const wright = new WrightPanel(mainWindow, {
    wrightApiPort: 8000,
    distPath: '/path/to/wright/apps/web/dist-desktop',
    workspacePath: '/path/to/user/workspace'
  });
  
  // Create and add the BrowserView to the main window
  const view = wright.createView();
  mainWindow.setBrowserView(view);
  view.setBounds({ x: 0, y: 0, width: 1200, height: 800 });
});
```

## Configuration Options

The `WrightPanel` constructor takes two arguments: `mainWindow` (BrowserWindow) and `options` (object).

| Option | Type | Default | Description |
|:---|:---|:---|:---|
| `wrightApiPort` | `number` | `8000` | Port of the running Wright FastAPI backend. |
| `distPath` | `string?` | `null` | Path to Wright's `dist-desktop/` directory. If null, loads from `http://localhost:{wrightApiPort}`. |
| `workspacePath` | `string?` | `null` | Absolute path of the workspace root. If set, restricts filesystem reads/writes inside this directory only. |

## Security Features

1. **Workspace Root Restriction**: When `workspacePath` is configured, any read, write, or directory listing request targeting files outside this path rejects with an `EACCES` error code.
2. **API Proxy Isolation**: The HTTP proxy bridge only routes requests to `localhost` on the configured API port to prevent arbitrary network proxying.
3. **Pty Session Limits**: Exposes a max limit of 10 concurrent active terminal sessions.
